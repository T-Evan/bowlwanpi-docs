#!/usr/bin/env python3
"""
成就系统 v2.0 - 重构版
每日灵感简报扩展模块

优化点：
- 类型注解
- 结构化日志
- 错误处理
- 配置驱动
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('achievements')


@dataclass
class Achievement:
    """成就数据类"""
    id: str
    name: str
    description: str
    icon: str
    points: int
    category: str
    unlocked: bool = False


@dataclass
class TaskRecord:
    """任务记录数据类"""
    type: str
    difficulty: str
    time: str


@dataclass
class DailyLog:
    """每日日志"""
    date: str
    tasks: List[TaskRecord] = field(default_factory=list)


class AchievementConfig:
    """成就配置管理"""
    
    ACHIEVEMENT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
        # 连续创造
        "streak_3": {
            "name": "🔥 三连击", "desc": "连续3天完成创造挑战",
            "icon": "🔥", "points": 10, "category": "streak"
        },
        "streak_7": {
            "name": "🌟 一周创造者", "desc": "连续7天完成创造挑战",
            "icon": "🌟", "points": 25, "category": "streak"
        },
        "streak_30": {
            "name": "👑 月度创造者", "desc": "连续30天完成创造挑战",
            "icon": "👑", "points": 100, "category": "streak"
        },
        
        # 数量成就
        "count_10": {
            "name": "📝 创造者", "desc": "完成10个创造任务",
            "icon": "📝", "points": 15, "category": "count"
        },
        "count_50": {
            "name": "🚀 高产出者", "desc": "完成50个创造任务",
            "icon": "🚀", "points": 50, "category": "count"
        },
        "count_100": {
            "name": "🎯 创造大师", "desc": "完成100个创造任务",
            "icon": "🎯", "points": 150, "category": "count"
        },
        
        # 类型成就
        "type_skill": {
            "name": "🛠️ 技能开发者", "desc": "完成5个技能开发任务",
            "icon": "🛠️", "points": 20, "category": "type"
        },
        "type_content": {
            "name": "✍️ 内容创作者", "desc": "完成5个内容创作任务",
            "icon": "✍️", "points": 20, "category": "type"
        },
        "type_auto": {
            "name": "⚙️ 自动化专家", "desc": "完成5个自动化任务",
            "icon": "⚙️", "points": 20, "category": "type"
        },
        "type_explore": {
            "name": "🔍 探索者", "desc": "完成5个探索任务",
            "icon": "🔍", "points": 20, "category": "type"
        },
        
        # 特殊成就
        "early_bird": {
            "name": "🌅 早起鸟", "desc": "在早上8点前完成创造",
            "icon": "🌅", "points": 15, "category": "special"
        },
        "night_owl": {
            "name": "🦉 夜猫子", "desc": "在晚上11点后完成创造",
            "icon": "🦉", "points": 15, "category": "special"
        },
        "weekend_warrior": {
            "name": "🎮 周末战士", "desc": "在周末完成创造",
            "icon": "🎮", "points": 10, "category": "special"
        },
        "perfect_week": {
            "name": "💯 完美周", "desc": "一周内每天都完成创造",
            "icon": "💯", "points": 30, "category": "special"
        },
        
        # 难度成就
        "hard_worker": {
            "name": "💪 挑战者", "desc": "完成5个困难任务",
            "icon": "💪", "points": 25, "category": "difficulty"
        },
        "masterpiece": {
            "name": "🎨 杰作", "desc": "完成1个史诗级任务",
            "icon": "🎨", "points": 50, "category": "difficulty"
        },
    }
    
    TYPE_MAP = {
        "skill": "type_skill",
        "content": "type_content",
        "auto": "type_auto",
        "explore": "type_explore"
    }
    
    @classmethod
    def get_achievement(cls, ach_id: str) -> Optional[Achievement]:
        """获取成就定义"""
        if ach_id not in cls.ACHIEVEMENT_DEFINITIONS:
            return None
        data = cls.ACHIEVEMENT_DEFINITIONS[ach_id]
        return Achievement(
            id=ach_id,
            name=data["name"],
            description=data["desc"],
            icon=data["icon"],
            points=data["points"],
            category=data["category"]
        )


class AchievementSystem:
    """成就系统核心类"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化成就系统
        
        Args:
            data_dir: 数据目录，默认使用 ~/.openclaw/workspace/pkm/achievements
        """
        if data_dir is None:
            data_dir = Path.home() / ".openclaw/workspace/pkm/achievements"
        
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.data_dir / "progress.json"
        self.progress = self._load_progress()
        
        logger.info(f"成就系统初始化完成，数据目录: {self.data_dir}")
    
    def _load_progress(self) -> Dict[str, Any]:
        """加载用户进度"""
        default_progress = {
            "unlocked": [],
            "stats": {
                "total_completed": 0,
                "current_streak": 0,
                "max_streak": 0,
                "by_type": defaultdict(int),
                "by_difficulty": defaultdict(int),
                "total_points": 0,
                "last_completion": None
            },
            "daily_log": {}
        }
        
        if not self.progress_file.exists():
            logger.info("创建新的进度文件")
            return default_progress
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保数据结构完整
                for key in default_progress:
                    if key not in data:
                        data[key] = default_progress[key]
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"加载进度文件失败: {e}")
            return default_progress
    
    def _save_progress(self) -> bool:
        """保存进度"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                # 转换 defaultdict 为普通 dict
                progress_to_save = {
                    **self.progress,
                    "stats": {
                        **self.progress["stats"],
                        "by_type": dict(self.progress["stats"]["by_type"]),
                        "by_difficulty": dict(self.progress["stats"]["by_difficulty"])
                    }
                }
                json.dump(progress_to_save, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"保存进度失败: {e}")
            return False
    
    def record_completion(
        self, 
        task_type: str, 
        difficulty: str, 
        timestamp: Optional[datetime] = None
    ) -> List[Achievement]:
        """
        记录任务完成
        
        Args:
            task_type: 任务类型
            difficulty: 难度级别
            timestamp: 完成时间，默认当前时间
            
        Returns:
            新解锁的成就列表
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        logger.info(f"记录任务完成: type={task_type}, difficulty={difficulty}")
        
        # 更新统计
        stats = self.progress["stats"]
        stats["total_completed"] += 1
        stats["by_type"][task_type] += 1
        stats["by_difficulty"][difficulty] += 1
        
        # 更新连续天数
        self._update_streak(timestamp)
        
        # 记录到 daily_log
        self._add_to_daily_log(task_type, difficulty, timestamp)
        
        # 检查新成就
        new_achievements = self._check_achievements(timestamp)
        
        # 保存
        if self._save_progress():
            logger.info(f"进度保存成功，新解锁成就: {len(new_achievements)} 个")
        
        return new_achievements
    
    def _update_streak(self, timestamp: datetime) -> None:
        """更新连续天数"""
        stats = self.progress["stats"]
        date_str = timestamp.strftime("%Y-%m-%d")
        last_date = stats["last_completion"]
        
        if last_date:
            try:
                last = datetime.strptime(last_date, "%Y-%m-%d")
                today = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                diff = (today - last).days
                
                if diff == 1:
                    stats["current_streak"] += 1
                    logger.info(f"连胜继续: {stats['current_streak']} 天")
                elif diff > 1:
                    logger.info(f"连胜中断，重新计数")
                    stats["current_streak"] = 1
            except ValueError:
                logger.warning(f"日期解析失败: {last_date}")
                stats["current_streak"] = 1
        else:
            stats["current_streak"] = 1
        
        stats["max_streak"] = max(stats["max_streak"], stats["current_streak"])
        stats["last_completion"] = date_str
    
    def _add_to_daily_log(
        self, 
        task_type: str, 
        difficulty: str, 
        timestamp: datetime
    ) -> None:
        """添加到每日日志"""
        date_str = timestamp.strftime("%Y-%m-%d")
        
        if date_str not in self.progress["daily_log"]:
            self.progress["daily_log"][date_str] = []
        
        self.progress["daily_log"][date_str].append({
            "type": task_type,
            "difficulty": difficulty,
            "time": timestamp.strftime("%H:%M")
        })
    
    def _check_achievements(self, timestamp: datetime) -> List[Achievement]:
        """检查是否解锁新成就"""
        new_unlocked: List[str] = []
        stats = self.progress["stats"]
        unlocked = self.progress["unlocked"]
        
        # 检查连续天数成就
        self._check_streak_achievements(stats, unlocked, new_unlocked)
        
        # 检查数量成就
        self._check_count_achievements(stats, unlocked, new_unlocked)
        
        # 检查类型成就
        self._check_type_achievements(stats, unlocked, new_unlocked)
        
        # 检查难度成就
        self._check_difficulty_achievements(stats, unlocked, new_unlocked)
        
        # 检查特殊成就
        self._check_special_achievements(timestamp, unlocked, new_unlocked)
        
        # 更新解锁列表和积分
        result = []
        for ach_id in new_unlocked:
            unlocked.append(ach_id)
            ach = AchievementConfig.get_achievement(ach_id)
            if ach:
                ach.unlocked = True
                stats["total_points"] += ach.points
                result.append(ach)
                logger.info(f"解锁成就: {ach.name}")
        
        return result
    
    def _check_streak_achievements(
        self, 
        stats: Dict, 
        unlocked: List[str], 
        new_unlocked: List[str]
    ) -> None:
        """检查连续天数成就"""
        streak_checks = [
            (3, "streak_3"), (7, "streak_7"), (30, "streak_30")
        ]
        for threshold, ach_id in streak_checks:
            if stats["current_streak"] >= threshold and ach_id not in unlocked:
                new_unlocked.append(ach_id)
    
    def _check_count_achievements(
        self, 
        stats: Dict, 
        unlocked: List[str], 
        new_unlocked: List[str]
    ) -> None:
        """检查数量成就"""
        count_checks = [
            (10, "count_10"), (50, "count_50"), (100, "count_100")
        ]
        for threshold, ach_id in count_checks:
            if stats["total_completed"] >= threshold and ach_id not in unlocked:
                new_unlocked.append(ach_id)
    
    def _check_type_achievements(
        self, 
        stats: Dict, 
        unlocked: List[str], 
        new_unlocked: List[str]
    ) -> None:
        """检查类型成就"""
        for type_key, count in stats["by_type"].items():
            if type_key in AchievementConfig.TYPE_MAP:
                ach_id = AchievementConfig.TYPE_MAP[type_key]
                if count >= 5 and ach_id not in unlocked:
                    new_unlocked.append(ach_id)
    
    def _check_difficulty_achievements(
        self, 
        stats: Dict, 
        unlocked: List[str], 
        new_unlocked: List[str]
    ) -> None:
        """检查难度成就"""
        hard_count = (
            stats["by_difficulty"].get("困难", 0) + 
            stats["by_difficulty"].get("史诗", 0)
        )
        if hard_count >= 5 and "hard_worker" not in unlocked:
            new_unlocked.append("hard_worker")
        
        if stats["by_difficulty"].get("史诗", 0) >= 1 and "masterpiece" not in unlocked:
            new_unlocked.append("masterpiece")
    
    def _check_special_achievements(
        self, 
        timestamp: datetime, 
        unlocked: List[str], 
        new_unlocked: List[str]
    ) -> None:
        """检查特殊成就"""
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        if hour < 8 and "early_bird" not in unlocked:
            new_unlocked.append("early_bird")
        if hour >= 23 and "night_owl" not in unlocked:
            new_unlocked.append("night_owl")
        if weekday >= 5 and "weekend_warrior" not in unlocked:
            new_unlocked.append("weekend_warrior")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        stats = self.progress["stats"]
        return {
            "achievements": self.progress["unlocked"],
            "total_points": stats["total_points"],
            "current_streak": stats["current_streak"],
            "max_streak": stats["max_streak"],
            "total_completed": stats["total_completed"]
        }
    
    def display_achievements(self) -> None:
        """显示成就列表"""
        print("\n🏆 成就系统 v2.0")
        print("=" * 50)
        
        all_defs = AchievementConfig.ACHIEVEMENT_DEFINITIONS
        unlocked = set(self.progress["unlocked"])
        stats = self.progress["stats"]
        
        print(f"\n进度: {len(unlocked)}/{len(all_defs)} ({len(unlocked)/len(all_defs)*100:.1f}%)")
        print(f"总积分: {stats['total_points']} 点")
        print(f"当前连胜: {stats['current_streak']} 天")
        print(f"最高连胜: {stats['max_streak']} 天")
        print(f"完成任务: {stats['total_completed']} 个\n")
        
        # 按分类显示
        categories = {
            "streak": "连续创造",
            "count": "数量达成",
            "type": "类型专精",
            "special": "特殊成就",
            "difficulty": "难度挑战"
        }
        
        for cat_id, cat_name in categories.items():
            cat_achievements = [
                (aid, data) for aid, data in all_defs.items()
                if data["category"] == cat_id
            ]
            if cat_achievements:
                print(f"\n{cat_name}:")
                for ach_id, data in cat_achievements:
                    status = "✅" if ach_id in unlocked else "🔒"
                    print(f"  {status} {data['icon']} {data['name']} - {data['desc']}")


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
                print(f"  {ach_data.icon} {ach_data.name} - {ach_data.description}")
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
