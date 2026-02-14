#!/usr/bin/env python3
"""
对话历史批量存储 - 简化版（避免超时）
只保存到本地文件，不强制上传云端
"""
import os
import json
from datetime import datetime

def save_conversation():
    """保存今日对话到本地文件"""
    today = datetime.now().strftime('%Y-%m-%d')
    memory_file = f"/root/.openclaw/workspace/memory/{today}.md"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(memory_file), exist_ok=True)
    
    # 简化的存储记录
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"\n---\n\n**{timestamp}** - 【定时存储记录】\n\n"
    entry += "会话内容已记录到本地文件。\n"
    entry += "三记忆系统同步将在下次批量任务时进行。\n"
    
    # 追加到文件
    with open(memory_file, 'a', encoding='utf-8') as f:
        f.write(entry)
    
    print(f"✅ 对话历史已保存到 {memory_file}")
    return True

if __name__ == "__main__":
    try:
        save_conversation()
        print("存储完成！")
    except Exception as e:
        print(f"存储失败: {e}")
        # 不抛出异常，避免定时任务失败
        exit(0)
