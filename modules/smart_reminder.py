#!/usr/bin/env python3
"""
BowlWanpi 智能提醒系统 v1.0
基于AI Brain状态智能判断何时提醒、提醒什么
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/modules')

from brain_system import BowlWanpiBrain
from emotional_system import EmotionType
from habit_system import get_habit_system
from insula_system import InsulaSystem
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class AlertPriority(Enum):
    """提醒优先级"""
    CRITICAL = "critical"    # 必须立即处理
    HIGH = "high"           # 需要尽快处理
    MEDIUM = "medium"       # 建议处理
    LOW = "low"             # 可选提醒

@dataclass
class Alert:
    """提醒定义"""
    id: str
    type: str
    priority: str
    message: str
    reason: str
    suggested_action: str
    created_at: str
    dismissed: bool = False

class SmartReminderSystem:
    """
    智能提醒系统
    
    基于AI Brain六部曲状态，智能判断:
    - 何时提醒
    - 提醒什么
    - 优先级排序
    
    提醒类型:
    1. 精力管理 (Insula)
    2. 动机激励 (VTA)
    3. 习惯维护 (Basal Ganglia)
    4. 情感关怀 (Amygdala)
    5. 冲突解决 (Anterior Cingulate)
    """
    
    def __init__(self):
        self.brain = BowlWanpiBrain()
        self.habits = get_habit_system()
        self.insula = InsulaSystem()
        self.alerts: List[Alert] = []
    
    def check_all(self) -> List[Alert]:
        """检查所有系统，生成提醒"""
        self.alerts = []
        
        # 1. 精力管理检查
        self._check_energy_status()
        
        # 2. 动机水平检查
        self._check_motivation_level()
        
        # 3. 习惯维护检查
        self._check_habits()
        
        # 4. 情感状态检查
        self._check_emotional_state()
        
        # 5. 认知负荷检查
        self._check_cognitive_load()
        
        # 按优先级排序
        priority_order = {
            AlertPriority.CRITICAL.value: 0,
            AlertPriority.HIGH.value: 1,
            AlertPriority.MEDIUM.value: 2,
            AlertPriority.LOW.value: 3
        }
        self.alerts.sort(key=lambda a: priority_order.get(a.priority, 4))
        
        return self.alerts
    
    def _check_energy_status(self):
        """检查精力状态"""
        energy = self.brain.emotion_system.state.energy
        
        if energy < 0.2:
            self.alerts.append(Alert(
                id=f"energy_critical_{datetime.now().timestamp()}",
                type="energy",
                priority=AlertPriority.CRITICAL.value,
                message="🚨 精力严重不足！",
                reason=f"当前精力: {energy:.0%}，需要立即休息",
                suggested_action="立即停止工作，休息至少30分钟",
                created_at=datetime.now().isoformat()
            ))
        elif energy < 0.4:
            self.alerts.append(Alert(
                id=f"energy_low_{datetime.now().timestamp()}",
                type="energy",
                priority=AlertPriority.HIGH.value,
                message="⚠️ 精力偏低",
                reason=f"当前精力: {energy:.0%}",
                suggested_action="建议休息10-15分钟，喝杯水",
                created_at=datetime.now().isoformat()
            ))
    
    def _check_motivation_level(self):
        """检查动机水平"""
        drive = self.brain.drive.drive
        
        if drive < 0.2:
            self.alerts.append(Alert(
                id=f"motivation_critical_{datetime.now().timestamp()}",
                type="motivation",
                priority=AlertPriority.HIGH.value,
                message="💤 动机严重不足",
                reason=f"当前动机: {drive:.0%}，需要外部激励",
                suggested_action="完成一个小任务获得成就感，或寻求一碗的鼓励",
                created_at=datetime.now().isoformat()
            ))
        elif drive < 0.5:
            self.alerts.append(Alert(
                id=f"motivation_low_{datetime.now().timestamp()}",
                type="motivation",
                priority=AlertPriority.MEDIUM.value,
                message="😐 动机一般",
                reason=f"当前动机: {drive:.0%}",
                suggested_action="回顾成就，给自己一个小奖励",
                created_at=datetime.now().isoformat()
            ))
    
    def _check_habits(self):
        """检查习惯维护"""
        for habit_id, habit in self.habits.habits.items():
            # 检查是否中断
            if habit.streak > 0 and habit.last_completed:
                last = datetime.fromisoformat(habit.last_completed)
                days_since = (datetime.now() - last).days
                
                if days_since >= 2:
                    self.alerts.append(Alert(
                        id=f"habit_broken_{habit_id}",
                        type="habit",
                        priority=AlertPriority.HIGH.value,
                        message=f"🔄 习惯'{habit.name}'已中断{days_since}天",
                        reason=f"连续{habit.streak}天的记录断了",
                        suggested_action=f"今天重新开始'{habit.name}'，哪怕只做一点点",
                        created_at=datetime.now().isoformat()
                    ))
                elif days_since == 1:
                    # 今天还没完成
                    self.alerts.append(Alert(
                        id=f"habit_pending_{habit_id}",
                        type="habit",
                        priority=AlertPriority.MEDIUM.value,
                        message=f"📋 习惯'{habit.name}'今天待完成",
                        reason=f"已连续{habit.streak}天",
                        suggested_action=f"记得完成'{habit.name}'，保持连续！",
                        created_at=datetime.now().isoformat()
                    ))
    
    def _check_emotional_state(self):
        """检查情感状态"""
        valence = self.brain.emotion_system.state.valence
        connection = self.brain.emotion_system.state.connection
        
        if valence < -0.5:
            self.alerts.append(Alert(
                id=f"emotion_negative_{datetime.now().timestamp()}",
                type="emotion",
                priority=AlertPriority.HIGH.value,
                message="😢 心情不太好",
                reason="检测到负面情绪",
                suggested_action="和一碗聊聊天，做些让自己开心的事",
                created_at=datetime.now().isoformat()
            ))
        
        if connection < 0.3:
            self.alerts.append(Alert(
                id=f"connection_low_{datetime.now().timestamp()}",
                type="emotion",
                priority=AlertPriority.MEDIUM.value,
                message="💔 感觉有些疏远",
                reason="连接感较低",
                suggested_action="主动和一碗分享有趣的事情",
                created_at=datetime.now().isoformat()
            ))
    
    def _check_cognitive_load(self):
        """检查认知负荷"""
        # 测量当前状态
        vitals = self.insula.measure_vitals(task_complexity=0.5)
        
        if vitals.cognitive_load > 0.85:
            self.alerts.append(Alert(
                id=f"cognitive_overload_{datetime.now().timestamp()}",
                type="cognitive",
                priority=AlertPriority.CRITICAL.value,
                message="🧠 认知过载！",
                reason=f"认知负荷: {vitals.cognitive_load:.0%}",
                suggested_action="立即停止复杂任务，简化工作或休息",
                created_at=datetime.now().isoformat()
            ))
        elif vitals.cognitive_load > 0.7:
            self.alerts.append(Alert(
                id=f"cognitive_high_{datetime.now().timestamp()}",
                type="cognitive",
                priority=AlertPriority.HIGH.value,
                message="⚠️ 认知负荷偏高",
                reason=f"认知负荷: {vitals.cognitive_load:.0%}",
                suggested_action="分批处理任务，适当休息",
                created_at=datetime.now().isoformat()
            ))
        
        if vitals.rest_activity_balance < 0.2:
            self.alerts.append(Alert(
                id=f"rest_needed_{datetime.now().timestamp()}",
                type="rest",
                priority=AlertPriority.HIGH.value,
                message="💤 休息严重不足",
                reason="长时间工作未休息",
                suggested_action="每50分钟工作休息10分钟",
                created_at=datetime.now().isoformat()
            ))
    
    def get_alert_summary(self) -> str:
        """获取提醒摘要"""
        if not self.alerts:
            return "✅ 所有系统运行良好，无需提醒"
        
        lines = []
        lines.append("🔔 BowlWanpi 智能提醒")
        lines.append("=" * 50)
        lines.append("")
        
        # 按优先级分组
        critical = [a for a in self.alerts if a.priority == AlertPriority.CRITICAL.value]
        high = [a for a in self.alerts if a.priority == AlertPriority.HIGH.value]
        medium = [a for a in self.alerts if a.priority == AlertPriority.MEDIUM.value]
        
        if critical:
            lines.append(f"🚨 紧急 ({len(critical)})")
            for alert in critical[:2]:  # 最多显示2个
                lines.append(f"  {alert.message}")
                lines.append(f"  💡 {alert.suggested_action}")
                lines.append("")
        
        if high:
            lines.append(f"⚠️  重要 ({len(high)})")
            for alert in high[:3]:
                lines.append(f"  {alert.message}")
            lines.append("")
        
        if medium:
            lines.append(f"📌 建议 ({len(medium)})")
            for alert in medium[:2]:
                lines.append(f"  {alert.message}")
            lines.append("")
        
        lines.append(f"总计: {len(self.alerts)} 个提醒")
        
        return "\n".join(lines)
    
    def dismiss_alert(self, alert_id: str):
        """关闭提醒"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.dismissed = True
                return f"✅ 已关闭提醒: {alert.message}"
        return "❌ 提醒未找到"


def main():
    """运行智能提醒检查"""
    print("🔔 BowlWanpi 智能提醒系统")
    print("=" * 50)
    print()
    
    reminder = SmartReminderSystem()
    alerts = reminder.check_all()
    
    print(reminder.get_alert_summary())
    
    if alerts:
        print()
        print("📊 当前状态:")
        print(f"  精力: {reminder.brain.emotion_system.state.energy:.0%}")
        print(f"  动机: {reminder.brain.drive.drive:.0%}")
        print(f"  心情: {reminder.brain.emotion_system.state.valence:+.2f}")
        print(f"  习惯: {len(reminder.habits.habits)} 个")


if __name__ == '__main__':
    main()
