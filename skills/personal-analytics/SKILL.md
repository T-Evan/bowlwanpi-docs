---
name: personal-analytics
description: Analyze conversation patterns, track productivity, and surface self-knowledge insights. Use when user wants to understand their own patterns (when they chat, what topics they discuss, productivity trends, sentiment over time). Provides weekly/monthly reports, topic recommendations, and time-based insights. Privacy-first design with all analysis local.
---

# Personal Analytics

**Know thyself. Work smarter. Discover patterns you didn't know existed.**

Personal Analytics analyzes your conversation patterns to surface actionable insights about your work style, interests, and productivity—all while keeping your data completely private and local.

## Core Capabilities

1. **Session Analysis** - When you chat, for how long, productivity patterns
2. **Topic Tracking** - What subjects come up repeatedly, trending interests
3. **Sentiment Patterns** - Mood tracking over time, stress indicators
4. **Productivity Insights** - When you're most effective, optimal work times
5. **Weekly/Monthly Reports** - Beautiful summaries of your patterns
6. **Topic Recommendations** - Auto-suggest topics for proactive-research monitoring

## Privacy First

🔒 **All analysis happens locally. Nothing leaves your machine.**

- Raw conversations **never** stored
- Only aggregated statistics saved
- Opt-in design (must enable)
- Data deletion anytime
- No external APIs for analysis
- Gitignored data files

## Quick Start

```bash
# Initialize
cp config.example.json config.json

# Enable tracking
python3 scripts/enable.py

# Analyze current sessions
python3 scripts/analyze.py

# Generate report
python3 scripts/report.py weekly

# Get topic recommendations
python3 scripts/recommend.py
```

## What Gets Tracked

### Session Metadata
- Timestamp (start/end)
- Duration
- Message count
- Primary topics discussed
- Sentiment (positive/neutral/negative/mixed)
- Productivity markers (tasks completed, decisions made)

### Aggregated Stats
- Hourly activity heatmap
- Topic frequency over time
- Average session duration
- Productivity by time of day
- Sentiment trends

### What's NOT Tracked
- ❌ Raw message content
- ❌ Personal information
- ❌ Sensitive data (passwords, keys, etc.)
- ❌ Specific conversations

## Configuration

### config.json

```json
{
  "enabled": true,
  "tracking": {
    "sessions": true,
    "topics": true,
    "sentiment": true,
    "productivity": true
  },
  "privacy": {
    "min_aggregation_window_hours": 24,
    "auto_delete_after_days": 90,
    "exclude_patterns": ["password", "secret", "token", "key"]
  },
  "insights": {
    "productivity_markers": [
      "completed", "shipped", "fixed", "merged", "deployed"
    ],
    "stress_indicators": [
      "urgent", "asap", "critical", "broken", "emergency"
    ]
  },
  "reports": {
    "weekly_day": "sunday",
    "weekly_time": "20:00",
    "auto_send": false
  },
  "integrations": {
    "proactive_research": {
      "auto_suggest_topics": true,
      "suggestion_threshold": 3
    }
  }
}
```

## Scripts

### analyze.py

Analyze conversation patterns:

```bash
# Analyze all available data
python3 scripts/analyze.py

# Analyze specific time range
python3 scripts/analyze.py --since "2026-01-01" --until "2026-01-31"

# Analyze and show insights
python3 scripts/analyze.py --insights

# Verbose output
python3 scripts/analyze.py --verbose
```

**Output:**
```
📊 Personal Analytics Analysis

Period: Jan 1 - Jan 28, 2026 (28 days)

Session Summary:
  Total sessions: 145
  Total time: 18h 32m
  Avg session: 7m 40s
  Most active: Tuesday 10:00-11:00

Topics (Top 10):
  1. Python (32 sessions)
  2. FM26 (28 sessions)
  3. Dirac Live (15 sessions)
  4. ETH/crypto (12 sessions)
  5. Docker (11 sessions)
  ...

Productivity:
  High productivity: 09:00-12:00, 14:00-16:00
  Low productivity: Late night (after 22:00)
  Peak day: Wednesday
  
Sentiment:
  Positive: 62%
  Neutral: 28%
  Negative: 8%
  Mixed: 2%
```

### report.py

Generate beautiful reports:

```bash
# Weekly report
python3 scripts/report.py weekly

# Monthly report
python3 scripts/report.py monthly

# Custom range
python3 scripts/report.py custom --since "2026-01-01" --until "2026-01-31"

# Export to file
python3 scripts/report.py weekly --output report.md

# Send via Telegram
python3 scripts/report.py weekly --send
```

### recommend.py

Get topic recommendations for proactive-research:

```bash
# Get recommendations
python3 scripts/recommend.py

# Show reasoning
python3 scripts/recommend.py --explain

# Auto-add to proactive-research
python3 scripts/recommend.py --auto-add

# Set threshold (minimum mentions)
python3 scripts/recommend.py --threshold 5
```

### enable.py / disable.py

Manage tracking:

```bash
# Enable tracking
python3 scripts/enable.py

# Disable tracking
python3 scripts/disable.py

# Show status
python3 scripts/status.py
```

## Privacy Controls

### Exclusion Patterns

Automatically exclude sensitive data:

```json
{
  "privacy": {
    "exclude_patterns": [
      "password", "token", "key", "secret",
      "credit card", "ssn", "api key"
    ]
  }
}
```

### Manual Deletion

```bash
# Delete all data
rm .analytics_data.json .topic_cache.json
```

## Credits

Built for ClawdHub. Privacy-first design inspired by Quantified Self movement.
