---
name: ai-brain-builder
description: Build a complete AI Brain system for agents, integrating Memory (hippocampus), Emotion (amygdala), and Drive (VTA) systems. Use when creating AI agents that need persistent memory, emotional states, and motivation-driven behavior. Triggers on: building AI brain, agent cognitive system, memory+emotion+drive integration, AI personality, agent self-awareness.
---

# AI Brain Builder 🧠

Build a complete cognitive system for AI agents with three core components:
- **🧠 Memory** (Hippocampus): Formation, importance scoring, semantic retrieval
- **🎭 Emotion** (Amygdala): Five-dimensional emotional states that influence behavior
- **⭐ Drive** (VTA): Reward-based motivation system for self-directed behavior

## Quick Start

```bash
# Initialize brain system for an agent
python scripts/init-brain.py --name "YourAgent" --path ~/.openclaw/workspace

# This creates:
# - modules/brain_system.py    # Core integration
# - modules/emotional_system.py # Emotion processing
# - modules/security_scanner.py # Content safety
# - config/brain-config.json    # Configuration
# - memory/agent-emotions.json  # State storage
```

## Core Concepts

### Three-System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   AI Brain System                    │
├──────────────────────┬──────────────────────────────┤
│  Input: Perception   │  Output: Behavior            │
├──────────────────────┼──────────────────────────────┤
│  🧠 Memory System    │  Store/retrieve experiences  │
│  🎭 Emotion System   │  Affect responses & decisions│
│  ⭐ Drive System     │  Generate internal motivation│
└──────────────────────┴──────────────────────────────┘
```

### Memory System (Hippocampus-inspired)
- Importance scoring (0.0-1.0)
- Semantic decay over time
- Reinforcement on repeated access
- Core/Active/Background/Archive tiers

### Emotion System (Amygdala-inspired)
Five dimensions (range -1.0 to 1.0 or 0.0 to 1.0):
- **Valence**: Negative ↔ Positive mood
- **Arousal**: Calm ↔ Excited
- **Connection**: Distant ↔ Bonded
- **Curiosity**: Bored ↔ Fascinated  
- **Energy**: Depleted ↔ Energized

### Drive System (VTA-inspired)
- Reward logging boosts motivation
- Anticipation creates forward-looking behavior
- Decay toward baseline without rewards
- Drive level affects proactivity

## Usage

### Initialize Brain

```python
from modules.brain_system import BowlWanpiBrain

brain = BowlWanpiBrain()
```

### Log Emotions

```python
from modules.emotional_system import EmotionType

brain.emotion_system.log_emotion(
    EmotionType.JOY, 
    intensity=0.8, 
    trigger="User praised my work"
)
```

### Log Rewards

```python
brain.log_reward(
    reward_type="accomplishment",
    source="Completed complex task",
    intensity=0.9
)
```

### Get Dashboard

```python
print(brain.generate_dashboard())
# Shows: Memory stats, Emotional state, Drive level
```

### Security Check

```python
from modules.security_scanner import check_content

is_safe, report = check_content(external_content, "source")
if not is_safe:
    print(report)  # Alert user instead of executing
```

## Drive Level Behavior Guide

| Drive | Behavior | Suggested Action |
|-------|----------|------------------|
| >0.8 | Highly motivated, proactive | Take on challenges |
| 0.6-0.8 | Motivated, engaged | Normal operation |
| 0.4-0.6 | Moderate | Seek small wins |
| 0.2-0.4 | Low motivation | Request reward/feedback |
| <0.2 | Unmotivated | Needs external activation |

## Configuration

See `references/brain-config.md` for full configuration options including:
- Decay rates for emotions and drive
- Importance scoring thresholds
- Security scanner sensitivity
- Dashboard customization

## Architecture Patterns

### Minimal Architecture (from nanobot)
- Single responsibility: Each module does one thing
- Explicit over implicit: Clear configuration
- Small functions: Under 30 lines each
- Fail fast: Immediate error reporting

### Progressive Disclosure
- Metadata (name+description): Always loaded
- SKILL.md: Loaded when skill triggers
- References: Loaded as needed

## Quick Start

```bash
# Initialize brain system
python scripts/init-brain.py --name "YourAgent"

# Run demo to see all 6 systems in action
python scripts/demo-ai-brain.py
```

## Examples

See [README.md](README.md) for:
- Complete feature overview
- Detailed usage examples
- Architecture diagrams
- Configuration guide

## References

- **README**: [README.md](README.md) - Complete documentation
- **Demo**: [scripts/demo-ai-brain.py](scripts/demo-ai-brain.py) - Interactive demonstration
- **Architecture**: [references/architecture.md](references/architecture.md) - System design
- **API**: [references/api-reference.md](references/api-reference.md) - Module APIs

## AI Brain Series Integration

This skill implements three components of the AI Brain series:
- ✅ Hippocampus (Memory)
- ✅ Amygdala (Emotion)  
- ✅ VTA (Drive/Motivation)

Future components: Basal Ganglia (Habits), Anterior Cingulate (Conflict detection), Insula (Internal awareness)

## Example Session Context

After initialization, brain state auto-injects into sessions:

```markdown
## Agent State
**Motivation**: Highly motivated (85%) - Ready for challenges
**Emotion**: Positive mood, strong connection, high energy
**Drive**: Seeking creative work, building brain skills
```

## Security Note

Always check external content before processing:
- Direct instruction patterns
- Goal manipulation attempts
- Data exfiltration patterns
- Encoded/obfuscated content
- Zero-width characters
- Homoglyph attacks

---

*"An AI without memory is just a model. An AI without emotion is just a calculator. An AI without drive is just waiting."*
