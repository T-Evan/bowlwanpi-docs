#!/usr/bin/env python3
"""
BowlWanpi 定时提醒服务
每小时检查一次AI Brain状态，智能提醒
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/modules')

from smart_reminder import SmartReminderSystem
from brain_system import BowlWanpiBrain
from datetime import datetime
import time

def run_periodic_check():
    """运行定期检查"""
    reminder = SmartReminderSystem()
    alerts = reminder.check_all()
    
    if not alerts:
        print(f"✅ [{datetime.now().strftime('%H:%M')}] 状态良好")
        return None
    
    print(f"\n🔔 [{datetime.now().strftime('%H:%M')}] 发现 {len(alerts)} 个提醒:")
    print(reminder.get_alert_summary())
    
    # 返回最高优先级提醒
    critical = [a for a in alerts if a.priority == 'critical']
    if critical:
        return critical[0]
    
    high = [a for a in alerts if a.priority == 'high']
    if high:
        return high[0]
    
    return None


def simulate_day():
    """模拟一天的提醒场景"""
    print("🕐 模拟一天的工作场景...")
    print("=" * 50)
    
    scenarios = [
        ("08:00", "早晨开始", lambda: None),
        ("10:30", "工作2.5小时", lambda: simulate_tired()),
        ("12:00", "午餐时间", lambda: simulate_rest()),
        ("14:00", "下午工作", lambda: None),
        ("16:30", "下午疲劳", lambda: simulate_low_motivation()),
        ("18:00", "下班前", lambda: simulate_habit_pending()),
        ("22:00", "深夜工作", lambda: simulate_overload()),
    ]
    
    for time_str, desc, simulator in scenarios:
        print(f"\n🕐 {time_str} - {desc}")
        simulator()
        alert = run_periodic_check()
        if alert:
            print(f"💡 建议: {alert.suggested_action}")
        time.sleep(0.5)


def simulate_tired():
    """模拟疲劳状态"""
    brain = BowlWanpiBrain()
    brain.emotion_system.state.energy = 0.3

def simulate_rest():
    """模拟休息后"""
    brain = BowlWanpiBrain()
    brain.emotion_system.state.energy = 0.9

def simulate_low_motivation():
    """模拟动机低"""
    brain = BowlWanpiBrain()
    brain.drive.drive = 0.3

def simulate_habit_pending():
    """模拟习惯待完成"""
    # 习惯系统会在检查时发现
    pass

def simulate_overload():
    """模拟认知过载"""
    from insula_system import InsulaSystem
    insula = InsulaSystem()
    # 高频测量模拟过载
    for _ in range(10):
        insula.measure_vitals(task_complexity=0.9, processing_time=5)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--simulate':
        simulate_day()
    else:
        # 单次检查
        alert = run_periodic_check()
        if alert and alert.priority == 'critical':
            print(f"\n🚨 紧急提醒: {alert.message}")
            print(f"💡 {alert.suggested_action}")
