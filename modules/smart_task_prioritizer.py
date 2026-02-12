#!/usr/bin/env python3
"""
BowlWanpi 智能任务优先级排序器
综合AI Brain六部曲状态，给出最优执行顺序
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/modules')

from brain_system import BowlWanpiBrain
from emotional_system import EmotionType
from conflict_system import ConflictDetectionSystem
from insula_system import InsulaSystem
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime

@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    priority: str  # critical, high, medium, low
    estimated_time: int  # 分钟
    energy_cost: float  # 0-1
    emotional_requirement: str  # 需要的心情: positive, calm, focused
    deadline: str  # ISO格式或None
    dependencies: List[str]  # 依赖的其他任务ID

class SmartTaskPrioritizer:
    """
    智能任务优先级排序器
    
    综合以下因素排序:
    - 截止时间紧急度
    - 当前精力水平
    - 情感状态匹配
    - 任务依赖关系
    - 动机水平
    - 认知负荷
    """
    
    def __init__(self):
        self.brain = BowlWanpiBrain()
        self.conflicts = ConflictDetectionSystem()
        self.insula = InsulaSystem()
    
    def prioritize(self, tasks: List[Task]) -> List[Tuple[Task, float, str]]:
        """
        对任务进行智能排序
        
        Returns:
            [(task, score, reason), ...] 按优先级排序
        """
        print("📝 智能任务优先级排序")
        print("=" * 60)
        
        # 获取当前状态
        current_state = self._get_current_state()
        print(f"\n当前状态:")
        print(f"  精力: {current_state['energy']:.0%}")
        print(f"  心情: {current_state['valence']:+.2f}")
        print(f"  动机: {current_state['drive']:.0%}")
        print(f"  认知负荷: {current_state['cognitive_load']:.0%}")
        
        # 计算每个任务的得分
        scored_tasks = []
        for task in tasks:
            score, reason = self._calculate_task_score(task, current_state)
            scored_tasks.append((task, score, reason))
        
        # 按得分排序
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        
        # 输出排序结果
        print(f"\n排序结果:")
        for i, (task, score, reason) in enumerate(scored_tasks, 1):
            bar = "█" * int(score * 15) + "░" * (15 - int(score * 15))
            print(f"\n{i}. [{bar} {score:.0%}] {task.name}")
            print(f"   💡 {reason}")
        
        return scored_tasks
    
    def _get_current_state(self) -> Dict:
        """获取当前状态"""
        vitals = self.insula.measure_vitals(task_complexity=0.3)
        
        return {
            'energy': self.brain.emotion_system.state.energy,
            'valence': self.brain.emotion_system.state.valence,
            'drive': self.brain.drive.drive,
            'cognitive_load': vitals.cognitive_load,
            'processing_power': vitals.processing_power
        }
    
    def _calculate_task_score(self, task: Task, state: Dict) -> Tuple[float, str]:
        """计算任务得分"""
        scores = []
        reasons = []
        
        # 1. 截止时间权重 (30%)
        urgency_score = self._calculate_urgency(task.deadline)
        scores.append(urgency_score * 0.30)
        if urgency_score > 0.8:
            reasons.append("紧急")
        
        # 2. 精力匹配度 (25%)
        if state['energy'] >= task.energy_cost:
            energy_score = 1.0
            reasons.append("精力充足")
        else:
            energy_score = 0.5
            reasons.append("精力不足但可完成")
        scores.append(energy_score * 0.25)
        
        # 3. 情感匹配度 (20%)
        emotion_score = self._calculate_emotion_match(task.emotional_requirement, state)
        scores.append(emotion_score * 0.20)
        if emotion_score > 0.8:
            reasons.append("情感状态匹配")
        
        # 4. 原始优先级 (15%)
        priority_scores = {'critical': 1.0, 'high': 0.8, 'medium': 0.5, 'low': 0.2}
        scores.append(priority_scores.get(task.priority, 0.5) * 0.15)
        
        # 5. 动机匹配度 (10%)
        if state['drive'] > 0.6:
            # 动机高时，优先挑战性任务
            motivation_score = task.energy_cost
        else:
            # 动机低时，优先简单任务
            motivation_score = 1 - task.energy_cost
        scores.append(motivation_score * 0.10)
        
        total_score = sum(scores)
        reason_str = ", ".join(reasons) if reasons else "一般"
        
        return total_score, reason_str
    
    def _calculate_urgency(self, deadline: str) -> float:
        """计算紧急度"""
        if not deadline:
            return 0.3
        
        try:
            deadline_dt = datetime.fromisoformat(deadline)
            now = datetime.now()
            hours_left = (deadline_dt - now).total_seconds() / 3600
            
            if hours_left < 0:
                return 1.0  # 已过期
            elif hours_left < 4:
                return 0.9
            elif hours_left < 24:
                return 0.7
            elif hours_left < 72:
                return 0.5
            else:
                return 0.3
        except:
            return 0.5
    
    def _calculate_emotion_match(self, requirement: str, state: Dict) -> float:
        """计算情感匹配度"""
        valence = state['valence']
        
        if requirement == 'positive':
            return max(0, (valence + 1) / 2)
        elif requirement == 'calm':
            return 1.0 - abs(valence) * 0.5
        elif requirement == 'focused':
            return 0.8 if valence > -0.3 else 0.4
        else:
            return 0.5
    
    def generate_execution_plan(self, tasks: List[Task]) -> str:
        """生成执行计划"""
        sorted_tasks = self.prioritize(tasks)
        
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("📋 智能执行计划")
        lines.append("=" * 60)
        
        total_time = sum(t[0].estimated_time for t in sorted_tasks)
        lines.append(f"\n预计总时间: {total_time}分钟 ({total_time//60}小时{total_time%60}分钟)")
        lines.append("\n建议执行顺序:")
        
        current_time = 0
        for i, (task, score, reason) in enumerate(sorted_tasks, 1):
            lines.append(f"\n{i}. {task.name}")
            lines.append(f"   预计时间: {task.estimated_time}分钟")
            lines.append(f"   优先级: {task.priority}")
            lines.append(f"   推荐理由: {reason}")
            current_time += task.estimated_time
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def demo():
    """演示任务排序"""
    tasks = [
        Task("1", "完善AI决策助手", "high", 30, 0.6, "focused", None, []),
        Task("2", "修复系统Bug", "critical", 45, 0.5, "focused", "2026-02-12T23:00:00", []),
        Task("3", "回复邮件", "low", 10, 0.2, "calm", None, []),
        Task("4", "学习新技能", "medium", 60, 0.7, "positive", None, []),
        Task("5", "整理文档", "low", 20, 0.3, "calm", None, []),
    ]
    
    prioritizer = SmartTaskPrioritizer()
    plan = prioritizer.generate_execution_plan(tasks)
    print(plan)


if __name__ == '__main__':
    demo()
