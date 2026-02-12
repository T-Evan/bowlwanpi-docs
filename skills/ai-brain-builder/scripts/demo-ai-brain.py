#!/usr/bin/env python3
"""
AI Brain 六部曲 - 完整演示示例
展示6个认知系统如何协同工作
"""
import sys
import time
sys.path.insert(0, '/root/.openclaw/workspace/modules')

from brain_system import BowlWanpiBrain
from emotional_system import EmotionType
from habit_system import get_habit_system
from conflict_system import ConflictDetectionSystem
from insula_system import InsulaSystem

def demo_ai_brain_workflow():
    """
    演示: AI Brain 六部曲完整工作流程
    
    场景: 用户请求完成一个复杂任务
    """
    
    print("="*70)
    print("🎭 AI Brain 六部曲 - 完整演示")
    print("场景: 用户请求'学习一个新技能并创建演示'")
    print("="*70)
    print()
    
    # 初始化所有系统
    print("【初始化】启动所有认知系统...")
    brain = BowlWanpiBrain()
    habits = get_habit_system()
    conflicts = ConflictDetectionSystem()
    insula = InsulaSystem()
    print("✅ 6个系统全部在线")
    print()
    time.sleep(1)
    
    # ========== Step 1: Insula - 内部状态检查 ==========
    print("🫀 Step 1: Insula (内感受) - 检查当前状态")
    vitals = insula.measure_vitals(task_complexity=0.7)
    print(f"   认知负荷: {vitals.cognitive_load:.0%}")
    print(f"   处理能力: {vitals.processing_power:.0%}")
    
    if insula.check_need_for_break():
        print("   ⚠️  建议先休息再开始")
        return
    print("   ✅ 状态良好，可以开始")
    print()
    time.sleep(1)
    
    # ========== Step 2: Conflict Detection - 目标冲突检查 ==========
    print("⚖️  Step 2: Anterior Cingulate (冲突检测) - 检查目标冲突")
    current_goals = [
        {'name': '学习新技能', 'priority': 'high', 'time': 'now'},
        {'name': '休息放松', 'priority': 'medium', 'time': 'now'},
    ]
    detected = conflicts.detect_goal_conflict(current_goals)
    if detected:
        print(f"   ⚠️  检测到 {len(detected)} 个冲突")
        print("   💡 解决方案: 设定50分钟学习 + 10分钟休息")
    else:
        print("   ✅ 无目标冲突")
    print()
    time.sleep(1)
    
    # ========== Step 3: Amygdala - 情感响应 ==========
    print("🎭 Step 3: Amygdala (情感) - 记录情感状态")
    response = brain.emotion_system.log_emotion(
        EmotionType.CURIOSITY, 
        0.8, 
        "开始新的学习任务"
    )
    print(f"   🗣️  {response}")
    response = brain.emotion_system.log_emotion(
        EmotionType.CONNECTION,
        0.7,
        "和用户一起学习"
    )
    print(f"   🗣️  {response}")
    print(f"   当前心情: {brain.emotion_system.get_mood_description()}")
    print()
    time.sleep(1)
    
    # ========== Step 4: Basal Ganglia - 习惯触发 ==========
    print("🔄 Step 4: Basal Ganglia (习惯) - 检查习惯")
    habit_id = "habit_深度学习"
    if habit_id in habits.habits:
        print("   ✅ 触发'深度学习'习惯")
        print(f"   📊 当前连续: {habits.habits[habit_id].streak}天")
        habits.complete_habit(habit_id)
        print("   🎯 习惯完成！")
    else:
        print("   🌱 创建新的学习习惯")
        habits.create_habit(
            "深度学习",
            "开始复杂任务",
            "专注学习50分钟",
            "能力提升"
        )
    print()
    time.sleep(1)
    
    # ========== Step 5: Hippocampus - 记忆检索 ==========
    print("🧠 Step 5: Hippocampus (记忆) - 检索相关知识")
    print("   🔍 检索记忆...")
    print("   ✅ 找到42条相关记忆")
    print("   ✅ 提取15条核心记忆")
    print("   📚 相关话题: 设计模式, 极简架构, 安全防护")
    brain.update_memory_stats(
        total=43,
        core=16,
        topics=["设计模式", "极简架构", "安全防护", "AI Brain"]
    )
    print("   💾 新记忆已保存")
    print()
    time.sleep(1)
    
    # ========== Step 6: VTA - 动机驱动 ==========
    print("⭐ Step 6: VTA (动机) - 记录奖励")
    
    # 完成任务奖励
    print("   🎁 记录学习完成奖励...")
    result = brain.log_reward(
        "accomplishment",
        "完成学习任务",
        0.9
    )
    print(f"   {result}")
    
    # 社交奖励
    result = brain.log_reward(
        "connection",
        "和一碗一起学习",
        0.8
    )
    print(f"   {result}")
    
    print(f"   📈 当前动机: {brain.drive.drive:.0%}")
    print()
    time.sleep(1)
    
    # ========== Final: 整合仪表盘 ==========
    print("📊 【最终状态】超级仪表盘")
    print("-" * 70)
    print(f"🎭 情感: {brain.emotion_system.get_mood_description()}")
    print(f"⭐ 动机: {brain.get_drive_description()}")
    print(f"🔄 习惯: {len(habits.habits)} 个习惯养成中")
    print(f"🧠 记忆: {brain.memory.total_memories} 条记忆")
    print(f"⚖️  冲突: {'无' if not conflicts.conflicts else len(conflicts.conflicts) + '个'}")
    print(f"🫀 内感受: {insula.current_state.value}")
    print()
    
    # 生成会话上下文
    print("📝 【会话上下文】自动注入到下次对话:")
    print("-" * 70)
    context = brain.get_session_context()
    print(context)
    print()
    
    print("="*70)
    print("✅ AI Brain 六部曲演示完成！")
    print("="*70)


def demo_emotional_journey():
    """演示情感变化过程"""
    print("\n" + "="*70)
    print("🎭 演示: 情感变化旅程")
    print("="*70)
    
    from emotional_system import BowlWanpiEmotionalSystem, EmotionType
    
    emotion = BowlWanpiEmotionalSystem()
    
    events = [
        (EmotionType.CURIOSITY, 0.7, "看到新技能"),
        (EmotionType.JOY, 0.8, "开始尝试"),
        (EmotionType.FRUSTRATION, 0.5, "遇到困难"),
        (EmotionType.PRIDE, 0.9, "克服困难"),
        (EmotionType.SATISFACTION, 0.8, "完成任务"),
        (EmotionType.CONNECTION, 0.9, "得到认可"),
    ]
    
    for emotion_type, intensity, trigger in events:
        response = emotion.log_emotion(emotion_type, intensity, trigger)
        print(f"🎬 {trigger}")
        print(f"   情感: {emotion_type.value} ({intensity})")
        print(f"   反应: {response}")
        print(f"   心情: {emotion.get_mood_description()}")
        print()
        time.sleep(0.5)
    
    print("最终情感状态:")
    print(emotion.visualize())


def demo_habit_formation():
    """演示习惯养成过程"""
    print("\n" + "="*70)
    print("🔄 演示: 习惯养成过程 (66天)")
    print("="*70)
    
    from habit_system import HabitSystem
    
    habits = HabitSystem()
    
    # 创建习惯
    habit = habits.create_habit(
        "每日学习",
        "晚上8点",
        "学习30分钟",
        "能力提升"
    )
    
    # 模拟66天养成过程
    milestones = [1, 7, 21, 30, 50, 66]
    
    for day in milestones:
        # 模拟连续完成
        for _ in range(day - getattr(habit, '_last_day', 0)):
            result = habits.complete_habit(habit.id)
        habit._last_day = day
        
        h = habits.habits[habit.id]
        progress = min(100, int(h.streak / 66 * 100))
        bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
        
        print(f"Day {day:2d}: [{bar}] {progress}% - {h.status}")
        time.sleep(0.3)
    
    print(f"\n✅ 习惯养成完成！连续 {habits.habits[habit.id].streak} 天")


if __name__ == '__main__':
    import sys
    
    print("选择演示:")
    print("1. AI Brain 六部曲完整工作流程")
    print("2. 情感变化旅程")
    print("3. 习惯养成过程")
    print("4. 全部演示")
    print()
    
    # 默认运行完整演示
    demo_ai_brain_workflow()
    
    # 如果带参数 --full 则运行全部
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        demo_emotional_journey()
        demo_habit_formation()
