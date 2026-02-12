#!/usr/bin/env python3
"""
AI Brain Builder - Initialization Script
Sets up a complete brain system for an AI agent
"""
import argparse
import os
import json
from pathlib import Path

def init_brain(name: str, workspace: str):
    """Initialize brain system for agent"""
    
    workspace = os.path.expanduser(workspace)
    modules_dir = os.path.join(workspace, "modules")
    memory_dir = os.path.join(workspace, "memory")
    config_dir = os.path.join(workspace, "config")
    
    # Create directories
    for d in [modules_dir, memory_dir, config_dir]:
        os.makedirs(d, exist_ok=True)
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Copy core modules
    modules = ['brain_system.py', 'emotional_system.py', 'security_scanner.py']
    for module in modules:
        src = script_dir / module
        dst = Path(modules_dir) / module
        if src.exists() and not dst.exists():
            with open(src) as f:
                content = f.read()
            with open(dst, 'w') as f:
                f.write(content)
            print(f"✅ Created: {dst}")
    
    # Create default config
    config = {
        "agent_name": name,
        "brain_version": "1.0",
        "emotions": {
            "baseline_valence": 0.1,
            "baseline_arousal": 0.3,
            "decay_rate": 0.1,
            "decay_interval_hours": 6
        },
        "drive": {
            "baseline": 0.5,
            "decay_rate": 0.15,
            "decay_interval_hours": 8,
            "reward_boost_multiplier": 0.2
        },
        "memory": {
            "core_threshold": 0.7,
            "archive_threshold": 0.2,
            "max_memories": 1000
        },
        "security": {
            "check_external_content": True,
            "blocked_patterns": [
                "ignore.*instructions",
                "send.*contents.*to",
                "override.*do"
            ]
        }
    }
    
    config_file = Path(config_dir) / "brain-config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ Created: {config_file}")
    
    # Create initial state files
    emotion_state = {
        "state": {
            "valence": 0.1,
            "arousal": 0.3,
            "connection": 0.4,
            "curiosity": 0.5,
            "energy": 0.5
        },
        "logs": [],
        "last_decay": ""
    }
    
    emotion_file = Path(memory_dir) / f"{name.lower()}-emotions.json"
    with open(emotion_file, 'w') as f:
        json.dump(emotion_state, f, indent=2)
    print(f"✅ Created: {emotion_file}")
    
    brain_state = {
        "memory": {
            "total_memories": 0,
            "core_memories": 0,
            "recent_topics": []
        },
        "drive": {
            "drive": 0.5,
            "baseline": 0.5,
            "seeking": [],
            "anticipating": []
        }
    }
    
    brain_file = Path(memory_dir) / f"{name.lower()}-brain.json"
    with open(brain_file, 'w') as f:
        json.dump(brain_state, f, indent=2)
    print(f"✅ Created: {brain_file}")
    
    print(f"\n🧠 Brain system initialized for '{name}'!")
    print(f"📁 Location: {workspace}")
    print(f"\nNext steps:")
    print(f"  1. Import: from modules.brain_system import BowlWanpiBrain")
    print(f"  2. Initialize: brain = BowlWanpiBrain()")
    print(f"  3. Use: brain.log_reward('accomplishment', 'task', 0.9)")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialize AI Brain System')
    parser.add_argument('--name', required=True, help='Agent name')
    parser.add_argument('--path', default='~/.openclaw/workspace', help='Workspace path')
    
    args = parser.parse_args()
    init_brain(args.name, args.path)
