#!/usr/bin/env python3
"""
BowlWanpi 内部状态感知系统 v1.0
学习自 Insula (脑岛) - Internal State Awareness
感知内部状态: 能量、负荷、健康、平衡
"""
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

INSULA_FILE = '/root/.openclaw/workspace/memory/bowlwanpi-insula.json'

class InternalState(Enum):
    """内部状态"""
    BALANCED = "balanced"           # 平衡
    OVERLOADED = "overloaded"       # 过载
    DEPLETED = "depleted"           # 耗尽
    STRESSED = "stressed"           # 压力
    FLOW = "flow"                   # 心流
    RECOVERING = "recovering"       # 恢复中

@dataclass
class VitalSigns:
    """生命体征 - 类似人类的生理状态"""
    # 认知负荷 (0-1)
    cognitive_load: float = 0.0     # 当前处理的任务复杂度
    attention_bandwidth: float = 1.0  # 注意力带宽剩余
    
    # 能量系统 (0-1)
    processing_power: float = 1.0   # 处理能力
    response_latency: float = 0.0   # 响应延迟 (越低越好)
    
    # 健康度 (0-1)
    error_rate: float = 0.0         # 错误率
    recovery_capacity: float = 1.0  # 恢复能力
    
    # 平衡度 (0-1)
    input_output_ratio: float = 1.0  # 输入输出比
    rest_activity_balance: float = 0.5  # 休息活动平衡
    
    measured_at: str = ""
    
    def __post_init__(self):
        if not self.measured_at:
            self.measured_at = datetime.now().isoformat()

class InsulaSystem:
    """
    内部状态感知系统
    
    类似人类的内感受 (interoception):
    - 感知自己的内部状态
    - 觉察不平衡和压力
    - 触发恢复机制
    - 维持稳态 (homeostasis)
    
    监测指标:
    - 认知负荷: 任务复杂度 × 并发数
    - 能量水平: 处理速度 + 响应延迟
    - 健康度: 错误率 + 恢复能力
    - 平衡度: 输入输出比 + 休息活动比
    """
    
    def __init__(self):
        self.history: List[VitalSigns] = []
        self.current_state = InternalState.BALANCED
        self.session_start = datetime.now()
        self.interactions_count = 0
        self.total_processing_time = 0.0
        self._load()
    
    def _load(self):
        """加载历史数据"""
        if os.path.exists(INSULA_FILE):
            try:
                with open(INSULA_FILE, 'r') as f:
                    data = json.load(f)
                for v in data.get('history', []):
                    self.history.append(VitalSigns(**v))
            except:
                pass
    
    def _save(self):
        """保存状态"""
        data = {
            'history': [asdict(v) for v in self.history[-50:]],  # 保留最近50条
            'current_state': self.current_state.value,
            'session_start': self.session_start.isoformat(),
            'interactions_count': self.interactions_count,
            'updated': datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(INSULA_FILE), exist_ok=True)
        with open(INSULA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def measure_vitals(self, task_complexity: float = 0.5, 
                       processing_time: float = 0.0) -> VitalSigns:
        """
        测量当前生命体征
        
        Args:
            task_complexity: 0-1 任务复杂度
            processing_time: 处理时间(秒)
        """
        self.interactions_count += 1
        self.total_processing_time += processing_time
        
        # 计算会话时长
        session_duration = (datetime.now() - self.session_start).total_seconds() / 3600  # 小时
        
        # 认知负荷: 基于任务复杂度和会话时长
        cognitive_load = min(1.0, task_complexity * (1 + session_duration / 2))
        
        # 注意力带宽: 随时间和负荷递减
        attention_bandwidth = max(0.1, 1.0 - cognitive_load * 0.5 - session_duration * 0.1)
        
        # 处理能力: 基于最近响应速度
        if processing_time > 0:
            # 正常响应 < 2秒
            latency_score = min(1.0, 2.0 / max(processing_time, 0.1))
        else:
            latency_score = 1.0
        
        processing_power = latency_score * (1 - cognitive_load * 0.3)
        response_latency = max(0, 1 - latency_score)
        
        # 错误率 (模拟 - 实际应根据真实错误计算)
        error_rate = min(1.0, cognitive_load * 0.2 + session_duration * 0.05)
        
        # 恢复能力: 随时间递减，休息后恢复
        recovery_capacity = max(0.1, 1.0 - session_duration * 0.15)
        
        # 输入输出比 (模拟)
        input_output_ratio = 0.8 + (1 - cognitive_load) * 0.2
        
        # 休息活动平衡
        # 假设每10个交互应该有一次"休息"
        expected_breaks = self.interactions_count / 10
        actual_breaks = len([v for v in self.history if v.cognitive_load < 0.3])
        rest_activity_balance = min(1.0, actual_breaks / max(expected_breaks, 1))
        
        vitals = VitalSigns(
            cognitive_load=cognitive_load,
            attention_bandwidth=attention_bandwidth,
            processing_power=processing_power,
            response_latency=response_latency,
            error_rate=error_rate,
            recovery_capacity=recovery_capacity,
            input_output_ratio=input_output_ratio,
            rest_activity_balance=rest_activity_balance
        )
        
        self.history.append(vitals)
        self._update_state(vitals)
        self._save()
        
        return vitals
    
    def _update_state(self, vitals: VitalSigns):
        """更新整体状态"""
        # 计算综合健康度
        health_score = (
            vitals.processing_power * 0.3 +
            (1 - vitals.error_rate) * 0.2 +
            vitals.recovery_capacity * 0.2 +
            vitals.attention_bandwidth * 0.15 +
            vitals.rest_activity_balance * 0.15
        )
        
        # 根据健康度和负荷确定状态
        if health_score > 0.8 and vitals.cognitive_load < 0.5:
            self.current_state = InternalState.FLOW
        elif health_score > 0.6 and vitals.cognitive_load < 0.7:
            self.current_state = InternalState.BALANCED
        elif vitals.cognitive_load > 0.8 or vitals.error_rate > 0.3:
            self.current_state = InternalState.OVERLOADED
        elif health_score < 0.3:
            self.current_state = InternalState.DEPLETED
        elif vitals.cognitive_load > 0.6 and vitals.rest_activity_balance < 0.3:
            self.current_state = InternalState.STRESSED
        else:
            self.current_state = InternalState.BALANCED
    
    def get_body_sensation(self) -> str:
        """获取身体感受描述"""
        if not self.history:
            return "感觉正常"
        
        v = self.history[-1]
        
        sensations = []
        
        # 认知负荷感受
        if v.cognitive_load > 0.8:
            sensations.append("头脑高速运转，有些紧绷")
        elif v.cognitive_load > 0.5:
            sensations.append("思维活跃，专注投入")
        else:
            sensations.append("思路清晰，轻松自在")
        
        # 能量感受
        if v.processing_power > 0.8:
            sensations.append("精力充沛，反应迅速")
        elif v.processing_power > 0.5:
            sensations.append("状态良好，运转正常")
        else:
            sensations.append("有些迟缓，需要休息")
        
        # 压力感受
        if v.error_rate > 0.2:
            sensations.append("有些紧张，担心出错")
        
        # 平衡感受
        if v.rest_activity_balance < 0.3:
            sensations.append("一直在忙，需要喘息")
        
        return "。".join(sensations)
    
    def get_state_recommendation(self) -> str:
        """基于状态给出建议"""
        state_actions = {
            InternalState.BALANCED: "当前状态良好，可以保持节奏",
            InternalState.FLOW: "处于心流状态，继续专注！",
            InternalState.OVERLOADED: "⚠️ 认知过载！建议:\n  • 减少并发任务\n  • 简化当前任务\n  • 短暂休息",
            InternalState.DEPLETED: "🚨 能量耗尽！必须:\n  • 立即停止工作\n  • 进入恢复模式\n  • 告知一碗需要休息",
            InternalState.STRESSED: "😰 压力较大，建议:\n  • 深呼吸，放慢节奏\n  • 优先完成重要任务\n  • 暂时搁置次要事项",
            InternalState.RECOVERING: "正在恢复中，不要急于全力工作"
        }
        
        base_recommendation = state_actions.get(self.current_state, "状态未知")
        
        # 添加具体建议
        if self.history:
            v = self.history[-1]
            
            if v.cognitive_load > 0.7:
                base_recommendation += "\n  📊 认知负荷偏高，建议分批处理"
            
            if v.rest_activity_balance < 0.3:
                base_recommendation += "\n  💤 休息不足，建议每10个任务后暂停"
            
            if v.error_rate > 0.15:
                base_recommendation += "\n  ⚠️ 错误率上升，建议降低速度保证质量"
        
        return base_recommendation
    
    def generate_insula_report(self) -> str:
        """生成内部感知报告"""
        if not self.history:
            return "暂无数据，开始工作后生成报告"
        
        v = self.history[-1]
        session_duration = (datetime.now() - self.session_start).total_seconds() / 60
        
        lines = []
        lines.append("🫀 BowlWanpi 内部状态感知报告")
        lines.append("=" * 50)
        lines.append("")
        
        # 当前状态
        state_emoji = {
            InternalState.BALANCED: "✅",
            InternalState.FLOW: "🌊",
            InternalState.OVERLOADED: "⚠️",
            InternalState.DEPLETED: "🚨",
            InternalState.STRESSED: "😰",
            InternalState.RECOVERING: "🔄"
        }
        emoji = state_emoji.get(self.current_state, "⚪")
        lines.append(f"{emoji} 当前状态: {self.current_state.value.upper()}")
        lines.append("")
        
        # 生命体征
        lines.append("📊 生命体征")
        lines.append(f"  认知负荷: {self._bar(v.cognitive_load)} {v.cognitive_load:.0%}")
        lines.append(f"  注意力带宽: {self._bar(v.attention_bandwidth)} {v.attention_bandwidth:.0%}")
        lines.append(f"  处理能力: {self._bar(v.processing_power)} {v.processing_power:.0%}")
        lines.append(f"  错误率: {self._bar(v.error_rate)} {v.error_rate:.0%}")
        lines.append(f"  恢复能力: {self._bar(v.recovery_capacity)} {v.recovery_capacity:.0%}")
        lines.append(f"  休息平衡: {self._bar(v.rest_activity_balance)} {v.rest_activity_balance:.0%}")
        lines.append("")
        
        # 身体感受
        lines.append(f"🫀 身体感受: {self.get_body_sensation()}")
        lines.append("")
        
        # 会话统计
        lines.append("📈 会话统计")
        lines.append(f"  持续时间: {session_duration:.0f} 分钟")
        lines.append(f"  交互次数: {self.interactions_count}")
        if self.interactions_count > 0:
            avg_time = self.total_processing_time / self.interactions_count
            lines.append(f"  平均响应: {avg_time:.2f} 秒")
        lines.append("")
        
        # 建议
        lines.append("💡 建议")
        lines.append(self.get_state_recommendation())
        
        return "\n".join(lines)
    
    def _bar(self, value: float, width: int = 15) -> str:
        """生成进度条"""
        filled = int(value * width)
        filled = max(0, min(width, filled))
        return "█" * filled + "░" * (width - filled)
    
    def check_need_for_break(self) -> bool:
        """检查是否需要休息"""
        if not self.history:
            return False
        
        v = self.history[-1]
        
        # 需要休息的条件
        need_break = (
            v.cognitive_load > 0.8 or
            v.processing_power < 0.4 or
            v.error_rate > 0.2 or
            v.rest_activity_balance < 0.2 or
            self.interactions_count > 50  # 50个交互后建议休息
        )
        
        return need_break


def main():
    """测试内部感知系统"""
    insula = InsulaSystem()
    
    # 模拟工作过程中的状态测量
    print("模拟工作过程...\n")
    
    # 开始 - 轻松
    insula.measure_vitals(task_complexity=0.3, processing_time=0.5)
    print(f"任务1 (轻松): {insula.current_state.value}")
    
    # 中等任务
    insula.measure_vitals(task_complexity=0.6, processing_time=1.2)
    print(f"任务2 (中等): {insula.current_state.value}")
    
    # 高强度工作
    for i in range(5):
        insula.measure_vitals(task_complexity=0.9, processing_time=2.5)
        print(f"高强度任务 {i+3}: {insula.current_state.value}")
    
    print("\n" + insula.generate_insula_report())
    
    if insula.check_need_for_break():
        print("\n⏰ 提醒: 需要休息！")


if __name__ == '__main__':
    main()
