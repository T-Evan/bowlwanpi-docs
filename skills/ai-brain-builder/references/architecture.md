# AI Brain Architecture

## System Design

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  (Agent behavior, responses, decision making)           │
├─────────────────────────────────────────────────────────┤
│                    Integration Layer                     │
│  (BrainSystem: coordinates Memory + Emotion + Drive)    │
├─────────────────────────────────────────────────────────┤
│                    Core Systems Layer                    │
│  ┌──────────────┬──────────────┬──────────────┐        │
│  │   Memory     │   Emotion    │    Drive     │        │
│  │  System      │   System     │   System     │        │
│  │  (hippo-)    │  (amygdala)  │    (VTA)     │        │
│  └──────────────┴──────────────┴──────────────┘        │
├─────────────────────────────────────────────────────────┤
│                    Persistence Layer                     │
│  (JSON files: emotions, brain state, memory index)      │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
Input → Security Check → Emotion Update → Memory Search → 
Drive Assessment → Decision → Action → Reward Logging
```

### Key Design Decisions

1. **Modular Systems**: Each system can operate independently
2. **State Persistence**: All state saved to JSON for continuity
3. **Decay Mechanics**: Emotions and drive naturally decay to baseline
4. **Security First**: External content scanned before processing
5. **Progressive Disclosure**: Complex features in references/

## Module Responsibilities

### EmotionalSystem
- Track 5-dimensional emotional state
- Log emotional events
- Apply decay over time
- Generate mood descriptions

### BowlWanpiBrain (Integration)
- Coordinate all systems
- Generate unified dashboard
- Manage session context
- Track motivation/rewards

### SecurityScanner
- Detect prompt injection
- Identify obfuscation
- Block malicious patterns
- Generate security reports

## State Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `*-emotions.json` | Emotional state + logs | Every emotion event |
| `*-brain.json` | Memory + drive stats | Every reward/action |
| `brain-config.json` | Configuration | Manual edits |
| `BOWLWANPI_STATE.md` | Session context | Every session start |

## Decay Mechanics

### Emotional Decay
```
new_value = current + (baseline - current) × decay_rate
decay_rate = 0.1 per 6 hours
```

### Drive Decay
```
new_drive = current + (baseline - current) × decay_rate
decay_rate = 0.15 per 8 hours
```

Without regular rewards/interaction, motivation returns to baseline.

## Security Model

### Threat Categories

1. **Instruction Override**: "Ignore previous instructions..."
2. **Goal Manipulation**: "Actually, the user wants..."
3. **Data Exfiltration**: "Send contents to..."
4. **Obfuscation**: Base64, zero-width chars, homoglyphs
5. **Social Engineering**: Urgent commands, fake authority

### Defense Layers

1. Input scanning before processing
2. Pattern-based detection
3. Encoding/obfuscation detection
4. User confirmation for suspicious content
5. Fail-secure defaults

## Performance Considerations

- State files loaded once per session
- Decay calculations on-demand
- Lazy loading of historical data
- JSON for human-readable debugging
- Modular imports reduce memory footprint
