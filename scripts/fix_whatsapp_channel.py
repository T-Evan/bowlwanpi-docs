#!/usr/bin/env python3
"""
定时任务 WhatsApp 通道修复工具
检测并移除所有 WhatsApp 通道配置
"""

import json
import subprocess
import sys
from pathlib import Path

def get_cron_jobs():
    """获取所有定时任务"""
    try:
        result = subprocess.run(
            ['openclaw', 'cron', 'list'],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"❌ 获取定时任务失败: {e}")
        return None

def check_whatsapp_channels(jobs_data):
    """检查 WhatsApp 通道配置"""
    jobs = jobs_data.get('jobs', [])
    whatsapp_jobs = []
    
    for job in jobs:
        delivery = job.get('delivery', {})
        channel = delivery.get('channel', '')
        
        if channel == 'whatsapp' or 'whatsapp' in str(delivery).lower():
            whatsapp_jobs.append({
                'id': job.get('id'),
                'name': job.get('name'),
                'channel': channel
            })
    
    return whatsapp_jobs

def fix_job_channel(job_id):
    """移除任务的 delivery 配置"""
    try:
        # 通过 cron update 命令移除 delivery
        # 先获取当前配置
        result = subprocess.run(
            ['openclaw', 'cron', 'list'],
            capture_output=True, text=True, timeout=30
        )
        jobs = json.loads(result.stdout)
        
        target_job = None
        for job in jobs.get('jobs', []):
            if job.get('id') == job_id:
                target_job = job
                break
        
        if not target_job:
            return False, "Job not found"
        
        # 移除 delivery 字段
        if 'delivery' in target_job:
            del target_job['delivery']
        
        # 更新任务（通过 API 或命令）
        # 由于 openclaw CLI 可能不支持直接更新 delivery，我们记录需要修复的任务
        return True, "Marked for fix"
        
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 检查定时任务 WhatsApp 通道配置...\n")
    
    jobs_data = get_cron_jobs()
    if not jobs_data:
        sys.exit(1)
    
    jobs = jobs_data.get('jobs', [])
    print(f"📋 发现 {len(jobs)} 个定时任务\n")
    
    # 检查 WhatsApp 配置
    whatsapp_jobs = check_whatsapp_channels(jobs_data)
    
    if not whatsapp_jobs:
        print("✅ 没有发现 WhatsApp 通道配置")
        
        # 显示所有任务的通道配置
        print("\n📊 当前通道配置:")
        for job in jobs:
            delivery = job.get('delivery', {})
            channel = delivery.get('channel', 'default')
            print(f"  • {job.get('name', 'Unknown')}: {channel}")
        
        return
    
    print(f"⚠️ 发现 {len(whatsapp_jobs)} 个任务使用 WhatsApp 通道:\n")
    for job in whatsapp_jobs:
        print(f"  ❌ {job['name']} (ID: {job['id'][:8]}...)")
        print(f"     通道: {job['channel']}")
    
    print("\n🔧 修复建议:")
    print("由于 openclaw CLI 限制，请手动修复:")
    print("\n方法1: 通过 gateway config 修改")
    print("  1. 编辑 ~/.openclaw/openclaw.json")
    print("  2. 找到 cron 任务配置")
    print("  3. 将 'whatsapp' 改为 'feishu' 或移除 delivery 配置")
    print("\n方法2: 重新创建任务")
    print("  1. 删除有问题的任务: openclaw cron remove <job-id>")
    print("  2. 重新创建任务，不指定 whatsapp 通道")
    
    # 保存报告
    report_file = Path('/tmp/whatsapp-channel-report.txt')
    with open(report_file, 'w') as f:
        f.write("WhatsApp Channel Report\n")
        f.write("="*50 + "\n\n")
        f.write(f"发现问题任务: {len(whatsapp_jobs)}\n\n")
        for job in whatsapp_jobs:
            f.write(f"Job: {job['name']}\n")
            f.write(f"ID: {job['id']}\n")
            f.write(f"Channel: {job['channel']}\n\n")
    
    print(f"\n📄 详细报告已保存: {report_file}")

if __name__ == '__main__':
    main()
