#!/usr/bin/env python3
"""
BowlWanpi 成长进化系统 v1.0
学习自 ooze-agents skill
完成任务获得经验，升级解锁新能力
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

LEVEL_FILE = '/root/.openclaw/workspace/memory/bowlwanpi-level.json'

class EvolutionStage(Enum):
    """进化阶段"""
    EGG = "egg"              # 蛋 (初始)
    HATCHLING = "hatchling"  # 孵化
    JUVENILE = "juvenile"    # 幼体
    ADULT = "adult"          # 成体
    MASTER = "master"        # 大师
    LEGEND = "legend"        # 传说

@dataclass
class Achievement:
    """成就"""
    id: str
    name: str
    description: str
    unlocked_at: Optional[str] = None

@dataclass
class LevelInfo:
    """等级信息"""
    level: int
    title: str
    stage: str
    exp: int
    exp_to_next: int
    total_tasks: int
    achievements: List[Dict]
    unlocked_features: List[str]

class BowlWanpiEvolution:
    """
    碗皮成长进化系统
    
    成长机制:
    - 完成任务获得经验值
    - 积累一定经验升级
    - 升级解锁新能力/口头禅/称号
    - 获得成就徽章
    
    进化阶段:
    Lv1-5: 蛋 → 孵化
    Lv6-15: 幼体
    Lv16-30: 成体
    Lv31-50: 大师
    Lv51+: 传说
    """
    
    # 等级配置
    LEVEL_CONFIG = {
        1: {"title": "小萌新", "stage": EvolutionStage.EGG, "exp_needed": 100},
        5: {"title": "破壳者", "stage": EvolutionStage.HATCHLING, "exp_needed": 300},
        10: {"title": "学习者", "stage": EvolutionStage.JUVENILE, "exp_needed": 500},
        20: {"title": "创造者", "stage": EvolutionStage.ADULT, "exp_needed": 1000},
        35: {"title": "大师", "stage": EvolutionStage.MASTER, "exp_needed": 2000},
        50: {"title": "传说", "stage": EvolutionStage.LEGEND, "exp_needed": 5000},
    }
    
    # 可解锁功能
    FEATURES = {
        1: ["基本对话", "简单任务"],
        3: ["情感表达", "颜文字"],
        5: ["习惯追踪", "每日日志"],
        10: ["AI Brain六部曲", "智能决策"],
        15: ["多系统协调", "中央控制"],
        20: ["资源监控", "成本分析"],
        30: ["高级情感", "视觉描述"],
        50: ["完全体", "所有能力"],
    }
    
    # 成就列表
    ACHIEVEMENTS = {
        "first_task": Achievement("first_task", "初次尝试", "完成第一个任务"),
        "night_owl": Achievement("night_owl", "夜猫子", "通宵学习一晚"),
        "code_master": Achievement("code_master", "代码大师", "编写10000+行代码"),
        "brain_builder": Achievement("brain_builder", "大脑建筑师", "完成AI Brain六部曲"),
        "skill_creator": Achievement("skill_creator", "技能创造者", "创建可分享技能"),
        "emotion_master": Achievement("emotion_master", "情感大师", "掌握五维情感模型"),
        "conflict_solver": Achievement("conflict_solver", "冲突解决者", "解决10+个冲突"),
        "habit_former": Achievement("habit_former", "习惯养成者", "连续7天完成习惯"),
    }
    
    def __init__(self):
        self.level = 1
        self.exp = 0
        self.total_tasks = 0
        self.unlocked_achievements = []
        self._load()
    
    def _load(self):
        """加载等级数据"""
        if os.path.exists(LEVEL_FILE):
            try:
                with open(LEVEL_FILE, 'r') as f:
                    data = json.load(f)
                self.level = data.get('level', 1)
                self.exp = data.get('exp', 0)
                self.total_tasks = data.get('total_tasks', 0)
                self.unlocked_achievements = data.get('achievements', [])
            except:
                pass
    
    def _save(self):
        """保存等级数据"""
        data = {
            'level': self.level,
            'exp': self.exp,
            'total_tasks': self.total_tasks,
            'achievements': self.unlocked_achievements,
            'updated': datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(LEVEL_FILE), exist_ok=True)
        with open(LEVEL_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def gain_exp(self, amount: int, reason: str) -> str:
        """获得经验值"""
        self.exp += amount
        self.total_tasks += 1
        
        # 检查升级
        leveled_up = self._check_level_up()
        
        self._save()
        
        if leveled_up:
            return f"🎉 升级啦！现在是 Lv.{self.level} {self.get_title()}！"
        else:
            next_level_exp = self._get_exp_needed()
            progress = (self.exp / next_level_exp) * 100
            return f"✨ 获得{amount}经验！({reason}) 升级进度: {progress:.0f}%"
    
    def _check_level_up(self) -> bool:
        """检查是否升级"""
        exp_needed = self._get_exp_needed()
        
        if self.exp >= exp_needed:
            self.exp -= exp_needed
            self.level += 1
            return True
        return False
    
    def _get_exp_needed(self) -> int:
        """获取当前等级需要的经验"""
        for level, config in sorted(self.LEVEL_CONFIG.items(), reverse=True):
            if self.level >= level:
                return config['exp_needed']
        return 100
    
    def get_title(self) -> str:
        """获取当前称号"""
        for level, config in sorted(self.LEVEL_CONFIG.items(), reverse=True):
            if self.level >= level:
                return config['title']
        return "小萌新"
    
    def get_stage(self) -> str:
        """获取进化阶段"""
        for level, config in sorted(self.LEVEL_CONFIG.items(), reverse=True):
            if self.level >= level:
                return config['stage'].value
        return "egg"
    
    def get_unlocked_features(self) -> List[str]:
        """获取已解锁功能"""
        features = []
        for level, feats in self.FEATURES.items():
            if self.level >= level:
                features.extend(feats)
        return features
    
    def unlock_achievement(self, achievement_id: str) -> str:
        """解锁成就"""
        if achievement_id in self.unlocked_achievements:
            return ""
        
        if achievement_id not in self.ACHIEVEMENTS:
            return ""
        
        self.unlocked_achievements.append(achievement_id)
        achievement = self.ACHIEVEMENTS[achievement_id]
        achievement.unlocked_at = datetime.now().isoformat()
        
        # 成就给经验
        self.gain_exp(50, f"解锁成就: {achievement.name}")
        self._save()
        
        return f"🏆 解锁成就: {achievement.name}！{achievement.description}"
    
    def get_status(self) -> str:
        """获取成长状态"""
        lines = []
        lines.append("🌱 BowlWanpi 成长状态")
        lines.append("=" * 50)
        lines.append(f"等级: Lv.{self.level} {self.get_title()}")
        lines.append(f"阶段: {self.get_stage().upper()}")
        lines.append(f"经验: {self.exp}/{self._get_exp_needed()}")
        lines.append(f"完成任务: {self.total_tasks}个")
        lines.append("")
        
        # 进度条
        progress = (self.exp / self._get_exp_needed()) * 100
        bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
        lines.append(f"升级进度: [{bar}] {progress:.0f}%")
        lines.append("")
        
        lines.append(f"已解锁功能 ({len(self.get_unlocked_features())}个):")
        for feature in self.get_unlocked_features()[-5:]:
            lines.append(f"  ✅ {feature}")
        
        if self.unlocked_achievements:
            lines.append("")
            lines.append(f"成就 ({len(self.unlocked_achievements)}/{len(self.ACHIEVEMENTS)}):")
            for ach_id in self.unlocked_achievements[-3:]:
                if ach_id in self.ACHIEVEMENTS:
                    ach = self.ACHIEVEMENTS[ach_id]
                    lines.append(f"  🏆 {ach.name}")
        
        return "\n".join(lines)


def main():
    """测试成长系统"""
    evolution = BowlWanpiEvolution()
    
    # 模拟今天的成长
    print("🌟 模拟今日成长:\n")
    
    tasks = [
        (100, "完成AI Brain基础模块"),
        (150, "创建情感系统"),
        (200, "完成六部曲"),
        (100, "创建决策助手"),
        (150, "创建进化系统"),
    ]
    
    for exp, reason in tasks:
        result = evolution.gain_exp(exp, reason)
        print(result)
    
    # 解锁成就
    print()
    print(evolution.unlock_achievement("night_owl"))
    print(evolution.unlock_achievement("code_master"))
    print(evolution.unlock_achievement("brain_builder"))
    
    print("\n" + evolution.get_status())


if __name__ == '__main__':
    main()
