#!/usr/bin/env python3
"""
Website Publisher - 部署脚本
部署网站到 GitHub Pages
"""

import subprocess
import os
import argparse
from datetime import datetime

def run_cmd(cmd, cwd=None):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  命令失败: {cmd}")
        print(f"   错误: {result.stderr}")
    return result.returncode == 0

def deploy(message=None, skip_update=False, dry_run=False):
    """部署网站"""
    docs_dir = os.environ.get('WEBSITE_DOCS', '/root/.openclaw/workspace/docs')

    if not skip_update:
        print("📝 更新数据...")
        if not dry_run:
            update_script = os.path.join(docs_dir, 'skills', 'website-publisher', 'scripts', 'update.py')
            run_cmd(f'python3 {update_script}')
        else:
            print("[DRY RUN] 跳过数据更新")

    # 生成提交信息
    if message is None:
        message = f"Update website data - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    print(f"\n🚀 部署到 GitHub Pages...")
    print(f"   提交信息: {message}")

    if dry_run:
        print("[DRY RUN] 模拟提交和推送")
        print("   git add -A")
        print(f"   git commit -m '{message}'")
        print("   git push origin gh-pages")
        return

    # Git 操作
    run_cmd('git add -A', cwd=docs_dir)

    # 检查是否有变更
    status_result = subprocess.run('git status --porcelain', shell=True, cwd=docs_dir, capture_output=True, text=True)
    if not status_result.stdout.strip():
        print("✅ 没有变更需要提交")
        return

    # 提交
    run_cmd(f'git commit -m "{message}"', cwd=docs_dir)

    # 推送
    if run_cmd('git push origin gh-pages', cwd=docs_dir):
        print("\n✅ 部署成功!")
        print("   🌐 https://yiwan-zhou.github.io/bowlwanpi-docs/")
    else:
        print("\n❌ 部署失败")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='部署网站到 GitHub Pages')
    parser.add_argument('--skip-update', action='store_true', help='跳过数据更新')
    parser.add_argument('--message', '-m', help='自定义提交信息')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行')
    args = parser.parse_args()

    deploy(message=args.message, skip_update=args.skip_update, dry_run=args.dry_run)
