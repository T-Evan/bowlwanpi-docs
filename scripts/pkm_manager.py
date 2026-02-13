#!/usr/bin/env python3
"""
个人知识库管理器 (PKM - Personal Knowledge Manager)
简单的 Obsidian 风格知识库，基于 Markdown
"""

import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
PKM_DIR = WORKSPACE / "pkm"
INBOX_DIR = PKM_DIR / "inbox"      # 收件箱（临时存放）
NOTES_DIR = PKM_DIR / "notes"      # 笔记目录
ARTICLES_DIR = PKM_DIR / "articles" # 文章收藏
CODE_DIR = PKM_DIR / "code"        # 代码片段
PROJECTS_DIR = PKM_DIR / "projects" # 项目归档
DAILY_DIR = PKM_DIR / "daily"      # 每日日志
IDEAS_DIR = PKM_DIR / "ideas"      # 灵感想法

# 确保目录存在
for d in [PKM_DIR, INBOX_DIR, NOTES_DIR, ARTICLES_DIR, CODE_DIR, PROJECTS_DIR, DAILY_DIR, IDEAS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def generate_id(title: str) -> str:
    """生成唯一ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    hash_str = hashlib.md5(title.encode()).hexdigest()[:6]
    return f"{timestamp}-{hash_str}"


def slugify(title: str) -> str:
    """将标题转为文件名"""
    # 移除特殊字符
    slug = re.sub(r'[^\w\s-]', '', title)
    # 替换空格为连字符
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.lower()[:50]


def add_note(title: str, content: str, category: str = "notes", tags: list = None):
    """
    添加一条笔记
    
    Args:
        title: 笔记标题
        content: 笔记内容
        category: 分类 (notes/articles/code/projects/daily/ideas)
        tags: 标签列表
    """
    # 选择目录
    dir_map = {
        "notes": NOTES_DIR,
        "article": ARTICLES_DIR,
        "articles": ARTICLES_DIR,
        "code": CODE_DIR,
        "project": PROJECTS_DIR,
        "projects": PROJECTS_DIR,
        "daily": DAILY_DIR,
        "idea": IDEAS_DIR,
        "ideas": IDEAS_DIR
    }
    target_dir = dir_map.get(category.lower(), NOTES_DIR)
    
    # 生成文件名
    slug = slugify(title)
    note_id = generate_id(title)
    filename = f"{slug}-{note_id}.md"
    filepath = target_dir / filename
    
    # 生成笔记内容
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tags_str = ' '.join([f'#{tag}' for tag in (tags or [])])
    
    note_content = f"""# {title}

> **创建时间**: {now}  
> **ID**: {note_id}  
> **分类**: {category}  
> **标签**: {tags_str}

---

{content}

---

## 关联笔记
<!-- 这里可以链接到其他笔记 -->
- 

## 思考/复盘
<!-- 后续补充 -->

"""
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(note_content)
    
    print(f"✅ 笔记已创建: {filepath}")
    return str(filepath)


def add_article(url: str, title: str = None, summary: str = None, tags: list = None):
    """添加文章收藏"""
    if not title:
        title = f"文章-{datetime.now().strftime('%m%d')}"
    
    content = f"""## 原文链接
[{url}]({url})

## 摘要
{summary or '（待补充）'}

## 关键内容
（待整理）

## 收获/启发
（待补充）
"""
    return add_note(title, content, category="articles", tags=tags or ['article', 'reading'])


def add_code_snippet(title: str, code: str, language: str = "python", description: str = "", tags: list = None):
    """添加代码片段"""
    content = f"""## 说明
{description}

## 代码 ({language})
```{language}
{code}
```

## 使用场景
（待补充）

## 注意事项
（待补充）
"""
    tags = (tags or []) + ['code', language]
    return add_note(title, content, category="code", tags=tags)


def add_idea(idea: str, tags: list = None):
    """快速记录灵感"""
    now = datetime.now()
    title = f"灵感-{now.strftime('%m%d-%H%M')}"
    content = f"""{idea}

## 可能的应用
（待展开）

## 相关思考
（待补充）
"""
    return add_note(title, content, category="ideas", tags=tags or ['idea'])


def add_daily_log(date: str = None):
    """创建每日日志"""
    now = datetime.now()
    if date:
        now = datetime.strptime(date, '%Y-%m-%d')
    
    title = f"Daily-{now.strftime('%Y-%m-%d')}"
    content = f"""## 今日完成
- [ ] 

## 学到的新东西
- 

## 遇到的问题
- 

## 明日计划
- [ ] 

## 碎片想法
- 
"""
    return add_note(title, content, category="daily", tags=['daily', 'log'])


def search_notes(keyword: str):
    """搜索笔记"""
    results = []
    
    # 遍历所有目录
    for dir_path in [NOTES_DIR, ARTICLES_DIR, CODE_DIR, PROJECTS_DIR, IDEAS_DIR]:
        if not dir_path.exists():
            continue
        
        for md_file in dir_path.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if keyword.lower() in content.lower():
                    # 提取标题
                    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
                    title = title_match.group(1) if title_match else md_file.stem
                    
                    # 提取前100字作为预览
                    preview = content.replace('#', '').replace('\n', ' ')[:150]
                    
                    results.append({
                        'title': title,
                        'file': str(md_file.relative_to(PKM_DIR)),
                        'preview': preview + '...',
                        'category': dir_path.name
                    })
            except:
                continue
    
    return results


def list_notes(category: str = None, limit: int = 20):
    """列出笔记"""
    dirs = []
    if category:
        dir_map = {
            "notes": NOTES_DIR, "articles": ARTICLES_DIR, "code": CODE_DIR,
            "projects": PROJECTS_DIR, "daily": DAILY_DIR, "ideas": IDEAS_DIR
        }
        if category.lower() in dir_map:
            dirs = [dir_map[category.lower()]]
    else:
        dirs = [NOTES_DIR, ARTICLES_DIR, CODE_DIR, PROJECTS_DIR, IDEAS_DIR]
    
    notes = []
    for dir_path in dirs:
        if not dir_path.exists():
            continue
        for md_file in sorted(dir_path.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else md_file.stem
                
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                
                notes.append({
                    'title': title,
                    'file': str(md_file),
                    'category': dir_path.name,
                    'updated': mtime.strftime('%m-%d %H:%M')
                })
            except:
                continue
    
    return sorted(notes, key=lambda x: x['updated'], reverse=True)[:limit]


def get_stats():
    """获取知识库统计"""
    stats = {}
    total = 0
    
    for name, dir_path in [
        ("笔记", NOTES_DIR), ("文章", ARTICLES_DIR), ("代码", CODE_DIR),
        ("项目", PROJECTS_DIR), ("日志", DAILY_DIR), ("灵感", IDEAS_DIR)
    ]:
        if dir_path.exists():
            count = len(list(dir_path.glob("*.md")))
            stats[name] = count
            total += count
    
    stats['总计'] = total
    return stats


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("""
🧠 个人知识库管理器 (PKM)

用法: python3 pkm_manager.py <command> [args]

命令:
  add-note "标题" "内容" [分类] [标签]    - 添加笔记
  add-article "URL" "标题" [摘要]          - 收藏文章
  add-code "标题" "代码" [语言] [描述]      - 保存代码片段
  add-idea "想法内容" [标签]               - 快速记录灵感
  daily [日期]                             - 创建每日日志
  search "关键词"                          - 搜索笔记
  list [分类] [数量]                       - 列出笔记
  stats                                    - 统计信息

示例:
  python3 pkm_manager.py add-idea "可以做一个AI助手来管理所有账号"
  python3 pkm_manager.py add-article "https://example.com" "好文章"
  python3 pkm_manager.py search "Python"
  python3 pkm_manager.py list articles 10
        """)
        return
    
    command = sys.argv[1]
    
    if command == "add-note" and len(sys.argv) >= 4:
        add_note(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "notes")
    
    elif command == "add-article" and len(sys.argv) >= 3:
        add_article(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None, 
                   sys.argv[4] if len(sys.argv) > 4 else None)
    
    elif command == "add-code" and len(sys.argv) >= 4:
        add_code_snippet(sys.argv[2], sys.argv[3], 
                        sys.argv[4] if len(sys.argv) > 4 else "python",
                        sys.argv[5] if len(sys.argv) > 5 else "")
    
    elif command == "add-idea" and len(sys.argv) >= 3:
        add_idea(sys.argv[2], sys.argv[3].split(',') if len(sys.argv) > 3 else None)
    
    elif command == "daily":
        add_daily_log(sys.argv[2] if len(sys.argv) > 2 else None)
    
    elif command == "search" and len(sys.argv) >= 3:
        results = search_notes(sys.argv[2])
        print(f"\n🔍 找到 {len(results)} 条笔记:\n")
        for r in results:
            print(f"📄 {r['title']} [{r['category']}]")
            print(f"   {r['preview']}")
            print(f"   📁 {r['file']}\n")
    
    elif command == "list":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        notes = list_notes(category, limit)
        print(f"\n📝 最近笔记:\n")
        for n in notes:
            print(f"  📄 {n['title']} [{n['category']}] - {n['updated']}")
    
    elif command == "stats":
        stats = get_stats()
        print("\n📊 知识库统计:\n")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    
    else:
        print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
