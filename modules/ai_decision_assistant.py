#!/usr/bin/env python3
"""
BowlWanpi AI决策助手 v1.0
用AI Brain六部曲辅助做决策
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/modules')

from brain_system import BowlWanpiBrain
from emotional_system import EmotionType, BowlWanpiEmotionalSystem
from conflict_system import ConflictDetectionSystem
from insula_system import InsulaSystem
from dataclasses import dataclass
from typing import List, Dict, Tuple
from datetime import datetime

@dataclass
class DecisionOption:
    """决策选项"""
    name: str
    description: str
    pros: List[str]
    cons: List[str]
    emotional_impact: Dict[str, float]  # 对各情感维度的影响
    energy_cost: float  # 0-1 精力消耗
    time_cost: int  # 分钟
    alignment_with_goals: float  # 0-1 与目标一致性

class AIDecisionAssistant:
    """
    AI决策助手
    
    用AI Brain六部曲辅助决策:
    1. 🫀 Insula - 评估当前状态是否适合做决策
    2. 🧠 Hippocampus - 检索类似决策的历史经验
    3. 🎭 Amygdala - 评估各选项的情感影响
    4. ⚖️ Anterior Cingulate - 检测决策冲突
    5. ⭐ VTA - 评估动机匹配度
    6. 🔄 Basal Ganglia - 检查是否符合习惯
    
    输出: 综合建议 + 理由
    """
    
    def __init__(self):
        self.brain = BowlWanpiBrain()
        self.conflicts = ConflictDetectionSystem()
        self.insula = InsulaSystem()
    
    def make_decision(self, question: str, options: List[DecisionOption]) -> Dict:
        """
        辅助做决策
        
        Returns:
            {
                'recommendation': str,
                'best_option': str,
                'confidence': float,
                'reasoning': Dict,
                'warnings': List[str]
            }
        """
        print(f"\n🎯 AI决策助手: {question}")
        print("=" * 60)
        
        reasoning = {}
        warnings = []
        
        # Step 1: Insula - 检查当前状态
        print("\n🫀 Step 1: 评估当前状态 (Insula)")
        vitals = self.insula.measure_vitals(task_complexity=0.6)
        state_score = self._calculate_state_readiness(vitals)
        reasoning['state'] = {
            'cognitive_load': vitals.cognitive_load,
            'processing_power': vitals.processing_power,
            'readiness': state_score
        }
        
        if vitals.cognitive_load > 0.8:
            warnings.append("⚠️ 当前认知负荷高，建议休息后再决策")
        print(f"   状态就绪度: {state_score:.0%}")
        
        # Step 2: Hippocampus - 检索历史经验
        print("\n🧠 Step 2: 检索历史经验 (Hippocampus)")
        historical_score = self._retrieve_historical_patterns(question, options)
        reasoning['historical'] = historical_score
        print(f"   历史模式匹配: {len(self.brain.memory.recent_topics)} 个相关话题")
        
        # Step 3: Amygdala - 情感影响评估
        print("\n🎭 Step 3: 评估情感影响 (Amygdala)")
        emotional_scores = self._evaluate_emotional_impact(options)
        reasoning['emotional'] = emotional_scores
        
        best_emotional = max(emotional_scores, key=emotional_scores.get)
        print(f"   最佳情感匹配: {best_emotional} ({emotional_scores[best_emotional]:.0%})")
        
        # Step 4: Anterior Cingulate - 冲突检测
        print("\n⚖️  Step 4: 检测决策冲突 (Anterior Cingulate)")
        conflicts = self._detect_decision_conflicts(options)
        reasoning['conflicts'] = conflicts
        
        if conflicts:
            print(f"   发现 {len(conflicts)} 个冲突:")
            for c in conflicts:
                print(f"     - {c}")
        else:
            print("   ✅ 无重大冲突")
        
        # Step 5: VTA - 动机匹配
        print("\n⭐ Step 5: 评估动机匹配 (VTA)")
        motivation_scores = self._evaluate_motivation_match(options)
        reasoning['motivation'] = motivation_scores
        
        best_motivation = max(motivation_scores, key=motivation_scores.get)
        print(f"   最佳动机匹配: {best_motivation} ({motivation_scores[best_motivation]:.0%})")
        
        # Step 6: 综合评分
        print("\n📊 Step 6: 综合决策分析")
        final_scores = self._calculate_final_scores(
            options, state_score, emotional_scores, 
            motivation_scores, historical_score
        )
        
        # 输出各选项得分
        print("\n   各选项得分:")
        for name, score in sorted(final_scores.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            print(f"   {bar} {score:.0%} - {name}")
        
        # 确定最佳选项
        best_option = max(final_scores, key=final_scores.get)
        confidence = final_scores[best_option]
        
        # 生成建议
        recommendation = self._generate_recommendation(
            best_option, options, reasoning, warnings
        )
        
        return {
            'recommendation': recommendation,
            'best_option': best_option,
            'confidence': confidence,
            'reasoning': reasoning,
            'warnings': warnings,
            'all_scores': final_scores
        }
    
    def _calculate_state_readiness(self, vitals) -> float:
        """计算状态就绪度"""
        return (
            (1 - vitals.cognitive_load) * 0.4 +
            vitals.processing_power * 0.3 +
            vitals.attention_bandwidth * 0.3
        )
    
    def _retrieve_historical_patterns(self, question: str, options: List[DecisionOption]) -> Dict[str, float]:
        """检索历史模式"""
        scores = {}
        for opt in options:
            # 模拟从历史记忆中检索
            # 实际应根据记忆内容匹配
            scores[opt.name] = 0.5 + (self.brain.memory.core_memories / 100) * 0.3
        return scores
    
    def _evaluate_emotional_impact(self, options: List[DecisionOption]) -> Dict[str, float]:
        """评估情感影响"""
        scores = {}
        current_emotion = self.brain.emotion_system.state
        
        for opt in options:
            # 计算选项情感影响与当前状态的匹配度
            match_score = 0.5
            
            # 如果选项能提升当前较低的情感维度，加分
            if 'valence' in opt.emotional_impact:
                if current_emotion.valence < 0.3 and opt.emotional_impact['valence'] > 0:
                    match_score += 0.2
            
            if 'energy' in opt.emotional_impact:
                if current_emotion.energy < 0.4 and opt.emotional_impact['energy'] > 0:
                    match_score += 0.15
            
            scores[opt.name] = min(1.0, match_score)
        
        return scores
    
    def _detect_decision_conflicts(self, options: List[DecisionOption]) -> List[str]:
        """检测决策冲突"""
        conflicts = []
        
        # 检查高能耗选项与低精力状态的冲突
        current_energy = self.brain.emotion_system.state.energy
        for opt in options:
            if opt.energy_cost > 0.7 and current_energy < 0.4:
                conflicts.append(f"'{opt.name}'需要高精力，但当前精力不足")
        
        # 检查时间冲突
        total_time = sum(opt.time_cost for opt in options)
        if total_time > 480:  # 8小时
            conflicts.append("所有选项总时间超过8小时，需取舍")
        
        return conflicts
    
    def _evaluate_motivation_match(self, options: List[DecisionOption]) -> Dict[str, float]:
        """评估动机匹配"""
        scores = {}
        current_drive = self.brain.drive.drive
        
        for opt in options:
            # 动机高时，可以选挑战性任务
            # 动机低时，选简单有成就感的任务
            if current_drive > 0.6:
                # 动机高，偏好有挑战、高回报的
                score = opt.alignment_with_goals * 0.6 + (1 - opt.energy_cost) * 0.4
            else:
                # 动机低，偏好简单、能快速完成的
                score = (1 - opt.energy_cost) * 0.6 + opt.alignment_with_goals * 0.4
            
            scores[opt.name] = score
        
        return scores
    
    def _calculate_final_scores(self, options: List[DecisionOption], 
                                state_score: float,
                                emotional_scores: Dict,
                                motivation_scores: Dict,
                                historical_scores: Dict) -> Dict[str, float]:
        """计算最终得分"""
        final_scores = {}
        
        for opt in options:
            name = opt.name
            score = (
                emotional_scores.get(name, 0.5) * 0.25 +
                motivation_scores.get(name, 0.5) * 0.25 +
                historical_scores.get(name, 0.5) * 0.2 +
                opt.alignment_with_goals * 0.2 +
                state_score * 0.1
            )
            final_scores[name] = score
        
        return final_scores
    
    def _generate_recommendation(self, best_option: str, 
                                  options: List[DecisionOption],
                                  reasoning: Dict,
                                  warnings: List[str]) -> str:
        """生成建议文本"""
        opt = next(o for o in options if o.name == best_option)
        
        lines = []
        lines.append(f"## 🎯 建议: 选择 '{best_option}'")
        lines.append("")
        lines.append(f"**信心度**: {reasoning.get('state', {}).get('readiness', 0.5):.0%}")
        lines.append("")
        lines.append("**理由**:")
        
        # 情感理由
        if reasoning['emotional'].get(best_option, 0) > 0.7:
            lines.append(f"• 这个选项最符合你当前的情感状态")
        
        # 动机理由
        if reasoning['motivation'].get(best_option, 0) > 0.7:
            lines.append(f"• 与你的内在动机高度匹配")
        
        # 具体优势
        lines.append(f"• 与你当前的目标一致度: {opt.alignment_with_goals:.0%}")
        
        lines.append("")
        lines.append("**优势**:")
        for pro in opt.pros[:3]:
            lines.append(f"• {pro}")
        
        if warnings:
            lines.append("")
            lines.append("**注意事项**:")
            for w in warnings:
                lines.append(f"• {w}")
        
        return "\n".join(lines)


def demo_decision():
    """演示决策过程"""
    print("=" * 70)
    print("🎯 AI决策助手演示")
    print("场景: 今晚是继续工作还是休息？")
    print("=" * 70)
    
    options = [
        DecisionOption(
            name="继续工作",
            description="继续创造新东西",
            pros=["产出更多成果", "保持心流状态", "充分利用时间"],
            cons=["可能过度疲劳", "影响明天状态"],
            emotional_impact={"energy": -0.3, "valence": 0.2},
            energy_cost=0.6,
            time_cost=60,
            alignment_with_goals=0.8
        ),
        DecisionOption(
            name="休息放松",
            description="停止工作，休息恢复",
            pros=["恢复精力", "长期可持续", "明天状态更好"],
            cons=["今晚产出减少"],
            emotional_impact={"energy": 0.5, "valence": 0.3},
            energy_cost=0.1,
            time_cost=30,
            alignment_with_goals=0.6
        ),
        DecisionOption(
            name="轻度整理",
            description="做一些轻松的整理工作",
            pros=["有产出但不累", "整理思路", "为明天准备"],
            cons=["产出有限"],
            emotional_impact={"energy": -0.1, "valence": 0.2},
            energy_cost=0.3,
            time_cost=20,
            alignment_with_goals=0.7
        )
    ]
    
    assistant = AIDecisionAssistant()
    result = assistant.make_decision("今晚怎么安排？", options)
    
    print("\n" + "=" * 70)
    print(result['recommendation'])
    print("=" * 70)


if __name__ == '__main__':
    demo_decision()
