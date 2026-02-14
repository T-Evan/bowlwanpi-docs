#!/usr/bin/env python3
"""
TTRPG 跑团存档管理器
帮助记录和管理跑团进度
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 基础路径
TTRPG_DIR = Path("/root/.openclaw/workspace/memory/ttrpg")
CAMPAIGNS_DIR = TTRPG_DIR / "campaigns"
ACTIVE_DIR = CAMPAIGNS_DIR / "active"
COMPLETED_DIR = CAMPAIGNS_DIR / "completed"
CHARACTERS_DIR = TTRPG_DIR / "characters"
SESSION_LOGS_DIR = TTRPG_DIR / "session-logs"

# 确保目录存在
for d in [ACTIVE_DIR, COMPLETED_DIR, CHARACTERS_DIR, SESSION_LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def get_campaign_path(name: str) -> Path:
    """获取战役文件路径"""
    safe_name = "".join(c for c in name if c.isalnum() or c in "-_ ").strip()
    safe_name = safe_name.replace(" ", "-")
    
    # 先在active中找
    path = ACTIVE_DIR / f"{safe_name}.md"
    if path.exists():
        return path
    
    # 再在completed中找
    path = COMPLETED_DIR / f"{safe_name}.md"
    if path.exists():
        return path
    
    # 默认返回active路径
    return ACTIVE_DIR / f"{safe_name}.md"


def new_campaign(name: str, universe: str = "未设定"):
    """创建新战役"""
    path = get_campaign_path(name)
    
    if path.exists():
        print(f"❌ 战役 '{name}' 已存在！")
        return False
    
    now = datetime.now().strftime("%Y-%m-%d")
    
    template = f"""# {name} - 跑团存档

**创建日期**: {now}
**世界观**: {universe}
**GM**: 碗皮 🎲
**玩家**: 一碗 🥣
**状态**: 🟢 进行中

---

## 🎭 角色卡

### 基本信息
**姓名**: （待创建）
**职业/身份**: 
**年龄**: 
**外貌**: 

### 背景故事
（待填写）

### 核心设定
**动机**: （是什么驱动着这个角色？）
**道德底线**: （什么是绝对不会做的？）
**恐惧**: 
**渴望**: 

### 属性
| 属性 | 基础值 | 调整值 | 备注 |
|------|--------|--------|------|
| 力量 | 10 | +0 | |
| 敏捷 | 10 | +0 | |
| 体质 | 10 | +0 | |
| 智力 | 10 | +0 | |
| 感知 | 10 | +0 | |
| 魅力 | 10 | +0 | |

### 技能专长
- 

### 装备物品
| 物品 | 描述 | 数量 |
|------|------|------|
| | | |

### 人际关系
| 人物 | 关系 | 信任度 | 备注 |
|------|------|--------|------|
| | | | |

---

## 📍 剧情进度

### 当前场景
📌 （待记录）

### 活跃任务/目标
- [ ] （主线）
- [ ] （支线）

### 已完成任务
- [x] （记录已完成的事项）

### 关键决定 & 后果追踪
| 章节 | 决定 | 后果 | 状态 |
|------|------|------|------|
| | | | 🔄进行中 |

### 重要NPC档案
| 名字 | 身份 | 关系 | 当前状态 |
|------|------|------|----------|
| | | | |

### 势力分布
| 势力 | 态度 | 势力范围 | 备注 |
|------|------|----------|------|
| | | | |

---

## 📖 会话记录

### Session 1 - {now}
**场景**: （地点、时间、氛围）
**参与**: 一碗（角色名）
**发生的事**:
1. 

**战斗/冲突**:
- 

**获得**:
- 物品：
- 信息：
- 关系：

**待续/伏笔**:
- 

---

## 🎯 下次预告
（GM准备的下个场景线索）

---

*最后更新: {now}*
*下次会话: （待定）*
"""
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ 新战役 '{name}' 已创建！")
    print(f"📁 存档位置: {path}")
    return True


def log_session(name: str, content: str):
    """记录会话日志"""
    path = get_campaign_path(name)
    
    if not path.exists():
        print(f"❌ 战役 '{name}' 不存在！先用 'new' 创建")
        return False
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    # 读取现有内容
    with open(path, 'r', encoding='utf-8') as f:
        existing = f.read()
    
    # 查找当前session数
    session_count = existing.count("### Session ")
    new_session_num = session_count + 1
    
    # 创建新session记录
    new_session = f"""
### Session {new_session_num} - {date_str}
**时间**: {time_str}
**发生的事**:
{content}

---
"""
    
    # 插入到"会话记录"部分后面
    if "## 📖 会话记录" in existing:
        marker = "## 📖 会话记录"
        idx = existing.find(marker) + len(marker)
        new_content = existing[:idx] + "\n" + new_session + existing[idx:]
    else:
        new_content = existing + "\n" + new_session
    
    # 更新最后更新时间
    new_content = new_content.replace(
        f"*最后更新: {date_str}*",
        f"*最后更新: {date_str} {time_str}*"
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Session {new_session_num} 已记录到 '{name}'")
    return True


def update_field(name: str, field: str, value: str):
    """更新战役字段"""
    path = get_campaign_path(name)
    
    if not path.exists():
        print(f"❌ 战役 '{name}' 不存在！")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单的字段更新（可以根据需要扩展）
    print(f"📝 请手动编辑文件更新字段: {path}")
    return True


def show_status(name: str):
    """显示战役状态"""
    path = get_campaign_path(name)
    
    if not path.exists():
        print(f"❌ 战役 '{name}' 不存在！")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n{'='*50}")
    print(f"📚 战役: {name}")
    print(f"{'='*50}")
    
    # 提取关键信息
    lines = content.split('\n')
    for line in lines[:50]:  # 只看前50行
        if line.strip().startswith('**'):
            print(line)
    
    session_count = content.count("### Session ")
    print(f"\n📖 已进行 {session_count} 次会话")
    
    # 显示最后更新
    if "*最后更新:" in content:
        for line in lines:
            if "*最后更新:" in line:
                print(line)
                break
    
    print(f"{'='*50}")
    return True


def list_campaigns():
    """列出所有战役"""
    print("\n🎮 进行中的战役:")
    print("-" * 40)
    
    active_count = 0
    for f in sorted(ACTIVE_DIR.glob("*.md")):
        name = f.stem
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        session_count = content.count("### Session ")
        print(f"  🟢 {name} ({session_count} sessions)")
        active_count += 1
    
    if active_count == 0:
        print("  （暂无）")
    
    print("\n✅ 已完成的战役:")
    print("-" * 40)
    
    completed_count = 0
    for f in sorted(COMPLETED_DIR.glob("*.md")):
        name = f.stem
        print(f"  ✓ {name}")
        completed_count += 1
    
    if completed_count == 0:
        print("  （暂无）")
    
    print(f"\n总计: {active_count} 进行中, {completed_count} 已完成")


def complete_campaign(name: str):
    """标记战役为完成"""
    active_path = ACTIVE_DIR / f"{name}.md"
    completed_path = COMPLETED_DIR / f"{name}.md"
    
    if not active_path.exists():
        print(f"❌ 战役 '{name}' 不存在或已完成！")
        return False
    
    # 移动文件
    import shutil
    shutil.move(active_path, completed_path)
    
    # 更新状态
    with open(completed_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace("**状态**: 🟢 进行中", "**状态**: ✅ 已完成")
    content = content.replace("**状态**: 进行中", "**状态**: 已完成")
    
    now = datetime.now().strftime("%Y-%m-%d")
    content += f"\n\n---\n*战役于 {now} 完结*\n"
    
    with open(completed_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 战役 '{name}' 已标记为完成！")
    return True


def show_help():
    """显示帮助"""
    help_text = """
🎲 TTRPG 跑团存档管理器

用法: python3 ttrpg_manager.py <command> [args]

命令:
  new <name> [universe]    创建新战役
  log <name> "content"      记录会话
  status <name>            查看战役状态
  list                     列出所有战役
  complete <name>          标记战役完成
  help                     显示帮助

示例:
  python3 ttrpg_manager.py new "夜之城往事" "赛博朋克2077"
  python3 ttrpg_manager.py log "夜之城往事" "和 fixer 接了第一单"
  python3 ttrpg_manager.py status "夜之城往事"
  python3 ttrpg_manager.py list
    """
    print(help_text)


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "new" and len(sys.argv) >= 3:
        name = sys.argv[2]
        universe = sys.argv[3] if len(sys.argv) > 3 else "未设定"
        new_campaign(name, universe)
    
    elif command == "log" and len(sys.argv) >= 4:
        name = sys.argv[2]
        content = sys.argv[3]
        log_session(name, content)
    
    elif command == "status" and len(sys.argv) >= 3:
        name = sys.argv[2]
        show_status(name)
    
    elif command == "list":
        list_campaigns()
    
    elif command == "complete" and len(sys.argv) >= 3:
        name = sys.argv[2]
        complete_campaign(name)
    
    elif command == "help":
        show_help()
    
    else:
        print("❌ 未知命令或参数不足")
        show_help()


if __name__ == "__main__":
    main()
