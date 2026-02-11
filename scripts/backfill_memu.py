#!/usr/bin/env python3
import re
import os
import json
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

sys.path.insert(0, '/root/memU-sdk-py/src')
from memu_sdk import MemUClient

def extract_conversations(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    date_match = re.search(r'# (\d{4}-\d{2}-\d{2})', content)
    date = date_match.group(1) if date_match else 'unknown'
    
    conversations = []
    pattern = r'\*\*\d{2}:\d{2}\*\*.*?\n\n\*\*一碗\*\*: (.*?)\n\n\*\*碗皮\*\*: (.*?)(?=\n\n---|\n\n\*\*\d{2}:\d{2}\*\*|$)'
    
    for match in re.finditer(pattern, content, re.DOTALL):
        user_msg = match.group(1).strip()
        assistant_msg = match.group(2).strip()
        
        if len(user_msg) > 5 and len(assistant_msg) > 5:
            user_msg = re.sub(r'\[.*?\]', '', user_msg)
            user_msg = re.sub(r'System:.*?\n', '', user_msg)
            user_msg = user_msg.strip()
            
            assistant_msg = re.sub(r'\[.*?\]', '', assistant_msg)
            assistant_msg = re.sub(r'System:.*?\n', '', assistant_msg)
            assistant_msg = assistant_msg.strip()
            
            if user_msg and assistant_msg and not user_msg.startswith('Read HEARTBEAT'):
                conversations.append({
                    'date': date,
                    'user': user_msg[:200],
                    'assistant': assistant_msg[:500]
                })
    
    return conversations

async def upload_to_memu(conversations, api_key):
    results = []
    
    async with MemUClient(api_key=api_key) as client:
        for i, conv in enumerate(conversations[:10]):
            try:
                conversation = [
                    {'role': 'user', 'content': conv['user']},
                    {'role': 'assistant', 'content': conv['assistant']}
                ]
                
                result = await client.memorize(
                    conversation=conversation,
                    user_id='yiwan',
                    agent_id='bowlwanpi',
                    wait_for_completion=False
                )
                
                results.append({
                    'date': conv['date'],
                    'task_id': result.task_id,
                    'status': 'success'
                })
                print(f"  ✅ {conv['date']} - Task ID: {result.task_id}")
                
            except Exception as e:
                results.append({
                    'date': conv['date'],
                    'error': str(e),
                    'status': 'failed'
                })
                print(f"  ❌ {conv['date']} - {str(e)[:50]}")
    
    return results

async def main():
    print('📤 开始上传缺失的记忆到 memU...')
    print('=' * 60)
    
    with open('secrets/memu-credentials.json') as f:
        creds = json.load(f)
        api_key = creds['api_key']
    
    memory_files = sorted(Path('memory').glob('2026-02-*.md'))
    print(f'\n找到 {len(memory_files)} 个记忆文件')
    
    all_conversations = []
    
    for file_path in memory_files:
        print(f'\n📄 处理 {file_path.name}...')
        conversations = extract_conversations(file_path)
        print(f'   提取到 {len(conversations)} 条对话')
        all_conversations.extend(conversations)
    
    print(f'\n总共 {len(all_conversations)} 条对话待上传')
    
    to_upload = all_conversations[:30]
    print(f'将上传前 {len(to_upload)} 条重要对话')
    
    print('\n☁️ 开始上传...')
    results = await upload_to_memu(to_upload, api_key)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    print(f'\n{"=" * 60}')
    print(f'✅ 上传完成: {success_count}/{len(results)} 条成功')
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    result_file = f'memory/memu-backfill-{timestamp}.json'
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'📊 详细结果已保存到: {result_file}')

if __name__ == '__main__':
    asyncio.run(main())
