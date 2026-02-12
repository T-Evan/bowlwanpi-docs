#!/usr/bin/env python3
"""
BowlWanpi 冲突检测系统 v1.0
学习自 Anterior Cingulate (前扣带皮层) - Conflict Detection
检测决策冲突、目标矛盾、资源竞争
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum

CONFLICT_FILE = '/root/.openclaw/workspace/memory/bowlwanpi-conflicts.json'

class ConflictType(Enum):
    """冲突类型"""
    GOAL_CONFLICT = "goal_conflict"      # 目标冲突
    RESOURCE_COMPETITION = "resource"     # 资源竞争
    PRIORITY_CLASH = "priority"           # 优先级冲突
    VALUE_MISMATCH = "value"              # 价值观不一致
    TIME_PRESSURE = "time"                # 时间压力

class ConflictSeverity(Enum):
    """冲突严重程度"""
    LOW = "low"           # 轻微，可忽略
    MEDIUM = "medium"     # 中等，需要注意
    HIGH = "high"         # 严重，必须解决
    CRITICAL = "critical" # 危急，立即处理

@dataclass
class Conflict:
    """冲突定义"""
    id: str
    type: str
    severity: str
    description: str
    option_a: str
    option_b: str
    detected_at: str
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None

class ConflictDetectionSystem:
    """
    冲突检测系统
    
    检测:
    - 目标冲突: 多个目标互相矛盾
    - 资源竞争: 多个任务争夺同一资源
    - 优先级冲突: 高优先级任务被低优先级阻塞
    - 价值观冲突: 行为与核心原则矛盾
    - 时间压力: 截止时间冲突
    
    解决策略:
    - 优先级排序
    - 资源重新分配
    - 目标调整
    - 时间管理
    """
    
    def __init__(self):
        self.conflicts: List[Conflict] = []
        self.resolved_conflicts: List[Conflict] = []
        self._load()
    
    def _load(self):
        """加载冲突数据"""
        if os.path.exists(CONFLICT_FILE):
            try:
                with open(CONFLICT_FILE, 'r') as f:
                    data = json.load(f)
                for c in data.get('conflicts', []):
                    self.conflicts.append(Conflict(**c))
                for c in data.get('resolved', []):
                    self.resolved_conflicts.append(Conflict(**c))
            except:
                pass
    
    def _save(self):
        """保存冲突数据"""
        data = {
            'conflicts': [asdict(c) for c in self.conflicts],
            'resolved': [asdict(c) for c in self.resolved_conflicts[-20:]],  # 保留最近20条
            'updated': datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(CONFLICT_FILE), exist_ok=True)
        with open(CONFLICT_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def detect_goal_conflict(self, goals: List[Dict]) -> List[Conflict]:
        """
        检测目标冲突
        
        例如:
        - "学习新技能" vs "休息"
        - "快速完成任务" vs "保证质量"
        """
        conflicts = []
        
        for i, goal1 in enumerate(goals):
            for goal2 in goals[i+1:]:
                # 检查直接矛盾
                if self._are_conflicting(goal1, goal2):
                    conflict = Conflict(
                        id=f"conflict_{datetime.now().timestamp()}",
                        type=ConflictType.GOAL_CONFLICT.value,
                        severity=self._assess_severity(goal1, goal2),
                        description=f"目标冲突: {goal1['name']} vs {goal2['name']}",
                        option_a=goal1['name'],
                        option_b=goal2['name'],
                        detected_at=datetime.now().isoformat()
                    )
                    conflicts.append(conflict)
                    self.conflicts.append(conflict)
        
        if conflicts:
            self._save()
        
        return conflicts
    
    def _are_conflicting(self, goal1: Dict, goal2: Dict) -> bool:
        """判断两个目标是否冲突"""
        # 时间冲突
        if goal1.get('time') == goal2.get('time'):
            return True
        
        # 资源冲突
        if goal1.get('resource') == goal2.get('resource'):
            return True
        
        # 方向冲突 (如: 学习 vs 休息)
        opposing_pairs = [
            ('学习', '休息'),
            ('工作', '娱乐'),
            ('快速', '质量'),
            ('探索', '稳定'),
        ]
        
        for pair in opposing_pairs:
            if (pair[0] in goal1['name'] and pair[1] in goal2['name']) or \
               (pair[1] in goal1['name'] and pair[0] in goal2['name']):
                return True
        
        return False
    
    def _assess_severity(self, goal1: Dict, goal2: Dict) -> str:
        """评估冲突严重程度"""
        # 都是高优先级
        if goal1.get('priority') == 'high' and goal2.get('priority') == 'high':
            return ConflictSeverity.HIGH.value
        
        # 一个高一个低
        if goal1.get('priority') == 'high' or goal2.get('priority') == 'high':
            return ConflictSeverity.MEDIUM.value
        
        return ConflictSeverity.LOW.value
    
    def detect_resource_competition(self, tasks: List[Dict]) -> List[Conflict]:
        """检测资源竞争"""
        conflicts = []
        resource_usage = {}
        
        for task in tasks:
            resource = task.get('resource')
            if resource:
                if resource in resource_usage:
                    # 资源冲突
                    conflict = Conflict(
                        id=f"resource_{datetime.now().timestamp()}",
                        type=ConflictType.RESOURCE_COMPETITION.value,
                        severity=ConflictSeverity.MEDIUM.value,
                        description=f"资源竞争: {resource}",
                        option_a=resource_usage[resource]['name'],
                        option_b=task['name'],
                        detected_at=datetime.now().isoformat()
                    )
                    conflicts.append(conflict)
                    self.conflicts.append(conflict)
                else:
                    resource_usage[resource] = task
        
        if conflicts:
            self._save()
        
        return conflicts
    
    def resolve_conflict(self, conflict_id: str, resolution: str) -> str:
        """解决冲突"""
        for conflict in self.conflicts:
            if conflict.id == conflict_id:
                conflict.resolved = True
                conflict.resolution = resolution
                conflict.resolved_at = datetime.now().isoformat()
                
                self.resolved_conflicts.append(conflict)
                self.conflicts.remove(conflict)
                self._save()
                
                return f"✅ 冲突已解决: {conflict.description}\n   解决方案: {resolution}"
        
        return "❌ 冲突未找到"
    
    def get_conflict_report(self) -> str:
        """生成冲突报告"""
        if not self.conflicts:
            return "✅ 当前无冲突，系统运行顺畅"
        
        lines = []
        lines.append("⚖️ BowlWanpi 冲突检测报告")
        lines.append("=" * 50)
        lines.append("")
        
        # 按严重程度分组
        critical = [c for c in self.conflicts if c.severity == 'critical']
        high = [c for c in self.conflicts if c.severity == 'high']
        medium = [c for c in self.conflicts if c.severity == 'medium']
        low = [c for c in self.conflicts if c.severity == 'low']
        
        if critical:
            lines.append(f"🔴 严重冲突 ({len(critical)})")
            for c in critical:
                lines.append(f"  • {c.description}")
                lines.append(f"    选项A: {c.option_a}")
                lines.append(f"    选项B: {c.option_b}")
            lines.append("")
        
        if high:
            lines.append(f"🟠 高优先级冲突 ({len(high)})")
            for c in high:
                lines.append(f"  • {c.description}")
            lines.append("")
        
        if medium:
            lines.append(f"🟡 中等冲突 ({len(medium)})")
            for c in medium:
                lines.append(f"  • {c.description}")
            lines.append("")
        
        if low:
            lines.append(f"🟢 轻微冲突 ({len(low)})")
            for c in low:
                lines.append(f"  • {c.description}")
            lines.append("")
        
        # 建议
        lines.append("💡 建议:")
        if critical or high:
            lines.append("  • 优先解决严重冲突")
            lines.append("  • 考虑调整目标或资源分配")
        else:
            lines.append("  • 当前冲突可控，继续监控")
        
        return "\n".join(lines)
    
    def suggest_resolution(self, conflict: Conflict) -> List[str]:
        """建议解决方案"""
        suggestions = []
        
        if conflict.type == ConflictType.GOAL_CONFLICT.value:
            suggestions = [
                f"先完成'{conflict.option_a}'，再处理'{conflict.option_b}'",
                f"将两个目标分解为更小的任务，交替进行",
                f"评估哪个目标更重要，优先完成",
                f"寻求一碗的意见和帮助",
            ]
        elif conflict.type == ConflictType.RESOURCE_COMPETITION.value:
            suggestions = [
                "重新分配资源，按优先级排序",
                "寻找替代资源或工具",
                "分时段使用资源",
                "并行化任务减少资源占用",
            ]
        elif conflict.type == ConflictType.TIME_PRESSURE.value:
            suggestions = [
                "重新评估时间估算",
                "请求延期或调整截止日期",
                "减少任务范围，聚焦核心",
                "寻求帮助或协作",
            ]
        
        return suggestions


def main():
    """测试冲突检测"""
    cds = ConflictDetectionSystem()
    
    # 模拟目标冲突
    goals = [
        {'name': '深度学习', 'priority': 'high', 'time': 'evening'},
        {'name': '休息', 'priority': 'medium', 'time': 'evening'},
        {'name': '检查系统', 'priority': 'high', 'resource': 'cpu'},
        {'name': '生成报告', 'priority': 'high', 'resource': 'cpu'},
    ]
    
    print("检测目标冲突...")
    goal_conflicts = cds.detect_goal_conflict(goals)
    print(f"发现 {len(goal_conflicts)} 个目标冲突\n")
    
    print("检测资源竞争...")
    resource_conflicts = cds.detect_resource_competition(goals)
    print(f"发现 {len(resource_conflicts)} 个资源竞争\n")
    
    print(cds.get_conflict_report())


if __name__ == '__main__':
    main()
