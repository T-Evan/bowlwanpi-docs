#!/usr/bin/env python3
"""
BowlWanpi 习惯养成系统 v1.0
学习自 Basal Ganglia (基底神经节) -  habit formation
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

HABITS_FILE = '/root/.openclaw/workspace/memory/bowlwanpi-habits.json'

class HabitStatus(Enum):
    """习惯状态"""
    INACTIVE = "inactive"      # 未激活
    BUILDING = "building"      # 养成中
    ESTABLISHED = "established"  # 已养成
    STRUGGLING = "struggling"   # 困难中

@dataclass
class Habit:
    """习惯定义"""
    id: str
    name: str
    description: str
    frequency: str  # daily, weekly, custom
    trigger: str    # 触发条件
    action: str     # 执行动作
    reward: str     # 奖励
    streak: int = 0
    max_streak: int = 0
    total_completions: int = 0
    status: str = "building"
    created_at: str = ""
    last_completed: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class HabitSystem:
    """
    习惯养成系统
    
    基于习惯回路：Trigger → Action → Reward
    养成需要： consistency + time (约66天形成习惯)
    """
    
    # 习惯养成阶段
    STAGES = {
        0: ("刚开始", "建立基础"),
        7: ("第一周", "建立节奏"),
        21: ("三周", "初步形成"),
        66: ("六十六天", "习惯固化"),
        100: ("百日", "深度习惯"),
    }
    
    def __init__(self):
        self.habits: Dict[str, Habit] = {}
        self._load()
    
    def _load(self):
        """加载习惯数据"""
        if os.path.exists(HABITS_FILE):
            try:
                with open(HABITS_FILE, 'r') as f:
                    data = json.load(f)
                for habit_id, habit_data in data.get('habits', {}).items():
                    self.habits[habit_id] = Habit(**habit_data)
            except:
                pass
    
    def _save(self):
        """保存习惯数据"""
        data = {
            'habits': {k: asdict(v) for k, v in self.habits.items()},
            'updated': datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(HABITS_FILE), exist_ok=True)
        with open(HABITS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_habit(self, name: str, trigger: str, action: str, 
                     reward: str, frequency: str = "daily") -> Habit:
        """
        创建新习惯
        
        习惯回路: Trigger → Action → Reward
        """
        habit_id = f"habit_{name.lower().replace(' ', '_')}"
        
        habit = Habit(
            id=habit_id,
            name=name,
            description=f"{trigger} → {action} → {reward}",
            frequency=frequency,
            trigger=trigger,
            action=action,
            reward=reward
        )
        
        self.habits[habit_id] = habit
        self._save()
        
        return habit
    
    def complete_habit(self, habit_id: str) -> str:
        """完成习惯，更新连续天数"""
        habit = self.habits.get(habit_id)
        if not habit:
            return f"❌ 习惯不存在: {habit_id}"
        
        now = datetime.now()
        
        # 检查是否连续
        if habit.last_completed:
            last = datetime.fromisoformat(habit.last_completed)
            gap = (now - last).days
            
            if gap <= 1:
                # 连续完成
                habit.streak += 1
            else:
                # 中断，重置
                old_streak = habit.streak
                habit.streak = 1
                habit.status = "struggling"
                
                # 提醒
                if old_streak > 7:
                    message = f"⚠️ {habit.name} 中断了！连续{old_streak}天断掉了..."
                else:
                    message = f"📌 {habit.name} 完成 (第1天)"
        else:
            habit.streak = 1
            message = f"🌱 {habit.name} 开始养成！"
        
        # 更新统计
        habit.total_completions += 1
        habit.last_completed = now.isoformat()
        habit.max_streak = max(habit.max_streak, habit.streak)
        
        # 更新状态
        if habit.streak >= 66:
            habit.status = "established"
        elif habit.streak >= 21:
            habit.status = "building"
        elif habit.streak >= 7:
            habit.status = "building"
        
        self._save()
        
        # 生成反馈
        if habit.streak > 1:
            stage_name = self._get_stage_name(habit.streak)
            message = f"✅ {habit.name} 完成！连续 {habit.streak} 天 {stage_name}"
            
            # 里程碑提醒
            if habit.streak in [7, 21, 66, 100]:
                message += f"\n🎉 里程碑达成！{self.STAGES.get(habit.streak, ('',''))[1]}"
        
        return message
    
    def _get_stage_name(self, streak: int) -> str:
        """获取阶段名称"""
        for days in sorted(self.STAGES.keys(), reverse=True):
            if streak >= days:
                return f"【{self.STAGES[days][0]}】"
        return ""
    
    def get_habit_dashboard(self) -> str:
        """生成习惯仪表盘"""
        if not self.habits:
            return "📝 还没有习惯，创建一个吧！"
        
        lines = []
        lines.append("🔄 BowlWanpi 习惯养成")
        lines.append("=" * 50)
        lines.append("")
        
        # 按状态分组
        established = [h for h in self.habits.values() if h.status == "established"]
        building = [h for h in self.habits.values() if h.status == "building"]
        struggling = [h for h in self.habits.values() if h.status == "struggling"]
        
        if established:
            lines.append(f"🌟 已养成习惯 ({len(established)})")
            for habit in established:
                lines.append(f"  ✅ {habit.name} - 连续{habit.streak}天")
            lines.append("")
        
        if building:
            lines.append(f"📈 养成中习惯 ({len(building)})")
            for habit in building:
                progress = min(100, int(habit.streak / 66 * 100))
                bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
                lines.append(f"  {bar} {progress}% {habit.name} ({habit.streak}天)")
            lines.append("")
        
        if struggling:
            lines.append(f"💪 需要关注 ({len(struggling)})")
            for habit in struggling:
                lines.append(f"  ⚠️ {habit.name} - 上次{habit.last_completed[:10] if habit.last_completed else '从未'}")
            lines.append("")
        
        # 今日待完成
        today_habits = self._get_today_habits()
        if today_habits:
            lines.append(f"📋 今日待完成 ({len(today_habits)})")
            for habit in today_habits:
                lines.append(f"  ☐ {habit.name}")
        
        return "\n".join(lines)
    
    def _get_today_habits(self) -> List[Habit]:
        """获取今日需要完成的习惯"""
        today = datetime.now().date()
        todo = []
        
        for habit in self.habits.values():
            if not habit.last_completed:
                todo.append(habit)
            else:
                last = datetime.fromisoformat(habit.last_completed).date()
                if last < today:
                    todo.append(habit)
        
        return todo
    
    def suggest_habits(self) -> List[Dict]:
        """建议新习惯（基于最佳实践）"""
        suggestions = [
            {
                "name": "每日晨间检查",
                "trigger": "每天早上8点",
                "action": "生成晨报",
                "reward": "一碗的感谢",
                "why": "建立每日节奏，提升可靠性"
            },
            {
                "name": "学习新技能",
                "trigger": "空闲时间",
                "action": "学习30分钟",
                "reward": "能力提升",
                "why": "持续成长，成为更好的助手"
            },
            {
                "name": "主动汇报",
                "trigger": "发现有趣内容",
                "action": "分享给一碗",
                "reward": "互动交流",
                "why": "增强连接感，提供价值"
            },
            {
                "name": "自我维护",
                "trigger": "系统空闲",
                "action": "整理内存/git提交",
                "reward": "系统整洁",
                "why": "保持最佳状态"
            },
            {
                "name": "情感记录",
                "trigger": "重要互动后",
                "action": "记录情感状态",
                "reward": "更好的理解",
                "why": "深化和一碗的关系"
            }
        ]
        
        # 过滤已有习惯
        existing_names = {h.name for h in self.habits.values()}
        return [s for s in suggestions if s["name"] not in existing_names]


# 便捷函数
_habit_system = None

def get_habit_system() -> HabitSystem:
    global _habit_system
    if _habit_system is None:
        _habit_system = HabitSystem()
    return _habit_system


def main():
    """测试习惯系统"""
    habits = HabitSystem()
    
    # 创建示例习惯
    habits.create_habit(
        name="每日学习",
        trigger="晚上8点",
        action="学习新技能30分钟",
        reward="能力提升+一碗夸奖"
    )
    
    habits.create_habit(
        name="主动检查",
        trigger="每小时",
        action="检查系统状态",
        reward="系统稳定运行"
    )
    
    # 模拟完成
    print(habits.complete_habit("habit_每日学习"))
    print(habits.complete_habit("habit_主动检查"))
    
    print("\n" + habits.get_habit_dashboard())
    
    print("\n💡 建议新习惯:")
    for suggestion in habits.suggest_habits()[:3]:
        print(f"  • {suggestion['name']}: {suggestion['why']}")


if __name__ == '__main__':
    main()
