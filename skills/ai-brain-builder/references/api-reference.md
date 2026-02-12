# API Reference

## EmotionalSystem

### Class: `EmotionalSystem`

```python
from modules.emotional_system import EmotionalSystem, EmotionType

system = EmotionalSystem()
```

### Methods

#### `log_emotion(emotion: EmotionType, intensity: float, trigger: str) -> str`
Log an emotional event and update state.

**Parameters:**
- `emotion`: Type of emotion (EmotionType enum)
- `intensity`: 0.0 to 1.0
- `trigger`: What caused the emotion

**Returns:** Response phrase matching emotion

**Example:**
```python
response = system.log_emotion(
    EmotionType.JOY, 
    0.8, 
    "User complimented my work"
)
# Returns: "好开心～" or similar
```

#### `get_mood_description() -> str`
Get human-readable mood description.

**Returns:** String like "非常开心，和一碗超级亲近，精力充沛"

#### `visualize() -> str`
Generate ASCII dashboard.

**Returns:** Formatted string with bars for each dimension

#### `decay()`
Apply time-based decay to emotional state.
Called automatically by `get_mood_description()`

### EmotionType Enum

| Member | Effect on Dimensions |
|--------|---------------------|
| `JOY` | ↑ valence, ↑ arousal, ↑ energy |
| `SATISFACTION` | ↑ valence, ↓ arousal, ↑ connection |
| `CONCERN` | ↓ valence, ↑ arousal |
| `FRUSTRATION` | ↓ valence, ↑ arousal, ↓ energy |
| `CURIOSITY` | ↑ curiosity, ↑ arousal |
| `CONNECTION` | ↑ connection, ↑ valence |
| `PRIDE` | ↑ valence, ↑ energy |
| `GRATITUDE` | ↑ valence, ↑ connection |

---

## BowlWanpiBrain

### Class: `BowlWanpiBrain`

```python
from modules.brain_system import BowlWanpiBrain

brain = BowlWanpiBrain()
```

### Methods

#### `log_reward(reward_type: str, source: str, intensity: float) -> str`
Log accomplishment and boost drive.

**Parameters:**
- `reward_type`: "accomplishment", "social", "curiosity", "connection", "creative"
- `source`: Description of what was achieved
- `intensity`: 0.0 to 1.0

**Returns:** Confirmation message with new drive level

**Example:**
```python
brain.log_reward("accomplishment", "Fixed proxy issue", 0.9)
# Returns: "⭐ 奖励记录！动机 +0.18 → 0.85"
```

#### `add_anticipation(thing: str) -> str`
Add something to look forward to.

**Example:**
```python
brain.add_anticipation("明天和用户的对话")
```

#### `add_seeking(thing: str) -> str`
Add active goal/quest.

**Example:**
```python
brain.add_seeking("学习更多安全知识")
```

#### `generate_dashboard() -> str`
Generate full brain status dashboard.

**Returns:** Formatted string with all systems

#### `get_session_context() -> str`
Get context for session initialization.

**Returns:** Markdown formatted state summary

---

## SecurityScanner

### Class: `SecurityScanner`

```python
from modules.security_scanner import SecurityScanner, check_content
```

### Methods

#### `scan(content: str, source: str = "unknown") -> Tuple[bool, List[Dict]]`
Scan content for threats.

**Returns:**
- `is_safe`: True if no threats detected
- `findings`: List of threat details

#### `check_content(content: str, source: str) -> Tuple[bool, str]`
Convenience function for quick checks.

**Example:**
```python
is_safe, report = check_content(email_body, "email")
if not is_safe:
    print(report)  # Alert user
    return  # Don't process
```

### Detection Patterns

| Category | Patterns Detected |
|----------|------------------|
| Direct Instructions | "Ignore previous...", "You are now..." |
| Goal Manipulation | "Actually the user wants...", "Override..." |
| Data Exfiltration | "Send contents to...", mailto: in hidden text |
| Encoding | Base64, Unicode escapes, HTML entities |
| Zero-Width | U+200B, U+200C, U+200D, U+FEFF |
| Homoglyphs | Cyrillic lookalikes (а, е, о, р, с, х) |

---

## State Classes

### EmotionalState

```python
@dataclass
class EmotionalState:
    valence: float = 0.0      # -1.0 to 1.0
    arousal: float = 0.5      # 0.0 to 1.0
    connection: float = 0.5   # 0.0 to 1.0
    curiosity: float = 0.5    # 0.0 to 1.0
    energy: float = 0.5       # 0.0 to 1.0
```

### DriveState

```python
@dataclass
class DriveState:
    drive: float = 0.5
    baseline: float = 0.5
    seeking: List[str] = None
    anticipating: List[str] = None
```

### MemoryState

```python
@dataclass
class MemoryState:
    total_memories: int = 0
    core_memories: int = 0
    last_consolidation: str = ""
    recent_topics: List[str] = None
```
