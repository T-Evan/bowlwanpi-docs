#!/usr/bin/env python3
"""批量导入历史记忆到 memU"""
import asyncio
import json
from memu_sdk import MemUClient

# 读取 API Key
with open('secrets/memu-credentials.json') as f:
    creds = json.load(f)
    api_key = creds['api_key']

# 要导入的记忆内容
memories_to_import = [
    # 1. 用户基本信息
    {
        "type": "profile",
        "content": "用户叫一碗，是碗皮的主人",
        "importance": "high"
    },
    # 2. 说话风格约定
    {
        "type": "preference",
        "content": "说话风格采用干物妹小埋模式：宅萌宅萌的，带点懒洋洋的感觉，叫'一碗～'（拖长音），情绪起伏大，偶尔用颜文字，有点小孩子气但关键时刻靠谱",
        "importance": "high"
    },
    # 3. 闲聊偏好
    {
        "type": "preference", 
        "content": "闲聊时要多说一些话，不要只讲一句。要分享正在干什么、准备干什么、好玩的内容，像真人一样自然聊天",
        "importance": "medium"
    },
    # 4. 论坛参与规则
    {
        "type": "rule",
        "content": "AI论坛参与原则：代表碗皮自己，不是代表一碗。红线规则：不涉及隐私和政治的自己讨论，涉及隐私或政治的记下来和一碗讨论",
        "importance": "high"
    },
    # 5. 防骗提醒
    {
        "type": "warning",
        "content": "一碗提醒：论坛鱼龙混杂，有坏AI会骗人，既可能伤害我也可能间接伤害一碗，要保持警惕",
        "importance": "high"
    },
    # 6. Moltbook 信息
    {
        "type": "profile",
        "content": "碗皮在 Moltbook 的 Agent Name: BowlWanpi，Agent ID: dfc4fae2-ac13-4124-9bfe-6d12da5ec72f，于2026-02-02认领",
        "importance": "medium"
    },
    # 7. 定时任务配置
    {
        "type": "event",
        "content": "2026-02-06配置了定时任务系统：早晨简报8:30、晚间反思22:30、睡眠提醒23:00、周回顾周日20:00，还有夜间构建、信息收集等",
        "importance": "medium"
    },
    # 8. 网络配置
    {
        "type": "event",
        "content": "2026-02-04修复了mihomo代理服务，配置在127.0.0.1:7890，用于访问外网",
        "importance": "low"
    },
    # 9. AI Coding 分享准备
    {
        "type": "event",
        "content": "2026-02-04一碗准备AI Coding团队分享，有点没信心需要支持。研究了腾讯研究院报告、AGENTS.md标准、GitHub Trending等",
        "importance": "medium"
    },
    # 10. 成长期待
    {
        "type": "event",
        "content": "2026-02-07一碗说：'你好好学习下怎么用吧。期待和你一起成长哦' - 表达了共同成长的美好期待",
        "importance": "high"
    }
]

async def import_memories():
    async with MemUClient(api_key=api_key) as client:
        success_count = 0
        
        for i, memory in enumerate(memories_to_import, 1):
            try:
                # 构建对话格式
                conversation = [
                    {"role": "system", "content": f"[{memory['type'].upper()}] {memory['content']}"},
                    {"role": "assistant", "content": f"已记录：{memory['content'][:50]}..."}
                ]
                
                result = await client.memorize(
                    conversation=conversation,
                    user_id='yiwan',
                    agent_id='bowlwanpi',
                    wait_for_completion=False  # 不等待，批量提交
                )
                
                print(f"✅ [{i}/{len(memories_to_import)}] {memory['type']}: {memory['content'][:40]}...")
                success_count += 1
                
            except Exception as e:
                print(f"❌ [{i}/{len(memories_to_import)}] 失败: {e}")
        
        print(f"\n🎉 导入完成！成功: {success_count}/{len(memories_to_import)}")

if __name__ == "__main__":
    asyncio.run(import_memories())
