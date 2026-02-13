#!/usr/bin/env python3
"""
碗皮创意工坊 🎨 - 游戏化任务管理系统
把创造变成一场冒险！

特性：
- 🎲 随机任务生成器
- 🎮 游戏化进度系统
- 🏆 成就徽章
- 📊 可视化统计
- 🎵 心情音乐推荐
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CreativeQuest:
    """创意任务"""
    id: str
    title: str
    description: str
    type: str
    difficulty: str
    estimated_time: int  # 分钟
    xp_reward: int
    tags: List[str]
    prompt_template: str


@dataclass
class PlayerStats:
    """玩家状态"""
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    streak_days: int = 0
    total_quests: int = 0
    current_mood: str = "专注"
    title: str = "创意学徒"


class CreativeWorkshop:
    """创意工坊主类"""
    
    # 任务类型
    QUEST_TYPES = {
        "skill": {"icon": "🛠️", "name": "技能开发", "color": "🔵"},
        "content": {"icon": "✍️", "name": "内容创作", "color": "🟢"},
        "auto": {"icon": "⚙️", "name": "自动化", "color": "🟡"},
        "explore": {"icon": "🔍", "name": "探索发现", "color": "🟣"},
        "optimize": {"icon": "🚀", "name": "性能优化", "color": "🔴"},
        "creative": {"icon": "🎨", "name": "创意设计", "color": "🟠"}
    }
    
    # 难度等级
    DIFFICULTY_LEVELS = {
        "简单": {"time": 15, "xp": 20, "multiplier": 1.0},
        "中等": {"time": 60, "xp": 50, "multiplier": 1.5},
        "困难": {"time": 120, "xp": 100, "multiplier": 2.0},
        "史诗": {"time": 240, "xp": 250, "multiplier": 3.0}
    }
    
    # 等级头衔
    TITLES = [
        (1, "创意学徒", 100),
        (2, "初级创造者", 250),
        (3, "中级创造者", 500),
        (4, "高级创造者", 1000),
        (5, "创意大师", 2000),
        (6, "传奇创造者", 4000),
        (7, "创意之神", 8000)
    ]
    
    def __init__(self):
        self.data_dir = Path.home() / ".openclaw/workspace/pkm/workshop"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats_file = self.data_dir / "player_stats.json"
        self.quests_file = self.data_dir / "completed_quests.json"
        
        self.stats = self._load_stats()
        self.completed_quests = self._load_completed()
        
    def _load_stats(self) -> PlayerStats:
        """加载玩家状态"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
                return PlayerStats(**data)
        return PlayerStats()
    
    def _load_completed(self) -> List[Dict]:
        """加载已完成任务"""
        if self.quests_file.exists():
            with open(self.quests_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save(self):
        """保存数据"""
        with open(self.stats_file, 'w') as f:
            json.dump(asdict(self.stats), f, indent=2)
        with open(self.quests_file, 'w') as f:
            json.dump(self.completed_quests, f, indent=2)
    
    def generate_daily_quests(self, count: int = 3) -> List[CreativeQuest]:
        """生成每日任务"""
        quests = []
        
        # 根据玩家等级调整难度概率
        difficulty_weights = self._get_difficulty_weights()
        
        quest_templates = [
            {
                "title": "写一个有趣的脚本",
                "desc": "创建一个解决日常问题的Python脚本",
                "type": "skill",
                "prompt": "写一个实用的Python脚本，解决'{context}'的问题"
            },
            {
                "title": "技术微分享",
                "desc": "用200字分享一个技巧",
                "type": "content",
                "prompt": "分享关于'{context}'的实用技巧"
            },
            {
                "title": "自动化任务",
                "desc": "自动化一个重复的手动操作",
                "type": "auto",
                "prompt": "创建一个自动化脚本，处理'{context}'"
            },
            {
                "title": "探索新工具",
                "desc": "尝试一个从未用过的新工具",
                "type": "explore",
                "prompt": "探索并试用'{context}'，记录体验"
            },
            {
                "title": "代码重构",
                "desc": "优化现有代码，提升性能或可读性",
                "type": "optimize",
                "prompt": "重构'{context}'的代码，添加类型注解和文档"
            },
            {
                "title": "创意写作",
                "desc": "用故事的方式解释一个技术概念",
                "type": "creative",
                "prompt": "用故事的形式解释'{context}'"
            },
            {
                "title": "制作教程",
                "desc": "创建一个 step-by-step 教程",
                "type": "content",
                "prompt": "创建一个关于'{context}'的详细教程"
            },
            {
                "title": "设计新功能",
                "desc": "为一个现有工具设计新功能",
                "type": "creative",
                "prompt": "为'{context}'设计一个新功能，画出流程图"
            },
            {
                "title": "数据分析",
                "desc": "分析某个数据集并发现洞察",
                "type": "explore",
                "prompt": "分析'{context}'的数据，找出有趣的模式"
            },
            {
                "title": "构建API",
                "desc": "为一个功能设计并实现API接口",
                "type": "skill",
                "prompt": "为'{context}'设计并实现一个简单的API"
            }
        ]
        
        contexts = [
            "文件管理", "数据分析", "日志处理", "代码质量",
            "工作效率", "知识管理", "自动化测试", "性能监控",
            "错误处理", "文档生成", "通知系统", "数据备份"
        ]
        
        selected = random.sample(quest_templates, min(count, len(quest_templates)))
        
        for i, template in enumerate(selected, 1):
            difficulty = random.choices(
                list(self.DIFFICULTY_LEVELS.keys()),
                weights=difficulty_weights
            )[0]
            
            diff_data = self.DIFFICULTY_LEVELS[difficulty]
            context = random.choice(contexts)
            
            quest = CreativeQuest(
                id=f"quest_{datetime.now().strftime('%Y%m%d')}_{i}",
                title=template["title"],
                description=template["desc"],
                type=template["type"],
                difficulty=difficulty,
                estimated_time=diff_data["time"],
                xp_reward=int(diff_data["xp"] * diff_data["multiplier"]),
                tags=[template["type"], difficulty],
                prompt_template=template["prompt"].format(context=context)
            )
            quests.append(quest)
        
        return quests
    
    def _get_difficulty_weights(self) -> List[int]:
        """根据等级获取难度权重"""
        if self.stats.level <= 2:
            return [60, 30, 10, 0]  # 简单为主
        elif self.stats.level <= 4:
            return [30, 50, 20, 0]  # 中等为主
        elif self.stats.level <= 6:
            return [10, 40, 40, 10]  # 困难为主
        else:
            return [5, 25, 50, 20]  # 史诗也有
    
    def complete_quest(self, quest: CreativeQuest, notes: str = ""):
        """完成任务"""
        # 计算奖励
        xp_gain = quest.xp_reward
        streak_bonus = min(self.stats.streak_days * 5, 50)  # 连胜加成
        total_xp = xp_gain + streak_bonus
        
        # 更新状态
        self.stats.xp += total_xp
        self.stats.total_quests += 1
        
        # 检查升级
        while self.stats.xp >= self.stats.xp_to_next:
            self._level_up()
        
        # 记录任务
        self.completed_quests.append({
            "quest": asdict(quest),
            "completed_at": datetime.now().isoformat(),
            "xp_gained": total_xp,
            "notes": notes
        })
        
        self._save()
        
        return {
            "xp_gained": total_xp,
            "streak_bonus": streak_bonus,
            "leveled_up": self.stats.xp >= self.stats.xp_to_next,
            "current_xp": self.stats.xp,
            "xp_to_next": self.stats.xp_to_next
        }
    
    def _level_up(self):
        """升级"""
        self.stats.xp -= self.stats.xp_to_next
        self.stats.level += 1
        
        # 更新头衔
        for level, title, xp_needed in self.TITLES:
            if self.stats.level == level:
                self.stats.title = title
                self.stats.xp_to_next = xp_needed
                break
    
    def display_status(self):
        """显示状态"""
        print("\n" + "=" * 60)
        print("🎨 碗皮创意工坊")
        print("=" * 60)
        
        # 玩家信息
        print(f"\n👤 {self.stats.title} Lv.{self.stats.level}")
        print(f"   XP: {self.stats.xp}/{self.stats.xp_to_next}")
        
        # 经验条
        progress = self.stats.xp / self.stats.xp_to_next
        bar_length = 30
        filled = int(progress * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"   [{bar}] {progress*100:.1f}%")
        
        print(f"\n📊 统计")
        print(f"   完成任务: {self.stats.total_quests}")
        print(f"   连胜天数: {self.stats.streak_days} 🔥")
        print(f"   当前心情: {self.stats.current_mood}")
    
    def display_daily_quests(self):
        """显示每日任务"""
        quests = self.generate_daily_quests()
        
        print("\n🎯 今日创意任务")
        print("-" * 60)
        
        for i, quest in enumerate(quests, 1):
            type_info = self.QUEST_TYPES[quest.type]
            print(f"\n{i}. {type_info['icon']} {quest.title}")
            print(f"   {quest.description}")
            print(f"   难度: {quest.difficulty} | 时间: {quest.estimated_time}分钟 | XP: {quest.xp_reward}")
            print(f"   💡 {quest.prompt_template}")
        
        return quests
    
    def get_mood_music(self) -> str:
        """根据心情推荐音乐"""
        moods = {
            "专注": ["Lo-fi Hip Hop", "Ambient", "Classical Piano"],
            "兴奋": ["Electronic", "Upbeat Pop", "Rock"],
            "放松": ["Jazz", "Acoustic", "Nature Sounds"],
            "困倦": ["Energetic EDM", "Fast Pop", "Metal"]
        }
        
        current_mood = self.stats.current_mood
        if current_mood in moods:
            return random.choice(moods[current_mood])
        return "Lo-fi Hip Hop"


def main():
    import sys
    
    workshop = CreativeWorkshop()
    
    if len(sys.argv) < 2:
        workshop.display_status()
        workshop.display_daily_quests()
        return
    
    command = sys.argv[1]
    
    if command == "quests":
        quests = workshop.display_daily_quests()
        # 保存到文件供选择
        quest_file = workshop.data_dir / "daily_quests.json"
        with open(quest_file, 'w') as f:
            json.dump([asdict(q) for q in quests], f, indent=2)
    
    elif command == "complete" and len(sys.argv) >= 3:
        quest_index = int(sys.argv[2]) - 1
        quest_file = workshop.data_dir / "daily_quests.json"
        
        if quest_file.exists():
            with open(quest_file, 'r') as f:
                quests_data = json.load(f)
                if 0 <= quest_index < len(quests_data):
                    quest = CreativeQuest(**quests_data[quest_index])
                    result = workshop.complete_quest(quest)
                    
                    print(f"\n✅ 任务完成！")
                    print(f"   获得 {result['xp_gained']} XP")
                    if result['streak_bonus'] > 0:
                        print(f"   连胜加成: +{result['streak_bonus']} XP")
                    print(f"   当前进度: {result['current_xp']}/{result['xp_to_next']} XP")
    
    elif command == "status":
        workshop.display_status()
    
    elif command == "music":
        music = workshop.get_mood_music()
        print(f"🎵 推荐音乐: {music}")
    
    elif command == "mood":
        moods = ["专注", "兴奋", "放松", "困倦"]
        print("\n选择心情:")
        for i, mood in enumerate(moods, 1):
            print(f"  {i}. {mood}")
    
    else:
        workshop.display_status()
        workshop.display_daily_quests()


if __name__ == "__main__":
    main()
