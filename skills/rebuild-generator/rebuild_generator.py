#!/usr/bin/env python3
"""
重建手册生成器 - 碗皮自主维护工作
扫描当前所有能力状态，生成重建摘要文档
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
MEMORY_DIR = os.path.join(WORKSPACE, "memory")

def ensure_dirs():
    """确保必要的目录存在"""
    os.makedirs(MEMORY_DIR, exist_ok=True)

def scan_files():
    """扫描工作区文件结构"""
    files_info = {
        "workspace_root": [],
        "memory_files": [],
        "skills": [],
        "config_files": []
    }
    
    # 扫描根目录
    for item in os.listdir(WORKSPACE):
        item_path = os.path.join(WORKSPACE, item)
        if os.path.isfile(item_path):
            files_info["workspace_root"].append({
                "name": item,
                "size": os.path.getsize(item_path)
            })
    
    # 扫描memory目录
    if os.path.exists(MEMORY_DIR):
        for item in os.listdir(MEMORY_DIR):
            item_path = os.path.join(MEMORY_DIR, item)
            if os.path.isfile(item_path):
                files_info["memory_files"].append({
                    "name": item,
                    "size": os.path.getsize(item_path)
                })
    
    # 扫描skills目录
    skills_dir = os.path.join(WORKSPACE, "skills")
    if os.path.exists(skills_dir):
        for root, dirs, files in os.walk(skills_dir):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), WORKSPACE)
                files_info["skills"].append(rel_path)
    
    # 识别配置文件
    config_patterns = ["*.md", "*.json", "*.yaml", "*.yml", "*.toml"]
    for pattern in config_patterns:
        for match in glob.glob(os.path.join(WORKSPACE, pattern)):
            files_info["config_files"].append(os.path.basename(match))
    
    return files_info

def read_core_configs():
    """读取核心配置文件内容"""
    configs = {}
    core_files = ["SOUL.md", "USER.md", "AGENTS.md", "TOOLS.md", "MEMORY.md"]
    
    for filename in core_files:
        filepath = os.path.join(WORKSPACE, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    configs[filename] = {
                        "exists": True,
                        "size": os.path.getsize(filepath),
                        "preview": f.read()[:500] + "..." if os.path.getsize(filepath) > 500 else f.read()
                    }
            except Exception as e:
                configs[filename] = {"exists": True, "error": str(e)}
        else:
            configs[filename] = {"exists": False}
    
    return configs

def scan_memory_system():
    """扫描记忆系统状态"""
    memory_status = {
        "daily_notes": [],
        "total_memory_files": 0,
        "memory_size_bytes": 0
    }
    
    if os.path.exists(MEMORY_DIR):
        for item in os.listdir(MEMORY_DIR):
            if item.endswith('.md'):
                filepath = os.path.join(MEMORY_DIR, item)
                size = os.path.getsize(filepath)
                memory_status["daily_notes"].append({
                    "file": item,
                    "size": size
                })
                memory_status["total_memory_files"] += 1
                memory_status["memory_size_bytes"] += size
    
    return memory_status

def generate_rebuild_summary(files_info, configs, memory_status):
    """生成重建摘要文档"""
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    summary = f"""# 🔄 重建手册摘要 - {today}

> 自动生成时间: {timestamp}
> 生成器版本: 1.0.0

---

## 📊 系统概览

### 工作区结构
| 项目 | 数量 | 说明 |
|------|------|------|
| 根目录文件 | {len(files_info['workspace_root'])} | 核心配置文件 |
| 记忆文件 | {memory_status['total_memory_files']} | 历史记录 |
| 技能脚本 | {len(files_info['skills'])} | 自动化工具 |
| 配置文件 | {len(files_info['config_files'])} | 各类配置 |

### 记忆系统状态
- **总文件数**: {memory_status['total_memory_files']}
- **总大小**: {memory_status['memory_size_bytes'] / 1024:.2f} KB

**每日笔记列表:**
"""
    
    for note in sorted(memory_status['daily_notes'], reverse=True)[:10]:
        summary += f"- `{note['file']}` ({note['size']} bytes)\n"
    
    summary += f"""

---

## 🔧 核心配置文件状态

| 文件 | 状态 | 大小 |
|------|------|------|
"""
    
    for filename, info in configs.items():
        status = "✅ 存在" if info.get("exists") else "❌ 缺失"
        size = f"{info.get('size', 0)} bytes" if info.get("exists") else "-"
        summary += f"| {filename} | {status} | {size} |\n"
    
    summary += f"""

---

## 📁 详细文件清单

### 根目录文件
"""
    for f in files_info['workspace_root']:
        summary += f"- `{f['name']}` ({f['size']} bytes)\n"
    
    summary += f"""

### 技能脚本
"""
    if files_info['skills']:
        for skill in files_info['skills']:
            summary += f"- `{skill}`\n"
    else:
        summary += "- (暂无技能脚本)\n"
    
    summary += f"""

---

## 🚀 重建步骤

如需在新服务器重建碗皮，按以下步骤操作:

### 1. 基础环境
```bash
# 确保目录结构
mkdir -p /root/.openclaw/workspace/memory
mkdir -p /root/.openclaw/workspace/skills
```

### 2. 恢复核心配置
按上述【核心配置文件状态】创建对应文件，内容参考预览。

### 3. 恢复记忆文件
将每日笔记复制到 `memory/` 目录。

### 4. 验证
```bash
# 检查关键文件
ls -la /root/.openclaw/workspace/*.md
ls -la /root/.openclaw/workspace/memory/
```

---

## 📝 生成日志

- 生成时间: {timestamp}
- 生成器: rebuild_generator.py
- 执行环境: OpenClaw VM

---

*本文件由碗皮自主维护系统自动生成*
"""
    
    return summary

def save_summary(summary):
    """保存摘要文档"""
    today = datetime.now().strftime("%Y-%m-%d")
    summary_path = os.path.join(MEMORY_DIR, f"rebuild-summary-{today}.md")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    return summary_path

def log_execution(status, message, summary_path):
    """记录执行日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    log_path = os.path.join(MEMORY_DIR, "nightly-build.log")
    
    log_entry = f"""
[{timestamp}] 重建手册生成任务
- 状态: {status}
- 消息: {message}
- 输出文件: {summary_path}
---
"""
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    return log_path

def main():
    print("🔄 开始执行重建手册生成任务...")
    
    # 确保目录
    ensure_dirs()
    print("✓ 目录检查完成")
    
    # 扫描文件
    print("📂 扫描工作区文件...")
    files_info = scan_files()
    print(f"  - 根目录文件: {len(files_info['workspace_root'])} 个")
    print(f"  - 技能脚本: {len(files_info['skills'])} 个")
    
    # 读取配置
    print("📖 读取核心配置...")
    configs = read_core_configs()
    
    # 扫描记忆系统
    print("🧠 扫描记忆系统...")
    memory_status = scan_memory_system()
    print(f"  - 记忆文件: {memory_status['total_memory_files']} 个")
    
    # 生成摘要
    print("📝 生成重建摘要...")
    summary = generate_rebuild_summary(files_info, configs, memory_status)
    
    # 保存摘要
    summary_path = save_summary(summary)
    print(f"✓ 摘要已保存: {summary_path}")
    
    # 记录日志
    log_path = log_execution("✅ 成功", "重建手册生成完成", summary_path)
    print(f"✓ 日志已记录: {log_path}")
    
    print("\\n🎉 任务完成！")
    print(f"   输出: {summary_path}")
    
    return summary_path

if __name__ == "__main__":
    main()
