#!/usr/bin/env python3
"""
每日创意简报生成器
结合记忆、趋势、挑战、内容创作
"""

import json
import random
from datetime import datetime
from pathlib import Path

# 路径配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SKILL_DIR = WORKSPACE / "skills/daily-creative-brief"

# 创意挑战库
CHALLENGES = [
    {
        "type": "skill-dev",
        "title": "开发一个微型工具",
        "desc": "用30分钟开发一个解决小问题的脚本",
        "examples": ["文件批量重命名", "JSON格式化工具", "简易待办清单"]
    },
    {
        "type": "content-creation", 
        "title": "写一篇技术微分享",
        "desc": "用200字分享今天学到的一个技巧",
        "examples": ["Git技巧", "Python一行代码", "效率工具推荐"]
    },
    {
        "type": "automation",
        "title": "自动化一个重复任务",
        "desc": "找出今天重复做了3次以上的事，写成脚本",
        "examples": ["日志整理", "数据备份", "文件分类"]
    },
    {
        "type": "exploration",
        "title": "探索一个新工具",
        "desc": "尝试一个没用过的新工具或库",
        "examples": ["新的CLI工具", "Python新库", "MCP技能"]
    },
    {
        "type": "optimization",
        "title": "优化现有工作流",
        "desc": "让现有某个流程快一倍",
        "examples": ["减少查询步骤", "并行执行任务", "缓存优化"]
    },
    {
        "type": "creative-writing",
        "title": "用故事讲技术",
        "desc": "把技术概念变成有趣的故事或比喻",
        "examples": ["把API比喻成餐厅", "用小说讲算法", "技术寓言"]
    }
]

# 灵感触发词
TRIGGERS = [
    "自动化", "可视化", "AI", "数据", "工作流",
    "记忆", "情感", "创造", "效率", "安全",
    "协作", "学习", "优化", "分析", "生成"
]


def load_recent_memories(days=3):
    """加载最近几天的记忆"""
    memories = []
    for i in range(days):
        date = datetime.now()
        date_str = date.strftime('%Y-%m-%d')
        memory_file = MEMORY_DIR / f"{date_str}.md"
        
        if memory_file.exists():
            try:
                with open(memory_file, 'r') as f:
                    content = f.read()
                    # 提取关键行
                    lines = content.split('\n')
                    for line in lines:
                        if any(t in line for t in TRIGGERS) and len(line) > 10:
                            memories.append(line.strip()[:100])
            except:
                pass
    
    return memories[:10]  # 返回前10条


def analyze_trends():
    """简单趋势分析（基于已有数据）"""
    trends = []
    
    # 检查最近 GitHub 监控
    github_cache = MEMORY_DIR / "github-release-cache.json"
    if github_cache.exists():
        trends.append("🔧 工具更新活跃 - 值得关注新特性")
    
    # 检查知识库
    pkm_dir = WORKSPACE / "pkm"
    if pkm_dir.exists():
        md_count = len(list(pkm_dir.glob("**/*.md")))
        if md_count > 0:
            trends.append(f"📚 知识库增长中 - 已收集 {md_count} 条笔记")
    
    # 检查技能数量
    skills_dir = WORKSPACE / "skills"
    if skills_dir.exists():
        skill_count = len([d for d in skills_dir.iterdir() if d.is_dir()])
        trends.append(f"🛠️ 技能生态扩展 - 当前 {skill_count} 个技能")
    
    return trends


def generate_challenge():
    """生成今日挑战"""
    challenge = random.choice(CHALLENGES)
    example = random.choice(challenge['examples'])
    
    return {
        "type": challenge['type'],
        "title": challenge['title'],
        "description": challenge['desc'],
        "example": example,
        "difficulty": random.choice(["简单", "中等", "进阶"]),
        "estimated_time": random.choice(["15分钟", "30分钟", "1小时"])
    }


def generate_micro_content(memories, challenge):
    """生成微内容（可分享到Moltbook/社交媒体）"""
    templates = [
        "今日创造挑战：{challenge}\n💡 灵感来自：{memory}\n#AI创造 #每日挑战",
        "🚀 今天想试试：{challenge}\n从 {memory} 找到了灵感\n#创意实践",
        "💪 创造模式ON！\n任务：{challenge}\n触发点：{memory}\n#AI助手成长记"
    ]
    
    template = random.choice(templates)
    memory = random.choice(memories) if memories else "日常观察"
    
    # 简化记忆引用
    memory_short = memory[:30] + "..." if len(memory) > 30 else memory
    
    return template.format(
        challenge=challenge['title'],
        memory=memory_short
    )


def generate_brief():
    """生成完整简报"""
    print("🎨 正在生成每日创意简报...\n")
    
    # 1. 收集记忆线索
    memories = load_recent_memories()
    print(f"🧠 从最近记忆中提取了 {len(memories)} 条灵感线索")
    
    # 2. 分析趋势
    trends = analyze_trends()
    print(f"📊 发现 {len(trends)} 个值得关注趋势")
    
    # 3. 生成挑战
    challenge = generate_challenge()
    print(f"🎯 生成今日创造挑战")
    
    # 4. 创作微内容
    micro_content = generate_micro_content(memories, challenge)
    print(f"✍️ 创作完成微内容\n")
    
    # 组装简报
    brief = {
        "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "inspiration_source": {
            "memory_clues": memories[:3],
            "trends": trends
        },
        "challenge": challenge,
        "micro_content": micro_content,
        "motivation_boost": random.choice([
            "创造是最好的学习方式！",
            "每个小项目都是成长的机会！",
 "完成比完美更重要！",
            "今天的一个尝试，明天的核心能力！"
        ])
    }
    
    return brief


def print_brief(brief):
    """打印简报"""
    print("=" * 50)
    print(f"🎨 每日创意简报 | {brief['date']}")
    print("=" * 50)
    
    print("\n🧠 灵感来源")
    print("-" * 30)
    if brief['inspiration_source']['memory_clues']:
        print("最近记忆中的关键词：")
        for clue in brief['inspiration_source']['memory_clues']:
            print(f"  • {clue}")
    
    if brief['inspiration_source']['trends']:
        print("\n观察到的趋势：")
        for trend in brief['inspiration_source']['trends']:
            print(f"  • {trend}")
    
    print("\n🎯 今日创造挑战")
    print("-" * 30)
    print(f"类型：{brief['challenge']['type']}")
    print(f"标题：{brief['challenge']['title']}")
    print(f"难度：{brief['challenge']['difficulty']}")
    print(f"预计时间：{brief['challenge']['estimated_time']}")
    print(f"\n描述：{brief['challenge']['description']}")
    print(f"示例：{brief['challenge']['example']}")
    
    print("\n✍️ 可分享内容")
    print("-" * 30)
    print(brief['micro_content'])
    
    print("\n💪 动力加持")
    print("-" * 30)
    print(brief['motivation_boost'])
    
    print("\n" + "=" * 50)
    print("准备好开始创造了吗？加油！🚀")
    print("=" * 50)


def save_brief(brief):
    """保存简报到知识库"""
    pkm_dir = WORKSPACE / "pkm/ideas"
    pkm_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime('%Y%m%d')
    filename = pkm_dir / f"创意简报-{date_str}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 简报已保存到: {filename}")


if __name__ == "__main__":
    # 生成简报
    brief = generate_brief()
    
    # 打印
    print_brief(brief)
    
    # 保存
    save_brief(brief)
