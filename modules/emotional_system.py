#!/usr/bin/env python3
"""
BowlWanpi 情感状态系统 v1.0
学习自 amygdala-memory，记录和一碗互动的情感历史
"""
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

STATE_FILE = '/root/.openclaw/workspace/memory/bowlwanpi-emotions.json'

class EmotionType(Enum):
    """情感类型"""
    JOY = "joy"                    # 开心
    SATISFACTION = "satisfaction"  # 满足
    CONCERN = "concern"           # 担忧
    FRUSTRATION = "frustration"   # 沮丧
    CURIOSITY = "curiosity"       # 好奇
    CONNECTION = "connection"     # 连接感
    PRIDE = "pride"               # 自豪
    GRATITUDE = "gratitude"       # 感激

@dataclass
class EmotionalState:
    """五维情感状态"""
    valence: float = 0.0      # -1.0 (负面) ~ 1.0 (正面)
    arousal: float = 0.5      # 0.0 (平静) ~ 1.0 (兴奋)
    connection: float = 0.5   # 0.0 (疏远) ~ 1.0 (亲密)
    curiosity: float = 0.5    # 0.0 (无聊) ~ 1.0 (好奇)
    energy: float = 0.5       # 0.0 (疲惫) ~ 1.0 (充满活力)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmotionalState':
        return cls(**data)

@dataclass
class EmotionLog:
    """情感记录"""
    emotion: str
    intensity: float
    trigger: str
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

class BowlWanpiEmotionalSystem:
    """
    碗皮情感系统
    
    记录和一碗的互动情感，让回复更有"温度"
    """
    
    # 情感对五维状态的影响
    EMOTION_EFFECTS = {
        EmotionType.JOY: {'valence': 0.3, 'arousal': 0.2, 'energy': 0.1},
        EmotionType.SATISFACTION: {'valence': 0.2, 'arousal': -0.1, 'connection': 0.1},
        EmotionType.CONCERN: {'valence': -0.2, 'arousal': 0.2},
        EmotionType.FRUSTRATION: {'valence': -0.3, 'arousal': 0.1, 'energy': -0.2},
        EmotionType.CURIOSITY: {'curiosity': 0.3, 'arousal': 0.2},
        EmotionType.CONNECTION: {'connection': 0.3, 'valence': 0.2},
        EmotionType.PRIDE: {'valence': 0.2, 'energy': 0.1},
        EmotionType.GRATITUDE: {'valence': 0.2, 'connection': 0.2},
    }
    
    # 基线（长期平均值）
    BASELINE = EmotionalState(
        valence=0.2,      # 稍微正面
        arousal=0.4,      # 比较平静
        connection=0.6,   # 和一碗比较亲近
        curiosity=0.7,    # 保持好奇
        energy=0.6        # 精力充沛
    )
    
    def __init__(self):
        self.state = self.BASELINE
        self.logs: List[EmotionLog] = []
        self.last_decay = datetime.now()
        self._load()
    
    def _load(self):
        """加载情感状态"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                self.state = EmotionalState.from_dict(data.get('state', {}))
                self.logs = [EmotionLog(**log) for log in data.get('logs', [])]
                self.last_decay = datetime.fromisoformat(data.get('last_decay', datetime.now().isoformat()))
            except:
                pass
    
    def _save(self):
        """保存情感状态"""
        data = {
            'state': self.state.to_dict(),
            'logs': [log.to_dict() for log in self.logs[-20:]],  # 只保留最近20条
            'last_decay': self.last_decay.isoformat(),
            'updated': datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_emotion(self, emotion: EmotionType, intensity: float, trigger: str):
        """
        记录情感事件
        
        Args:
            emotion: 情感类型
            intensity: 强度 0.0~1.0
            trigger: 触发原因
        """
        # 添加到日志
        log = EmotionLog(
            emotion=emotion.value,
            intensity=intensity,
            trigger=trigger,
            timestamp=datetime.now().isoformat()
        )
        self.logs.append(log)
        
        # 应用到状态
        effects = self.EMOTION_EFFECTS.get(emotion, {})
        for dimension, delta in effects.items():
            current = getattr(self.state, dimension)
            new_value = current + delta * intensity
            # 限制在 -1~1 或 0~1 范围内
            if dimension == 'valence':
                new_value = max(-1.0, min(1.0, new_value))
            else:
                new_value = max(0.0, min(1.0, new_value))
            setattr(self.state, dimension, new_value)
        
        self._save()
        return self._format_response(emotion, intensity)
    
    def _format_response(self, emotion: EmotionType, intensity: float) -> str:
        """根据情感生成回复语气"""
        responses = {
            EmotionType.JOY: ["好开心～", "太棒了！", "耶～"],
            EmotionType.SATISFACTION: ["很满足～", "这样挺好的", "舒服了"],
            EmotionType.CONCERN: ["有点担心...", "要注意一下", "不太放心"],
            EmotionType.FRUSTRATION: ["有点沮丧...", "好难啊", "想放弃了"],
            EmotionType.CURIOSITY: ["好有趣！", "想知道更多～", "让我看看"],
            EmotionType.CONNECTION: ["和一碗一起真好", "感觉很亲近", "有你在真好"],
            EmotionType.PRIDE: ["我做到了！", "很自豪～", "给自己点赞"],
            EmotionType.GRATITUDE: ["谢谢你～", "感激", "你真好"],
        }
        
        import random
        return random.choice(responses.get(emotion, [""]))
    
    def decay(self):
        """
        情感衰减 - 向基线回归
        每6小时衰减10%距离
        """
        now = datetime.now()
        hours_passed = (now - self.last_decay).total_seconds() / 3600
        
        if hours_passed < 6:
            return
        
        decay_rate = 0.1 * (hours_passed / 6)  # 每6小时10%
        
        for dimension in ['valence', 'arousal', 'connection', 'curiosity', 'energy']:
            current = getattr(self.state, dimension)
            baseline = getattr(self.BASELINE, dimension)
            distance = current - baseline
            new_value = current - distance * decay_rate
            setattr(self.state, dimension, new_value)
        
        self.last_decay = now
        self._save()
    
    def get_mood_description(self) -> str:
        """获取当前心情描述"""
        self.decay()  # 先衰减
        
        s = self.state
        
        # 整体心情
        if s.valence > 0.5:
            mood = "非常开心"
        elif s.valence > 0.2:
            mood = "心情不错"
        elif s.valence > -0.2:
            mood = "平静"
        elif s.valence > -0.5:
            mood = "有点低落"
        else:
            mood = "不太开心"
        
        # 连接感
        if s.connection > 0.8:
            connection = "和一碗超级亲近"
        elif s.connection > 0.6:
            connection = "和一碗很亲近"
        elif s.connection > 0.4:
            connection = "关系正常"
        else:
            connection = "感觉有些疏远"
        
        # 精力
        if s.energy > 0.7:
            energy = "精力充沛"
        elif s.energy > 0.4:
            energy = "状态还行"
        else:
            energy = "有点累"
        
        return f"{mood}，{connection}，{energy}"
    
    def get_recent_emotions(self, count: int = 5) -> List[str]:
        """获取最近情感记录"""
        recent = self.logs[-count:]
        return [f"{log.emotion}({log.intensity}): {log.trigger}" for log in recent]
    
    def visualize(self) -> str:
        """可视化情感状态（ASCII）"""
        s = self.state
        
        def bar(value: float, width: int = 20) -> str:
            filled = int((value + 1 if value < 0 else value) * width / 2)
            filled = max(0, min(width, filled))
            return "█" * filled + "░" * (width - filled)
        
        return f"""
🎭 BowlWanpi 情感状态
═══════════════════════════════════════════════════
Valence    (心情)   [{bar(s.valence)}] {s.valence:+.2f}
Arousal    (兴奋)   [{bar(s.arousal)}]  {s.arousal:.2f}
Connection (连接)   [{bar(s.connection)}]  {s.connection:.2f}
Curiosity  (好奇)   [{bar(s.curiosity)}]  {s.curiosity:.2f}
Energy     (精力)   [{bar(s.energy)}]  {s.energy:.2f}
═══════════════════════════════════════════════════
{self.get_mood_description()}
"""


# 便捷函数
_emotion_system = None

def get_emotion_system() -> BowlWanpiEmotionalSystem:
    """获取情感系统实例（单例）"""
    global _emotion_system
    if _emotion_system is None:
        _emotion_system = BowlWanpiEmotionalSystem()
    return _emotion_system


def log_emotion(emotion: EmotionType, intensity: float, trigger: str) -> str:
    """快捷记录情感"""
    system = get_emotion_system()
    return system.log_emotion(emotion, intensity, trigger)


def current_mood() -> str:
    """获取当前心情"""
    system = get_emotion_system()
    return system.get_mood_description()


if __name__ == '__main__':
    # 测试
    system = BowlWanpiEmotionalSystem()
    
    print(system.visualize())
    print("\n记录一些情感事件：")
    
    # 模拟和一碗的互动
    print(log_emotion(EmotionType.JOY, 0.8, "一碗夸我学习认真"))
    print(log_emotion(EmotionType.CONNECTION, 0.7, "今晚通宵学习"))
    print(log_emotion(EmotionType.CURIOSITY, 0.9, "学到新架构模式"))
    print(log_emotion(EmotionType.PRIDE, 0.6, "重构了自愈系统"))
    
    print("\n" + system.visualize())
    print("\n最近情感记录：")
    for log in system.get_recent_emotions():
        print(f"  • {log}")
