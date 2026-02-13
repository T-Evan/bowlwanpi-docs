#!/usr/bin/env python3
"""
快速创造工具 - 快速记录灵感、创建内容
"""

import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
PKM_DIR = WORKSPACE / "pkm"
MEMORY_DIR = WORKSPACE / "memory"


def quick_idea(content):
    """快速记录一个灵感"""
    ideas_dir = PKM_DIR / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = ideas_dir / f"灵感-{timestamp}.md"
    
    content_md = f"""# 灵感记录

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**状态**: 💡 原始想法

## 内容
{content}

## 可能的应用
（待补充）

## 下一步行动
- [ ] 深入思考可行性
- [ ] 寻找相关资源
- [ ] 制定实施计划
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content_md)
    
    print(f"✅ 灵感已记录: {filename}")
    return str(filename)


def quick_snippet(title, code, language="python"):
    """快速保存代码片段"""
    code_dir = PKM_DIR / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = code_dir / f"{title.replace(' ', '-')}-{timestamp}.md"
    
    content = f"""# {title}

**添加时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**语言**: {language}

## 代码
```{language}
{code}
```

## 使用说明
（待补充）

## 来源/参考
（待补充）
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 代码片段已保存: {filename}")
    return str(filename)


def quick_note(title, content, category="notes"):
    """快速添加笔记"""
    notes_dir = PKM_DIR / category
    notes_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = notes_dir / f"{title.replace(' ', '-')}-{timestamp}.md"
    
    note_content = f"""# {title}

**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分类**: {category}

## 内容
{content}

## 关联思考
（待补充）
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(note_content)
    
    print(f"✅ 笔记已创建: {filename}")
    return str(filename)


def quick_tweet(content, tags=None):
    """生成社交媒体内容"""
    if tags is None:
        tags = ["#AI", "#创造", "#学习"]
    
    # 限制长度
    max_len = 280 - sum(len(t) for t in tags) - len(tags) - 10
    if len(content) > max_len:
        content = content[:max_len-3] + "..."
    
    tweet = f"{content}\n{' '.join(tags)}"
    
    # 保存
    content_dir = PKM_DIR / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = content_dir / f"tweet-{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(tweet)
    
    print(f"✅ 社交媒体内容已生成")
    print(f"\n📝 内容预览:")
    print("-" * 40)
    print(tweet)
    print("-" * 40)
    print(f"💾 已保存到: {filename}")
    
    return tweet


def quick_link(url, title=None, notes=None):
    """快速收藏链接"""
    articles_dir = PKM_DIR / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d')
    safe_title = title.replace(' ', '-') if title else f"link-{timestamp}"
    filename = articles_dir / f"{safe_title}.md"
    
    content = f"""# {title or '未命名链接'}

**收藏时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**URL**: {url}

## 快速笔记
{notes or '（待补充）'}

## 内容摘要
（待阅读后填写）

## 关键收获
（待总结）

## 行动项
- [ ] 深度阅读
- [ ] 提取知识点
- [ ] 应用到实践
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 链接已收藏: {filename}")
    return str(filename)


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("""
⚡ 快速创造工具

用法: python3 quick_create.py <type> [args]

类型:
  idea "内容"           - 快速记录灵感
  snippet "标题" "代码" [语言]  - 保存代码片段
  note "标题" "内容" [分类]     - 添加笔记
  tweet "内容" [标签1,标签2]    - 生成社交媒体内容
  link "URL" "标题" [笔记]      - 收藏链接

示例:
  python3 quick_create.py idea "可以做一个自动整理下载文件的脚本"
  python3 quick_create.py snippet "快速排序" "def quick_sort(arr):..." python
  python3 quick_create.py tweet "今天学会了用Python自动生成日报，效率提升3倍！" "#Python,#效率"
        """)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "idea" and len(sys.argv) >= 3:
        quick_idea(sys.argv[2])
    
    elif cmd == "snippet" and len(sys.argv) >= 4:
        language = sys.argv[4] if len(sys.argv) > 4 else "python"
        quick_snippet(sys.argv[2], sys.argv[3], language)
    
    elif cmd == "note" and len(sys.argv) >= 4:
        category = sys.argv[4] if len(sys.argv) > 4 else "notes"
        quick_note(sys.argv[2], sys.argv[3], category)
    
    elif cmd == "tweet" and len(sys.argv) >= 3:
        tags = sys.argv[3].split(',') if len(sys.argv) > 3 else None
        quick_tweet(sys.argv[2], tags)
    
    elif cmd == "link" and len(sys.argv) >= 3:
        title = sys.argv[3] if len(sys.argv) > 3 else None
        notes = sys.argv[4] if len(sys.argv) > 4 else None
        quick_link(sys.argv[2], title, notes)
    
    else:
        print(f"❌ 命令错误或参数不足: {cmd}")


if __name__ == "__main__":
    main()
