# Whisper STT Skill

本地语音转文字技能，基于 OpenAI Whisper (faster-whisper 实现)

## 安装

```bash
# 安装依赖
pip install faster-whisper

# 安装 ffmpeg（用于音频格式转换）
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg
```

## 使用方法

### 基础转录

```bash
# 使用默认模型 (base) 和中文识别
python3 scripts/transcribe.py /path/to/audio.ogg

# 指定模型和语言
python3 scripts/transcribe.py /path/to/audio.mp3 --model small --language en

# 保存结果到文件
python3 scripts/transcribe.py /path/to/audio.wav -o output.txt

# 输出 JSON 格式（带时间戳）
python3 scripts/transcribe.py /path/to/audio.opus -o output.json --json
```

### 支持的音频格式

- WAV, MP3, M4A, FLAC, OGG, OPUS, WebM

### 模型选择

| 模型 | 大小 | 速度 | 准确率 | 显存需求 |
|------|------|------|--------|----------|
| tiny | 39M | 最快 | 一般 | ~1GB |
| base | 74M | 快 | 较好 | ~1GB |
| small | 244M | 中等 | 好 | ~2GB |
| medium | 769M | 慢 | 很好 | ~5GB |
| large | 1550M | 最慢 | 最好 | ~10GB |

**推荐**: 日常使用 `base`，追求准确用 `small`，英文内容可用 `tiny`

## 语言代码

- `zh` - 中文
- `en` - 英文
- `ja` - 日语
- `ko` - 韩语
- `auto` - 自动检测（不指定 -l 参数）

完整列表: https://github.com/openai/whisper/blob/main/whisper/tokenizer.py

## 首次使用

第一次运行会自动下载模型文件到 `~/.cache/whisper/`，下载时间取决于模型大小和网络速度。

## Python API

```python
from scripts.transcribe import transcribe_audio

text, segments = transcribe_audio(
    audio_path="audio.mp3",
    model_size="base",
    language="zh",
    device="auto"  # auto/cpu/cuda
)

print(text)
```

## 注意事项

1. **OGG/OPUS 文件**: 需要 ffmpeg 支持，脚本会自动转换
2. **GPU 加速**: 如果有 NVIDIA 显卡且安装了 CUDA，会自动使用 GPU
3. **长音频**: 会自动分段处理，每段单独输出时间戳
