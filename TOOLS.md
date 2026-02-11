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
- **Primary:** Tavily AI Search ✅ 已配置
  - API Key: `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`
  - 配置路径: `skills/intelligent-search/.env`
  - 特点: 引用详细、支持中英文
- **Fallback:** 腾讯云 WSA (国内快速)
- **Notes:** Tavily 是主要搜索工具，腾讯云作为中文查询备用
- **Credentials:** 
  - Tavily: `skills/intelligent-search/.env`
  - 腾讯云: `/root/.openclaw/workspace/secrets/tencent-credentials.json`

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
