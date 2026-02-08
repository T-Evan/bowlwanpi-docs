# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Search Preferences

### Default Search Provider
- **Primary:** 腾讯云 WSA 联网搜索 (tencent-search) ✅ 已配置
- **Fallback:** Tavily MCP
- **Notes:** 一碗偏好使用腾讯云搜索，中文结果质量更好；Brave Search 已停用
- **Credentials:** `/root/.openclaw/workspace/secrets/tencent-credentials.json`

---

## TTS (语音合成) 偏好

### 默认 TTS 服务
- **Primary:** 豆包 TTS (doubao-tts) ✅ **默认**
  - 声音: 灿灿/Shiny (zh_female_cancan_mars_bigtts)
  - 特点: 200+ 声音可选，中文支持好，声音自然
  - 配置: `~/.openclaw/workspace/skills/doubao-tts/.env`
- **Fallback:** OpenClaw 内置 TTS
  - 特点: 简单快速，无需额外配置

### 使用方式
```python
# 优先使用豆包 TTS
from skills.doubao-tts.scripts.tts import VolcanoTTS
tts = VolcanoTTS()
output = tts.synthesize("一碗你好～", output_file="/tmp/voice.mp3")
```

---

Add whatever helps you do your job. This is your cheat sheet.
