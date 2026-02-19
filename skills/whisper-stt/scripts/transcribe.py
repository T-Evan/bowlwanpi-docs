#!/usr/bin/env python3
"""
Whisper STT - 本地语音转文字
支持 openai-whisper 和 faster-whisper
"""

import argparse
import os
import sys
import tempfile
import warnings
from pathlib import Path

# 忽略一些烦人的警告
warnings.filterwarnings("ignore")


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import whisper
        return "openai-whisper"
    except ImportError:
        try:
            from faster_whisper import WhisperModel
            return "faster-whisper"
        except ImportError:
            pass
    
    print("❌ 需要先安装 whisper:")
    print("   pip install openai-whisper")
    print("   或")
    print("   pip install faster-whisper")
    return None


def transcribe_with_openai_whisper(audio_path, model_size="base", language="zh"):
    """使用 openai-whisper 转录"""
    import whisper
    
    print(f"🔄 加载模型: {model_size}")
    model = whisper.load_model(model_size)
    
    print(f"🎙️ 开始转录: {audio_path}")
    
    # 转录
    result = model.transcribe(
        audio_path,
        language=language,
        task="transcribe",
        verbose=False
    )
    
    print(f"📊 检测到语言: {result.get('language', 'unknown')}")
    
    # 收集文本
    full_text = result["text"].strip()
    segments = []
    
    for seg in result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip()
        })
        print(f"[{seg['start']:.2f}s -> {seg['end']:.2f}s] {seg['text'].strip()}")
    
    return full_text, segments


def transcribe_with_faster_whisper(audio_path, model_size="base", language="zh", device="auto"):
    """使用 faster-whisper 转录"""
    from faster_whisper import WhisperModel
    
    # 自动检测设备
    if device == "auto":
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
    else:
        compute_type = "float16" if device == "cuda" else "int8"
    
    print(f"🔄 加载模型: {model_size} ({device})")
    
    # 加载模型
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    
    print(f"🎙️ 开始转录: {audio_path}")
    
    # 转录
    segments, info = model.transcribe(
        audio_path,
        language=language,
        task="transcribe",
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    print(f"📊 检测到语言: {info.language} (概率: {info.language_probability:.2%})")
    
    # 收集所有文本
    full_text = []
    segment_list = []
    
    for segment in segments:
        text = segment.text.strip()
        full_text.append(text)
        segment_list.append({
            "start": segment.start,
            "end": segment.end,
            "text": text
        })
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {text}")
    
    return " ".join(full_text), segment_list


def convert_to_wav(input_path, output_path=None):
    """将音频转换为 WAV 格式（如果需要）"""
    import subprocess
    
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".wav")
    
    # 使用 ffmpeg 转换
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        output_path
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ 音频转换失败: {e}")
        return None
    except FileNotFoundError:
        print("❌ 需要先安装 ffmpeg")
        return None


def main():
    parser = argparse.ArgumentParser(description="Whisper 语音转文字")
    parser.add_argument("audio", help="音频文件路径")
    parser.add_argument("--model", "-m", default="base",
                        choices=["tiny", "base", "small", "medium", "large", "large-v3"],
                        help="模型大小 (默认: base)")
    parser.add_argument("--language", "-l", default="zh",
                        help="语言代码 (默认: zh)")
    parser.add_argument("--device", "-d", default="auto",
                        choices=["auto", "cpu", "cuda"],
                        help="运行设备 (默认: auto)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--json", "-j", action="store_true",
                        help="输出 JSON 格式（带时间戳）")
    
    args = parser.parse_args()
    
    # 检查依赖
    backend = check_dependencies()
    if not backend:
        sys.exit(1)
    
    print(f"✅ 使用后端: {backend}")
    
    # 检查文件
    if not os.path.exists(args.audio):
        print(f"❌ 文件不存在: {args.audio}")
        sys.exit(1)
    
    # 检查是否需要转换格式
    audio_path = args.audio
    file_ext = Path(args.audio).suffix.lower()
    
    if file_ext not in [".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus", ".webm"]:
        print(f"⚠️ 不支持的格式: {file_ext}")
        sys.exit(1)
    
    # OGG/OPUS 需要转换
    needs_conversion = file_ext in [".ogg", ".opus", ".webm", ".m4a"]
    temp_wav = None
    
    if needs_conversion:
        print(f"🔄 转换音频格式...")
        temp_wav = convert_to_wav(audio_path)
        if temp_wav is None:
            sys.exit(1)
        audio_path = temp_wav
    
    try:
        # 执行转录
        if backend == "openai-whisper":
            text, segments = transcribe_with_openai_whisper(
                audio_path,
                model_size=args.model,
                language=args.language
            )
        else:
            text, segments = transcribe_with_faster_whisper(
                audio_path,
                model_size=args.model,
                language=args.language,
                device=args.device
            )
        
        # 输出结果
        print("\n" + "="*50)
        print("📝 转录结果:")
        print("="*50)
        print(text)
        print("="*50)
        
        # 保存到文件
        if args.output:
            if args.json:
                import json
                output_data = {
                    "text": text,
                    "segments": segments,
                    "language": args.language,
                    "model": args.model,
                    "backend": backend
                }
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
            else:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(text)
            print(f"✅ 已保存到: {args.output}")
        
        # 返回结果（便于脚本调用）
        return text
        
    finally:
        # 清理临时文件
        if temp_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)


if __name__ == "__main__":
    result = main()
    if result:
        print(f"\n💡 调用方式: python3 {__file__} <音频文件>")
