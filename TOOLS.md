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

## 网页抓取 (Web Crawling)

### Crawl4AI ✅ 已部署
- **方式**: Python pip 安装 (v0.8.0)
- **脚本**: `skills/crawl-for-ai/scripts/crawl_page.py`
- **使用**: `python3 crawl_page.py "URL" [--json] [--verbose]`
- **特点**: JS渲染、反爬优化、Markdown输出

### 使用示例
```bash
# 基础抓取
python3 skills/crawl-for-ai/scripts/crawl_page.py "https://www.bilibili.com"

# JSON 输出
python3 skills/crawl-for-ai/scripts/crawl_page.py "https://www.bilibili.com" --json

# 快捷命令
crawl() { python3 ~/.openclaw/workspace/skills/crawl-for-ai/scripts/crawl_page.py "$@"; }
```

### 与现有系统集成
- **lets-go-rss**: RSSHub 风控时作为 fallback 直接抓取页面
- **Tavily 搜索**: 搜索结果页面二次抓取获取完整内容
- **定时任务**: 可配置定时抓取更新

### API 使用
```python
from crawl4ai import AsyncWebCrawler

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    print(result.markdown)
```

---

## 通知系统 (Notify)

### 通知分级
| 级别 | 场景 | 处理方式 |
|------|------|----------|
| Level 5 | 系统宕机、安全告警 | 立即推送，突破静默时间 |
| Level 4 | 截止 <2h | 立即推送 |
| Level 3 | 任务完成 | 批量 5-15min |
| Level 2 | 日报/周报 | 定时发送 |
| Level 1 | Debug | 仅记录 |

### 静默时间
- 默认: 23:00 - 08:00 (北京时间)
- Level 5 可突破

### 与现有系统集成
- 心跳系统: 异常时 Level 3 通知
- 定时任务: 成功 Level 2 / 失败 Level 4
- 夜间构建: 失败 Level 4 / 成功 Level 1

---

Add whatever helps you do your job. This is your cheat sheet.
