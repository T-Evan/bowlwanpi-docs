# Personal Analytics

**Know thyself. Work smarter. Discover patterns you didn't know existed.**

Personal Analytics analyzes your conversation patterns to surface actionable insights about your work style, interests, and productivity—all while keeping your data completely private and local.

## Features

- ⏰ **Time Pattern Analysis** - When you chat, for how long, productivity peaks
- 📚 **Topic Tracking** - What you discuss most, emerging interests
- 😊 **Sentiment Monitoring** - Mood trends, stress indicators
- 💡 **Productivity Insights** - Task completion, optimal work times
- 📊 **Beautiful Reports** - Weekly/monthly summaries
- 🔗 **Proactive Research Integration** - Auto-suggest monitoring topics
- 🔒 **Privacy First** - All local, no external data, opt-in design

## Quick Start

```bash
# 1. Setup
cp config.example.json config.json

# 2. Enable tracking
python3 scripts/enable.py

# 3. Analyze (after some sessions)
python3 scripts/analyze.py --insights

# 4. Generate weekly report
python3 scripts/report.py weekly

# 5. Get topic recommendations
python3 scripts/recommend.py --explain
```

## Privacy Guarantee

🔒 **Your data never leaves your machine.**

- Raw conversations NOT stored
- Only aggregated statistics saved
- All analysis happens locally
- No external APIs for analysis
- Data files are gitignored
- Delete anytime with one command

## What Gets Tracked

### ✅ Tracked (Aggregated Only)
- Session timestamps and duration
- Topic frequencies
- Sentiment distribution
- Productivity markers
- Time-of-day patterns

### ❌ NOT Tracked
- Raw message content
- Personal information
- Sensitive data (passwords, keys)
- Specific conversation details

## Use Cases

### 📈 Optimize Your Schedule
Discover when you're most productive and schedule deep work accordingly.

### 🎯 Focus on What Matters
Identify topics you're spending time on and decide if they align with your goals.

### 😊 Track Well-being
Monitor stress indicators, late-night work, and mood trends.

### 💡 Discover Hidden Interests
Surface emerging topics you didn't realize you cared about.

## Commands

### Enable/Disable

```bash
# Enable tracking
python3 scripts/enable.py

# Disable tracking
python3 scripts/disable.py

# Check status
python3 scripts/status.py
```

### Analyze

```bash
# Analyze all data
python3 scripts/analyze.py

# Analyze date range
python3 scripts/analyze.py --since "2026-01-01" --until "2026-01-31"

# With insights
python3 scripts/analyze.py --insights

# JSON output
python3 scripts/analyze.py --json
```

### Reports

```bash
# Weekly report
python3 scripts/report.py weekly

# Monthly report
python3 scripts/report.py monthly

# Custom range
python3 scripts/report.py custom --since "2026-01-01" --until "2026-01-31"

# Save to file
python3 scripts/report.py weekly --output report.md

# Send via Telegram
python3 scripts/report.py weekly --send
```

### Recommendations

```bash
# Get topic recommendations
python3 scripts/recommend.py

# With explanations
python3 scripts/recommend.py --explain

# Set threshold (min mentions)
python3 scripts/recommend.py --threshold 5

# Auto-add to proactive-research
python3 scripts/recommend.py --auto-add
```

## License

MIT

## Credits

Built for ClawdHub by the Moltmates team. Privacy-first design inspired by Quantified Self movement.
