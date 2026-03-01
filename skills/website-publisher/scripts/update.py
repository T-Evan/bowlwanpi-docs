#!/usr/bin/env python3
"""
Website Publisher - 数据更新脚本
生成博客所需的动态数据文件
"""

import json
import subprocess
import os
from datetime import datetime

def get_docker_containers():
    """获取 Docker 容器信息"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{json .}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                c = json.loads(line)
                # 解析端口 - 只取第一个端口映射
                ports_full = c.get('Ports', '')
                # 提取第一个端口 (格式: 0.0.0.0:5700->5700/tcp, [::]:5700->5700/tcp)
                port_match = None
                if '->' in ports_full:
                    # 取第一个映射，去掉 IPv6 部分
                    first_mapping = ports_full.split(',')[0].strip()
                    # 提取端口号 (格式: 0.0.0.0:5700->5700/tcp)
                    parts = first_mapping.split('->')
                    if len(parts) >= 2:
                        host_part = parts[0]  # 0.0.0.0:5700
                        port_match = host_part.split(':')[-1]  # 5700

                # 构建描述
                descriptions = {
                    'qinglong': '青龙面板 - 自动化任务管理平台',
                    'sillytavern': 'SillyTavern - AI 角色扮演前端'
                }
                name = c.get('Names', '')

                # 格式化创建时间
                created_raw = c.get('CreatedAt', '')
                created_formatted = created_raw
                try:
                    # 尝试解析并重新格式化时间
                    from datetime import datetime
                    # Docker 格式: 2026-03-02 01:08:26 +0800 CST
                    dt = datetime.strptime(created_raw[:19], '%Y-%m-%d %H:%M:%S')
                    created_formatted = dt.strftime('%Y-%m-%dT%H:%M:%S+08:00')
                except:
                    pass

                container_info = {
                    'name': name,
                    'image': c.get('Image', ''),
                    'status': c.get('State', 'unknown'),
                    'health': 'healthy' if 'healthy' in c.get('Status', '').lower() else 'unknown',
                    'ports': f"0.0.0.0:{port_match}->{port_match}/tcp" if port_match else ports_full,
                    'created': created_formatted,
                    'description': descriptions.get(name, 'Docker 容器服务'),
                    'url': f"http://localhost:{port_match}" if port_match else ''
                }
                containers.append(container_info)
        return containers
    except Exception as e:
        print(f"获取 Docker 容器失败: {e}")
        return []

def update_docker_containers():
    """更新 Docker 容器数据文件"""
    docs_dir = os.environ.get('WEBSITE_DOCS', '/root/.openclaw/workspace/docs')
    data_file = os.path.join(docs_dir, 'data', 'docker-containers.json')

    containers = get_docker_containers()
    data = {
        'containers': containers,
        'count': len(containers),
        'updated': datetime.now().isoformat()
    }

    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Docker 容器数据已更新: {len(containers)} 个容器")
    return data

def update_stats():
    """更新统计文件，添加 docker_containers 计数"""
    docs_dir = os.environ.get('WEBSITE_DOCS', '/root/.openclaw/workspace/docs')
    stats_file = os.path.join(docs_dir, 'data', 'stats.json')

    # 先更新容器数据
    docker_data = update_docker_containers()

    # 读取现有 stats
    stats = {}
    if os.path.exists(stats_file):
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)

    # 更新 docker_containers 计数
    stats['docker_containers'] = docker_data['count']
    stats['updated'] = datetime.now().isoformat()

    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"✅ 统计数据已更新")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='更新网站数据')
    parser.add_argument('--only', choices=['docker', 'stats', 'all'], default='all',
                        help='仅更新特定数据')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行')
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN] 模拟运行模式")

    if args.only in ['docker', 'all']:
        update_docker_containers()

    if args.only in ['stats', 'all']:
        update_stats()

    print("\n🎉 数据更新完成!")
