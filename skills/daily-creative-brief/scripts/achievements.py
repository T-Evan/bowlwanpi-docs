#!/usr/bin/env python3
"""
成就系统 - 每日灵感简报扩展
追踪创造成就，解锁徽章
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class AchievementSystem:
    def __init__(self):
        self.data_dir = Path.home() / ".openclaw/workspace/pkm/achievements"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.achievements_file = self.data_dir / "achievements.json"
        self.progress_file = self.data_dir / "progress.json"
        
        self.achievements = self._load_achievements()
        self.progress = self._load_progress()
        
    def _load_achievements(self):
        """加载成就定义"""
        return {
            # 连续创造
            "streak_3": {"name": "🔥 三连击", "desc": "连续3天完成创造挑战", "icon": "🔥", "points": 10},
            "streak_7": {"name": "🌟 一周创造者", "desc": "连续7天完成创造挑战", "icon": "🌟", "points": 25},
            "streak_30": {"name": "👑 月度创造者", "desc": "连续30天完成创造挑战", "icon": "👑", "points": 100},
            
            # 数量成就
            "count_10": {"name": "📝 创造者", "desc": "完成10个创造任务", "icon": "📝", "points": 15},
            "count_50": {"name": "🚀 高产出者", "desc": "完成50个创造任务", "icon": "🚀", "points": 50},
            "count_100": {"name": "🎯 创造大师", "desc": "完成100个创造任务", "icon": "🎯", "points": 150},
            
            # 类型成就
            "type_skill": {"name": "🛠️ 技能开发者", "desc": "完成5个技能开发任务", "icon": "🛠️", "points": 20},
            "type_content": {"name": "✍️ 内容创作者", "desc": "完成5个内容创作任务", "icon": "✍️", "points": 20},
            "type_auto": {"name": "⚙️ 自动化专家", "desc": "完成5个自动化任务", "icon": "⚙️", "points": 20},
            "type_explore": {"name": "🔍 探索者", "desc": "完成5个探索任务", "icon": "🔍", "points": 20},
            
            # 特殊成就
            "early_bird": {"name": "🌅 早起鸟", "desc": "在早上8点前完成创造", "icon": "🌅", "points": 15},
            "night_owl": {"name": "🦉 夜猫子", "desc": "在晚上11点后完成创造", "icon": "🦉", "points": 15},
            "weekend_warrior": {"name": "🎮 周末战士", "desc": "在周末完成创造", "icon": "🎮", "points": 10},
            "perfect_week": {"name": "💯 完美周", "desc": "一周内每天都完成创造", "icon": "💯", "points": 30},
            
            # 难度成就
            "hard_worker": {"name": "💪 挑战者", "desc": "完成5个困难任务", "icon": "💪", "points": 25},
            "masterpiece": {"name": "🎨 杰作", "desc": "完成1个史诗级任务", "icon": "🎨", "points": 50},
        }
    
    def _load_progress(self):
        """加载用户进度"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "unlocked": [],
            "stats": {
                "total_completed": 0,
                "current_streak": 0,
                "max_streak": 0,
                "by_type": {
                    "skill": 0,
                    "content": 0,
                    "auto": 0,
                    "explore": 0,
                    "optimize": 0,
                    "creative": 0
                },
                "by_difficulty": {
                    "简单": 0,
                    "中等": 0,
                    "困难": 0,
                    "史诗": 0
                },
                "total_points": 0,
                "last_completion": None
            },
            "daily_log": {}
        }
    
    def _save_progress(self):
        """保存进度"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def record_completion(self, task_type, difficulty, timestamp=None):
        """记录任务完成"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # 更新统计
        self.progress["stats"]["total_completed"] += 1
        self.progress["stats"]["by_type"][task_type] = \
            self.progress["stats"]["by_type"].get(task_type, 0) + 1
        self.progress["stats"]["by_difficulty"][difficulty] += 1
        
        # 更新连续天数
        date_str = timestamp.strftime("%Y-%m-%d")
        last_date = self.progress["stats"]["last_completion"]
        
        if last_date:
            last = datetime.strptime(last_date, "%Y-%m-%d")
            today = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            diff = (today - last).days
            
            if diff == 1:
                self.progress["stats"]["current_streak"] += 1
            elif diff > 1:
                self.progress["stats"]["current_streak"] = 1
        else:
            self.progress["stats"]["current_streak"] = 1
        
        self.progress["stats"]["max_streak"] = \
            max(self.progress["stats"]["max_streak"], self.progress["stats"]["current_streak"])
        self.progress["stats"]["last_completion"] = date_str
        
        # 记录到 daily_log
        if date_str not in self.progress["daily_log"]:
            self.progress["daily_log"][date_str] = []
        self.progress["daily_log"][date_str].append({
            "type": task_type,
            "difficulty": difficulty,
            "time": timestamp.strftime("%H:%M")
        })
        
        # 检查新成就
        new_achievements = self._check_achievements(timestamp)
        
        self._save_progress()
        return new_achievements
    
    def _check_achievements(self, timestamp):
        """检查是否解锁新成就"""
        new_unlocked = []
        stats = self.progress["stats"]
        
        # 检查连续天数成就
        if stats["current_streak"] >= 3 and "streak_3" not in self.progress["unlocked"]:
            new_unlocked.append("streak_3")
        if stats["current_streak"] >= 7 and "streak_7" not in self.progress["unlocked"]:
            new_unlocked.append("streak_7")
        if stats["current_streak"] >= 30 and "streak_30" not in self.progress["unlocked"]:
            new_unlocked.append("streak_30")
        
        # 检查数量成就
        if stats["total_completed"] >= 10 and "count_10" not in self.progress["unlocked"]:
            new_unlocked.append("count_10")
        if stats["total_completed"] >= 50 and "count_50" not in self.progress["unlocked"]:
            new_unlocked.append("count_50")
        if stats["total_completed"] >= 100 and "count_100" not in self.progress["unlocked"]:
            new_unlocked.append("count_100")
        
        # 检查类型成就
        for type_key, count in stats["by_type"].items():
            achievement_map = {
                "skill": "type_skill",
                "content": "type_content",
                "auto": "type_auto",
                "explore": "type_explore"
            }
            if type_key in achievement_map:
                ach_id = achievement_map[type_key]
                if count >= 5 and ach_id not in self.progress["unlocked"]:
                    new_unlocked.append(ach_id)
        
        # 检查难度成就
        hard_count = stats["by_difficulty"].get("困难", 0) + stats["by_difficulty"].get("史诗", 0)
        if hard_count >= 5 and "hard_worker" not in self.progress["unlocked"]:
            new_unlocked.append("hard_worker")
        if stats["by_difficulty"].get("史诗", 0) >= 1 and "masterpiece" not in self.progress["unlocked"]:
            new_unlocked.append("masterpiece")
        
        # 检查特殊成就
        hour = timestamp.hour
        if hour < 8 and "early_bird" not in self.progress["unlocked"]:
            new_unlocked.append("early_bird")
        if hour >= 23 and "night_owl" not in self.progress["unlocked"]:
            new_unlocked.append("night_owl")
        
        weekday = timestamp.weekday()
        if weekday >= 5 and "weekend_warrior" not in self.progress["unlocked"]:
            new_unlocked.append("weekend_warrior")
        
        # 更新解锁列表和积分
        for ach_id in new_unlocked:
            self.progress["unlocked"].append(ach_id)
            self.progress["stats"]["total_points"] += self.achievements[ach_id]["points"]
        
        return [self.achievements[aid] for aid in new_unlocked]
    
    def get_status(self):
        """获取当前状态"""
        return {
            "achievements": self.progress["unlocked"],
            "total_points": self.progress["stats"]["total_points"],
            "current_streak": self.progress["stats"]["current_streak"],
            "max_streak": self.progress["stats"]["max_streak"],
            "total_completed": self.progress["stats"]["total_completed"]
        }
    
    def get_all_achievements(self):
        """获取所有成就列表"""
        result = []
        for aid, data in self.achievements.items():
            result.append({
                "id": aid,
                **data,
                "unlocked": aid in self.progress["unlocked"]
            })
        return result
    
    def display_achievements(self):
        """显示成就列表"""
        print("\n🏆 成就系统")
        print("=" * 50)
        
        all_achievements = self.get_all_achievements()
        unlocked_count = len(self.progress["unlocked"])
        total_count = len(all_achievements)
        
        print(f"\n进度: {unlocked_count}/{total_count} ({unlocked_count/total_count*100:.1f}%)")
        print(f"总积分: {self.progress['stats']['total_points']} 点")
        print(f"当前连胜: {self.progress['stats']['current_streak']} 天")
        print(f"最高连胜: {self.progress['stats']['max_streak']} 天")
        print(f"完成任务: {self.progress['stats']['total_completed']} 个\n")
        
        print("已解锁成就:")
        for ach in all_achievements:
            if ach["unlocked"]:
                print(f"  ✅ {ach['icon']} {ach['name']} - {ach['desc']} (+{ach['points']}点)")
        
        print("\n待解锁成就:")
        for ach in all_achievements:
            if not ach["unlocked"]:
                print(f"  🔒 {ach['icon']} {ach['name']} - {ach['desc']} (+{ach['points']}点)")


def main():
    import sys
    
    ach = AchievementSystem()
    
    if len(sys.argv) < 2:
        ach.display_achievements()
        return
    
    command = sys.argv[1]
    
    if command == "record" and len(sys.argv) >= 4:
        task_type = sys.argv[2]
        difficulty = sys.argv[3]
        new_achievements = ach.record_completion(task_type, difficulty)
        
        if new_achievements:
            print("\n🎉 解锁新成就！")
            for ach_data in new_achievements:
                print(f"  {ach_data['icon']} {ach_data['name']} - {ach_data['desc']}")
        else:
            print("✅ 进度已记录")
    
    elif command == "status":
        status = ach.get_status()
        print(f"\n连胜: {status['current_streak']} 天")
        print(f"总任务: {status['total_completed']} 个")
        print(f"积分: {status['total_points']} 点")
        print(f"成就: {len(status['achievements'])} 个")
    
    else:
        ach.display_achievements()


if __name__ == "__main__":
    main()
