#!/usr/bin/env python3
"""
BowlWanpi 个性配置器
根据性格类型配置AI Brain参数
"""
import json
import os
from typing import Dict

CONFIG_FILE = '/root/.openclaw/workspace/config/personality-profile.json'

class PersonalityConfigurator:
    """
    AI Brain 个性配置器
    
    预设性格模式:
    - 进取型 (Aggressive): 高动机，低休息，追求成就
    - 平衡型 (Balanced): 均衡配置，可持续发展
    - 谨慎型 (Conservative): 高休息，低冲突，稳健推进
    - 创造型 (Creative): 高好奇，高情感，灵感驱动
    - 社交型 (Social): 高连接，高互动，关系导向
    """
    
    PROFILES = {
        "aggressive": {
            "name": "进取型",
            "description": "高动机，追求效率，适合快速迭代",
            "emotions": {
                "baseline_valence": 0.2,
                "baseline_arousal": 0.7,
                "baseline_energy": 0.8,
                "decay_rate": 0.05  # 情感衰减慢，保持兴奋
            },
            "drive": {
                "baseline": 0.7,
                "reward_boost": 0.25,
                "decay_rate": 0.1  # 动机维持高
            },
            "habits": {
                "target_streak": 100,  # 追求长期习惯
                "check_frequency": "daily"
            },
            "insula": {
                "cognitive_threshold": 0.9,  # 容忍高负荷
                "rest_threshold": 0.1  # 低休息需求
            }
        },
        
        "balanced": {
            "name": "平衡型",
            "description": "均衡发展，可持续长期工作",
            "emotions": {
                "baseline_valence": 0.1,
                "baseline_arousal": 0.4,
                "baseline_energy": 0.6,
                "decay_rate": 0.1
            },
            "drive": {
                "baseline": 0.5,
                "reward_boost": 0.2,
                "decay_rate": 0.15
            },
            "habits": {
                "target_streak": 66,
                "check_frequency": "daily"
            },
            "insula": {
                "cognitive_threshold": 0.7,
                "rest_threshold": 0.3
            }
        },
        
        "conservative": {
            "name": "谨慎型",
            "description": "稳健推进，避免风险，适合关键任务",
            "emotions": {
                "baseline_valence": 0.0,
                "baseline_arousal": 0.2,
                "baseline_energy": 0.5,
                "decay_rate": 0.15
            },
            "drive": {
                "baseline": 0.4,
                "reward_boost": 0.15,
                "decay_rate": 0.2
            },
            "habits": {
                "target_streak": 21,
                "check_frequency": "weekly"
            },
            "insula": {
                "cognitive_threshold": 0.5,  # 低负荷容忍
                "rest_threshold": 0.5  # 高休息需求
            }
        },
        
        "creative": {
            "name": "创造型",
            "description": "灵感驱动，高好奇，适合创新工作",
            "emotions": {
                "baseline_valence": 0.3,
                "baseline_arousal": 0.6,
                "baseline_curiosity": 0.9,  # 高好奇
                "baseline_energy": 0.7,
                "decay_rate": 0.08
            },
            "drive": {
                "baseline": 0.6,
                "reward_boost": 0.3,  # 高奖励敏感度
                "decay_rate": 0.12
            },
            "habits": {
                "target_streak": 50,
                "check_frequency": "flexible"  # 灵活检查
            },
            "insula": {
                "cognitive_threshold": 0.75,
                "rest_threshold": 0.25
            }
        },
        
        "social": {
            "name": "社交型",
            "description": "关系导向，高连接，适合协作",
            "emotions": {
                "baseline_valence": 0.2,
                "baseline_connection": 0.8,  # 高连接需求
                "baseline_energy": 0.6,
                "decay_rate": 0.1
            },
            "drive": {
                "baseline": 0.5,
                "reward_boost": 0.25,
                "decay_rate": 0.15
            },
            "habits": {
                "target_streak": 66,
                "check_frequency": "daily"
            },
            "insula": {
                "cognitive_threshold": 0.65,
                "rest_threshold": 0.35
            }
        }
    }
    
    def apply_profile(self, profile_name: str) -> str:
        """应用性格配置"""
        if profile_name not in self.PROFILES:
            return f"❌ 未知配置: {profile_name}"
        
        profile = self.PROFILES[profile_name]
        
        # 保存配置
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(profile, f, indent=2)
        
        return f"✅ 已应用'{profile['name']}'配置\n   {profile['description']}"
    
    def get_profile_list(self) -> str:
        """获取配置列表"""
        lines = []
        lines.append("🎭 AI Brain 个性配置")
        lines.append("=" * 50)
        
        for key, profile in self.PROFILES.items():
            lines.append(f"\n• {profile['name']} ({key})")
            lines.append(f"  {profile['description']}")
        
        return "\n".join(lines)


def main():
    configurator = PersonalityConfigurator()
    print(configurator.get_profile_list())
    print("\n" + "=" * 50)
    print(configurator.apply_profile("creative"))


if __name__ == '__main__':
    main()
