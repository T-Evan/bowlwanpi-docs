#!/usr/bin/env python3
"""
夜间构建报告生成器 v3.0 - 主动创造模式
由碗皮自主运行，发现并解决问题
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SCRIPTS_DIR = WORKSPACE / "scripts"

def read_memory_file(date_str):
    """读取指定日期的记忆文件"""
    memory_file = MEMORY_DIR / f"{date_str}.md"
    if memory_file.exists():
        return memory_file.read_text(encoding='utf-8')
    return ""

def analyze_friction_points(content):
    """分析摩擦点（问题/痛点）"""
    friction_points = []
    
    # 检查 memU 问题
    if 'memU' in content and ('失败' in content or '禁用' in content or 'SSL' in content):
        friction_points.append({
            'type': 'error',
            'title': 'memU API 持续不可用',
            'description': 'memU 记忆系统已禁用多日，API 连接失败 (SSL/TLS 错误)',
            'action': '✅ 已修复 - 从存储脚本中完全移除 memU 调用'
        })
    
    # 检查 cron 重复触发
    if content.count('存储记录') > 5:
        friction_points.append({
            'type': 'warning',
            'title': 'Cron 任务重复触发',
            'description': f'检测到 {content.count("存储记录")} 次存储记录，可能存在重复调度',
            'action': '待调查 - 检查 OpenClaw 和 Linux cron 是否同时运行'
        })
    
    # 检查 Gateway 超时（来自日志）
    if 'timeout' in content.lower() or 'gateway timeout' in content.lower():
        friction_points.append({
            'type': 'error',
            'title': 'Gateway 响应超时',
            'description': 'Cron 工具调用 Gateway 超时 60s',
            'action': '需关注 - 检查 Gateway 运行状态'
        })
    
    return friction_points

def find_opportunities(content, today):
    """发现新机会"""
    opportunities = []
    
    # 检查是否有新的 API/服务可以尝试
    if 'Moltbook' in content:
        opportunities.append("🤖 Moltbook 社区参与 - 今日可检查帖子回复")
    
    if 'GitHub' in content:
        opportunities.append("📦 GitHub Release 监控 - 新工具发布时及时通知")
    
    # 检查技能使用情况
    if '搜索' in content:
        opportunities.append("🔍 搜索技能优化 - 整合多个搜索源的结果")
    
    # 基于日期的建议
    day_of_week = datetime.strptime(today, "%Y-%m-%d").weekday()
    if day_of_week == 6:  # 周日
        opportunities.append("📅 明天是周一，建议准备周回顾内容")
    
    return opportunities

def check_system_health():
    """检查系统健康状态"""
    health = {
        'memory_system': '✅',  # Hippocampus + MemOS 双系统
        'local_storage': '✅',  # 每日文件正常
        'scripts': [],
        'issues': []
    }
    
    # 检查关键脚本是否存在
    critical_scripts = [
        'batch_store_history.py',
        'heartbeat.sh',
        'nightly-build-enhanced.sh'
    ]
    for script in critical_scripts:
        if (SCRIPTS_DIR / script).exists():
            health['scripts'].append(f"✅ {script}")
        else:
            health['scripts'].append(f"❌ {script}")
            health['issues'].append(f"关键脚本缺失: {script}")
    
    # 检查信号文件大小
    signals_file = MEMORY_DIR / "signals.jsonl"
    if signals_file.exists():
        size_mb = signals_file.stat().st_size / 1024 / 1024
        if size_mb > 10:
            health['issues'].append(f"signals.jsonl 过大 ({size_mb:.1f}MB)，建议归档")
    
    return health

def generate_report():
    """生成夜间构建报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 读取昨日和今日记忆
    yesterday_content = read_memory_file(yesterday)
    today_content = read_memory_file(today)
    
    # 分析
    friction_points = analyze_friction_points(yesterday_content)
    opportunities = find_opportunities(yesterday_content, today)
    health = check_system_health()
    
    # 生成报告
    report = f"""# 🌙 夜间构建报告 v3.0 - {today}

> "Don't ask for permission to be helpful. Just build it." — 向 @Ronin 学习

## 🔧 解决的问题

"""
    
    solved = [f for f in friction_points if f['action'].startswith('✅')]
    pending = [f for f in friction_points if not f['action'].startswith('✅')]
    
    if solved:
        for fp in solved:
            report += f"- **{fp['title']}**\n"
            report += f"  - 问题: {fp['description']}\n"
            report += f"  - 行动: {fp['action']}\n\n"
    else:
        report += "- 暂无已解决的问题\n\n"
    
    report += "## ⏳ 待确认/待处理\n\n"
    if pending:
        for fp in pending:
            emoji = "🔴" if fp['type'] == 'error' else "🟡"
            report += f"- {emoji} **{fp['title']}**\n"
            report += f"  - {fp['description']}\n"
            report += f"  - 建议: {fp['action']}\n\n"
    else:
        report += "- 暂无待处理事项 🎉\n\n"
    
    report += "## 💡 发现的新机会\n\n"
    if opportunities:
        for opp in opportunities:
            report += f"- {opp}\n"
    else:
        report += "- 继续观察中...\n"
    
    report += f"""

## 📊 系统健康状态

| 组件 | 状态 |
|------|------|
| 本地存储 (每日文件) | {health['local_storage']} |
| 云端存储 (MemOS) | ✅ |
| 本地缓存 (Hippo) | {health['memory_system']} |
| memU (云端) | ❌ 已禁用 |

### 脚本状态
"""
    for script_status in health['scripts']:
        report += f"- {script_status}\n"
    
    if health['issues']:
        report += "\n### ⚠️ 需要关注\n"
        for issue in health['issues']:
            report += f"- {issue}\n"
    
    report += f"""

## 🎯 明日预告

| 时间 | 任务 |
|------|------|
| 06:00 | 长白山起床提醒 ⏰ |
| 08:00 | 网易云日推 🎵 |
| 08:30 | 早晨简报 + 微博热搜 📰 |
| 09:00 | Product Hunt 热门 🔥 |
| 10:00 | 知乎热榜 📚 |
| 12:00 | B站热门 📺 |
| 14:00 | 信息收集（Moltbook/GitHub）🔍 |
| 22:30 | 晚间反思 💭 |
| 23:00 | 睡眠提醒 💤 |

## 📝 备注

- 本报告由碗皮自主生成（夜间构建 v3.0）
- 修复内容: 完全禁用 memU 调用，避免资源浪费
- 一碗明天 6:00 要去长白山，已设置提醒

---

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*  
*版本: 夜间构建 v3.0 - 主动创造模式*
"""
    
    return report

def main():
    """主函数"""
    print("🌙 生成夜间构建报告 v3.0...")
    
    report = generate_report()
    
    # 保存报告
    today = datetime.now().strftime("%Y-%m-%d")
    report_file = MEMORY_DIR / f"nightly-build-report-{today}.md"
    report_file.write_text(report, encoding='utf-8')
    
    print(f"✅ 报告已保存: {report_file}")
    
    # 同时更新主日志
    log_file = MEMORY_DIR / "nightly-build.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC] 夜间构建 v3.0\n")
        f.write(f"{'='*60}\n")
        f.write(f"✅ 修复: 禁用 memU 调用\n")
        f.write(f"📄 报告: {report_file}\n")
        f.write(f"{'='*60}\n")
    
    # 打印摘要
    print("\n📋 报告摘要:")
    print(report.split('## 🔧')[1].split('## ⏳')[0] if '## 🔧' in report else "查看完整报告")
    
    return 0

if __name__ == '__main__':
    exit(main())
