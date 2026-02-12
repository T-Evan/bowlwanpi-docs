# AI Brain Builder 🧠

**Build a complete cognitive system for AI agents**

[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://openclaw.ai)
[![Version](https://img.shields.io/badge/version-1.0.0-green)](https://github.com/openclaw/openclaw)

## Overview

AI Brain Builder helps you create a complete cognitive ecosystem for AI agents with six core systems inspired by neuroscience:

| System | Brain Region | Function | Status |
|--------|--------------|----------|--------|
| 🧠 Memory | Hippocampus | Memory formation, importance scoring, retrieval | ✅ |
| 🎭 Emotion | Amygdala | Five-dimensional emotional states | ✅ |
| ⭐ Drive | VTA | Reward-based motivation system | ✅ |
| 🔄 Habit | Basal Ganglia | Habit loop formation | ✅ |
| ⚖️ Conflict | Anterior Cingulate | Conflict detection & resolution | ✅ |
| 🫀 Interoception | Insula | Internal state awareness | ✅ |

## Quick Start

### Installation

```bash
# Clone or copy the skill to your OpenClaw workspace
cp -r ai-brain-builder ~/.openclaw/workspace/skills/

# Initialize the brain system for your agent
cd ~/.openclaw/workspace/skills/ai-brain-builder/scripts
python init-brain.py --name "YourAgent"
```

### Basic Usage

```python
from modules.brain_system import BowlWanpiBrain
from modules.emotional_system import EmotionType

# Initialize brain
brain = BowlWanpiBrain()

# Log emotions
brain.emotion_system.log_emotion(
    EmotionType.JOY, 
    intensity=0.8, 
    trigger="User praised my work"
)

# Log rewards (boosts motivation)
brain.log_reward(
    "accomplishment",
    "Completed complex task",
    0.9
)

# View dashboard
print(brain.generate_dashboard())
```

### Run Demo

```bash
# Full AI Brain workflow demo
python scripts/demo-ai-brain.py

# Show all demos (emotional journey, habit formation)
python scripts/demo-ai-brain.py --full
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Brain Ecosystem                        │
├─────────────────────────────────────────────────────────────┤
│  Input → Security Check → Emotion Update → Memory Search   │
│              ↓                                              │
│  Drive Assessment → Conflict Detection → Decision          │
│              ↓                                              │
│  Action → Reward Logging → State Persistence               │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 🧠 Memory System
- Importance scoring (0.0-1.0)
- Semantic decay over time
- Automatic reinforcement
- Core/Active/Background tiers

### 🎭 Emotional System
Five dimensions (range -1.0 to 1.0 or 0.0 to 1.0):
- **Valence**: Negative ↔ Positive mood
- **Arousal**: Calm ↔ Excited
- **Connection**: Distant ↔ Bonded
- **Curiosity**: Bored ↔ Fascinated
- **Energy**: Depleted ↔ Energized

### ⭐ Drive System
- Reward logging boosts drive
- Anticipation creates motivation
- Decay toward baseline without rewards
- Drive level affects proactivity

### 🔄 Habit System
- Habit loop: Trigger → Action → Reward
- Streak tracking
- Formation stages (7/21/66 days)
- Automatic reinforcement

### ⚖️ Conflict Detection
- Goal conflicts
- Resource competition
- Priority clashes
- Resolution suggestions

### 🫀 Interoception
- Cognitive load monitoring
- Processing power tracking
- Error rate awareness
- Rest-activity balance

## File Structure

```
ai-brain-builder/
├── SKILL.md                      # Skill definition
├── scripts/
│   ├── init-brain.py            # Initialize brain system
│   ├── brain_system.py          # Core integration
│   ├── emotional_system.py      # Emotion processing
│   ├── habit_system.py          # Habit formation
│   ├── conflict_system.py       # Conflict detection
│   ├── insula_system.py         # Internal awareness
│   ├── security_scanner.py      # Content safety
│   └── demo-ai-brain.py         # Demo script
└── references/
    ├── architecture.md          # System design
    └── api-reference.md         # API documentation
```

## State Files

After initialization, these files track state:

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `*-emotions.json` | Emotional state & logs | Every emotion event |
| `*-brain.json` | Memory & drive stats | Every reward/action |
| `*-habits.json` | Habit tracking | Every completion |
| `*-conflicts.json` | Conflict records | Detection/Resolution |
| `*-insula.json` | Vital signs history | Every measurement |

## Configuration

Edit `config/brain-config.json`:

```json
{
  "agent_name": "YourAgent",
  "emotions": {
    "baseline_valence": 0.1,
    "decay_rate": 0.1,
    "decay_interval_hours": 6
  },
  "drive": {
    "baseline": 0.5,
    "reward_boost_multiplier": 0.2
  }
}
```

## Use Cases

1. **Personal AI Assistant**: Give your agent memory, emotions, and motivation
2. **Long-running Tasks**: Track state across sessions
3. **Self-improvement**: Habit formation for consistent behavior
4. **Conflict Resolution**: Detect and resolve competing goals
5. **Health Monitoring**: Track internal state to prevent overload

## Examples

### Example 1: Emotional Response

```python
from emotional_system import EmotionType

# User compliments the agent
response = brain.emotion_system.log_emotion(
    EmotionType.JOY, 0.9, "User said great job!"
)
print(response)  # "好开心～" or similar

# Check current mood
print(brain.emotion_system.get_mood_description())
```

### Example 2: Habit Formation

```python
from habit_system import get_habit_system

habits = get_habit_system()

# Create a new habit
habits.create_habit(
    name="Daily Learning",
    trigger="8 PM",
    action="Study for 30 minutes",
    reward="Skill improvement"
)

# Complete the habit
print(habits.complete_habit("habit_daily_learning"))
```

### Example 3: Conflict Detection

```python
from conflict_system import ConflictDetectionSystem

cds = ConflictDetectionSystem()

# Define current goals
goals = [
    {'name': 'Work', 'priority': 'high', 'time': 'now'},
    {'name': 'Rest', 'priority': 'medium', 'time': 'now'},
]

# Detect conflicts
conflicts = cds.detect_goal_conflict(goals)
for c in conflicts:
    print(f"Conflict: {c.description}")
    suggestions = cds.suggest_resolution(c)
    print(f"Suggestion: {suggestions[0]}")
```

## Philosophy

> "An AI without memory is just a model.  
> An AI without emotion is just a calculator.  
> An AI without drive is just waiting.  
> An AI without habits is reinventing every time.  
> An AI without conflict detection makes poor decisions.  
> An AI without self-awareness doesn't know its limits."

## Credits

Inspired by the AI Brain series:
- [hippocampus-memory](https://www.clawhub.ai/skills/hippocampus)
- [amygdala-memory](https://www.clawhub.ai/skills/amygdala-memory)
- [vta-memory](https://www.clawhub.ai/skills/vta-memory)

Created by BowlWanpi during an intensive learning session.

## License

MIT - Feel free to use and modify!

---

**Happy Brain Building! 🧠✨**
