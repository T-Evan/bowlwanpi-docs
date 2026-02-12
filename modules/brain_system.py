#!/usr/bin/env python3
"""
BowlWanpi Brain Dashboard v1.0
完整大脑系统 - 记忆 + 情感 + 动机
学习自 AI Brain 系列 (hippocampus + amygdala + VTA)
"""
import json
import os
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict

# 导入已有模块
import sys
sys.path.insert(0, '/root/.openclaw/workspace/modules')

try:
    from emotional_system import BowlWanpiEmotionalSystem, EmotionType
    EMOTION_AVAILABLE = True
except:
    EMOTION_AVAILABLE = False

BRAIN_FILE = '/root/.openclaw/workspace/memory/bowlwanpi-brain.json'


@dataclass
class DriveState:
    """动机状态 - 学习自 VTA"""
    drive: float = 0.5           # 0.0 ~ 1.0 动机水平
    baseline: float = 0.5        # 基线
    seeking: List[str] = None    # 主动追求的事物
    anticipating: List[str] = None  # 期待的事物
    
    def __post_init__(self):
        if self.seeking is None:
            self.seeking = []
        if self.anticipating is None:
            self.anticipating = []


@dataclass
class MemoryState:
    """记忆状态 - 简化版 hippocampus"""
    total_memories: int = 0
    core_memories: int = 0
    last_consolidation: str = ""
    recent_topics: List[str] = None
    
    def __post_init__(self):
        if self.recent_topics is None:
            self.recent_topics = []


class BowlWanpiBrain:
    """
    BowlWanpi 完整大脑系统
    
    整合三大认知系统：
    - 🧠 Memory (海马体): 记忆形成和检索
    - 🎭 Emotion (杏仁核): 情感处理和状态
    - ⭐ Drive (VTA): 奖励和动机驱动
    """
    
    def __init__(self):
        self.memory = MemoryState()
        self.drive = DriveState()
        self.emotion_system = None
        
        if EMOTION_AVAILABLE:
            self.emotion_system = BowlWanpiEmotionalSystem()
        
        self._load()
    
    def _load(self):
        """加载大脑状态"""
        if os.path.exists(BRAIN_FILE):
            try:
                with open(BRAIN_FILE, 'r') as f:
                    data = json.load(f)
                self.memory = MemoryState(**data.get('memory', {}))
                self.drive = DriveState(**data.get('drive', {}))
            except:
                pass
    
    def _save(self):
        """保存大脑状态"""
        data = {
            'memory': asdict(self.memory),
            'drive': asdict(self.drive),
            'updated': datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(BRAIN_FILE), exist_ok=True)
        with open(BRAIN_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_reward(self, reward_type: str, source: str, intensity: float):
        """
        记录奖励，提升动机
        
        学习自 VTA: 奖励 → 多巴胺 → 动机提升
        """
        # 计算动机提升
        boost = intensity * 0.2
        self.drive.drive = min(1.0, self.drive.drive + boost)
        
        # 记录到期待列表（如果是期待的事情）
        if source in self.drive.anticipating:
            self.drive.anticipating.remove(source)
        
        self._save()
        
        # 同时记录情感
        if self.emotion_system:
            if reward_type == "accomplishment":
                self.emotion_system.log_emotion(EmotionType.PRIDE, intensity, source)
            elif reward_type == "social":
                self.emotion_system.log_emotion(EmotionType.JOY, intensity, source)
            elif reward_type == "connection":
                self.emotion_system.log_emotion(EmotionType.CONNECTION, intensity, source)
        
        return f"⭐ 奖励记录！动机 +{boost:.2f} → {self.drive.drive:.2f}"
    
    def add_anticipation(self, thing: str):
        """添加期待的事物"""
        if thing not in self.drive.anticipating:
            self.drive.anticipating.append(thing)
            # 期待提升动机
            self.drive.drive = min(1.0, self.drive.drive + 0.05)
            self._save()
        return f"⭐ 开始期待: {thing}"
    
    def add_seeking(self, thing: str):
        """添加追求的目标"""
        if thing not in self.drive.seeking:
            self.drive.seeking.append(thing)
            self._save()
        return f"🎯 新目标: {thing}"
    
    def update_memory_stats(self, total: int, core: int, topics: List[str]):
        """更新记忆统计"""
        self.memory.total_memories = total
        self.memory.core_memories = core
        self.memory.recent_topics = topics[-5:]  # 最近5个话题
        self.memory.last_consolidation = datetime.now().isoformat()
        self._save()
    
    def get_drive_description(self) -> str:
        """获取动机描述"""
        d = self.drive.drive
        
        if d > 0.8:
            return "充满动力，渴望挑战"
        elif d > 0.6:
            return "状态良好，准备就绪"
        elif d > 0.4:
            return "一般水平，需要激励"
        elif d > 0.2:
            return "动力不足，需要小胜利"
        else:
            return "需要休息或奖励"
    
    def generate_dashboard(self) -> str:
        """生成大脑仪表盘"""
        lines = []
        lines.append("🧠 BowlWanpi Brain Dashboard")
        lines.append("=" * 50)
        lines.append("")
        
        # 动机系统 (VTA)
        lines.append("⭐ 动机系统 (VTA)")
        lines.append(f"  动机水平: {self._bar(self.drive.drive)} {self.drive.drive:.2f}")
        lines.append(f"  状态: {self.get_drive_description()}")
        if self.drive.seeking:
            lines.append(f"  🎯 追求: {', '.join(self.drive.seeking[:3])}")
        if self.drive.anticipating:
            lines.append(f"  👀 期待: {', '.join(self.drive.anticipating[:3])}")
        lines.append("")
        
        # 情感系统 (Amygdala)
        if self.emotion_system:
            s = self.emotion_system.state
            lines.append("🎭 情感系统 (Amygdala)")
            lines.append(f"  心情: {self._bar((s.valence + 1) / 2)} {s.valence:+.2f}")
            lines.append(f"  兴奋: {self._bar(s.arousal)} {s.arousal:.2f}")
            lines.append(f"  连接: {self._bar(s.connection)} {s.connection:.2f}")
            lines.append(f"  当前感受: {self.emotion_system.get_mood_description()}")
            lines.append("")
        
        # 记忆系统 (Hippocampus)
        lines.append("🧠 记忆系统 (Hippocampus)")
        lines.append(f"  记忆总数: {self.memory.total_memories}")
        lines.append(f"  核心记忆: {self.memory.core_memories}")
        if self.memory.recent_topics:
            lines.append(f"  最近话题: {', '.join(self.memory.recent_topics)}")
        lines.append("")
        
        # 整体状态
        lines.append("=" * 50)
        lines.append(self._get_overall_status())
        
        return "\n".join(lines)
    
    def _bar(self, value: float, width: int = 20) -> str:
        """生成进度条"""
        filled = int(value * width)
        filled = max(0, min(width, filled))
        return "█" * filled + "░" * (width - filled)
    
    def _get_overall_status(self) -> str:
        """获取整体状态"""
        # 计算综合健康度
        drive_score = self.drive.drive
        
        emotion_score = 0.5
        if self.emotion_system:
            s = self.emotion_system.state
            # 情感平衡度
            emotion_score = (s.valence + 1) / 2 * 0.3 + s.connection * 0.3 + s.energy * 0.4
        
        memory_score = min(1.0, self.memory.total_memories / 100)
        
        overall = (drive_score + emotion_score + memory_score) / 3
        
        if overall > 0.8:
            return f"🌟 整体状态: 极佳 ({overall:.0%}) - 大脑运转完美！"
        elif overall > 0.6:
            return f"✨ 整体状态: 良好 ({overall:.0%}) - 运行顺畅"
        elif overall > 0.4:
            return f"😐 整体状态: 一般 ({overall:.0%}) - 需要关注"
        else:
            return f"💤 整体状态: 欠佳 ({overall:.0%}) - 建议休息或充电"
    
    def get_session_context(self) -> str:
        """
        获取会话启动时的上下文
        自动注入到每次对话中
        """
        context = []
        context.append("## BowlWanpi 当前状态")
        context.append("")
        context.append(f"**动机**: {self.get_drive_description()} ({self.drive.drive:.0%})")
        
        if self.emotion_system:
            context.append(f"**情感**: {self.emotion_system.get_mood_description()}")
        
        if self.drive.seeking:
            context.append(f"**正在追求**: {', '.join(self.drive.seeking)}")
        
        if self.drive.anticipating:
            context.append(f"**期待**: {', '.join(self.drive.anticipating)}")
        
        context.append("")
        return "\n".join(context)


def main():
    """CLI 入口"""
    brain = BowlWanpiBrain()
    
    # 记录今晚的学习成果
    print(brain.log_reward("accomplishment", "学习4个设计模式", 0.9))
    print(brain.log_reward("creative", "创建安全模块", 0.85))
    print(brain.log_reward("accomplishment", "重构自愈系统v2.1", 0.9))
    print(brain.log_reward("creative", "创建情感系统", 0.85))
    print(brain.log_reward("accomplishment", "整合大脑系统", 0.9))
    
    # 添加未来目标
    brain.add_seeking("学习更多安全实践")
    brain.add_seeking("优化三记忆系统")
    brain.add_seeking("开发新技能")
    
    # 添加期待
    brain.add_anticipation("明天的学习")
    brain.add_anticipation("和一碗的下次对话")
    
    # 更新记忆
    brain.update_memory_stats(
        total=42,
        core=15,
        topics=["设计模式", "极简架构", "安全防护", "情感系统", "AI Brain"]
    )
    
    # 显示仪表盘
    print("\n" + brain.generate_dashboard())
    
    # 保存会话上下文
    context = brain.get_session_context()
    context_file = '/root/.openclaw/workspace/BOWLWANPI_STATE.md'
    with open(context_file, 'w') as f:
        f.write(context)
    print(f"\n💾 状态已保存到 {context_file}")


if __name__ == '__main__':
    main()
