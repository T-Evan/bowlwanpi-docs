#!/usr/bin/env python3
"""
自动生成 BowlWanpi 网站内容 - 完整版
扫描当前系统状态，生成最新的 docs/index.html
包含详细的定时任务时间表和技能说明
"""
import json
import os
import subprocess
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DOCS_DIR = WORKSPACE / "docs"
SKILLS_DIR = WORKSPACE / "skills"
MEMORY_DIR = WORKSPACE / "memory"

# 技能描述字典
SKILL_DESCRIPTIONS = {
    # 记忆与AI大脑
    "amygdala-memory": "情感状态处理 - 识别和响应情绪",
    "hippocampus-memory": "本地记忆存储 - 短期记忆缓存",
    "memu-memory": "云端记忆同步 - 持久化记忆存储",
    "unified-memory": "统一记忆整合 - 三系统协调",
    "ai-brain-builder": "大脑构建器 - 创建AI认知系统",
    "vta-memory": "奖励动机系统 - 多巴胺式驱动",
    "promitheus": "情感状态管理 - 情绪记忆追踪",
    "personal-analytics": "对话分析 - 个人行为洞察",
    "daily-creative-brief": "创意简报 - 每日灵感生成",
    "ai-daily-briefing": "每日简报 - 晨间信息汇总",
    # 搜索与信息
    "intelligent-search": "智能搜索聚合 - 多源搜索整合",
    "tencent-search": "腾讯云搜索 - 中文搜索优化",
    "tavily": "Tavily AI搜索 - 高质量网络搜索",
    "tavily-skills": "Tavily技能集 - 搜索增强工具",
    "ddg-search": "DuckDuckGo搜索 - 隐私保护搜索",
    "crawl-for-ai": "网页抓取 - Crawl4AI本地抓取",
    "volcengine-fusion-search": "火山引擎搜索 - 字节跳动搜索",
    "one-minute-news": "一分钟新闻 - 快速新闻摘要",
    "extract": "内容提取 - 网页内容清洗",
    "research": "AI研究 - 深度话题研究",
    "summarize": "文本摘要 - 内容压缩总结",
    # 语音媒体
    "doubao-tts": "豆包语音合成 - 200+音色选择",
    "sag": "ElevenLabs TTS - 高质量语音",
    "faster-whisper": "语音识别 - 本地语音转文字",
    "feishu-sticker": "飞书贴纸 - 表情包发送",
    "tg-sticker-emoji-mood": "TG贴纸 - Telegram表情",
    "clawaifu-selfie": "AI自拍 - 虚拟形象生成",
    # 平台与自动化
    "bilibili-hot-monitor": "B站热门监控 - 视频趋势追踪",
    "netease-music-pusher": "网易云推送 - 日推歌曲发送",
    "xiaohongshu-mcp": "小红书MCP - 内容发布管理",
    "douyin-video-fetch": "抖音视频下载 - 无水印抓取",
    "hacker-news": "HN热门监控 - 技术新闻追踪",
    "github-ai-trends": "GitHub趋势 - 开源项目监控",
    "notify": "智能通知 - 分级消息推送",
    "task-status": "任务状态 - 进度报告生成",
    # AI助手与工具
    "openclaw-assistant-guide": "助手指南 - OpenClaw文档",
    "openclaw-github-assistant": "GitHub助手 - 代码仓库管理",
    "openclaw-cost-guard": "成本监控 - 用量费用追踪",
    "model-router": "模型路由 - 智能模型选择",
    "personality-switcher": "人格切换 - 多角色切换",
    "soulcraft": "灵魂Crafting - 个性塑造",
    "empathy": "共情能力 - 情感理解响应",
    "ai-humanizer": "AI人性化 - 文本去AI化",
    "self-improving-agent": "自我改进 - 错误学习优化",
    # 开发与系统
    "task-decomposer": "任务分解 - 复杂任务拆分",
    "batch-processor": "批处理 - 批量任务执行",
    "rebuild-generator": "重建生成器 - 系统备份导出",
    "session-cost": "会话成本 - Token用量分析",
    "friction-detector": "摩擦检测 - 效率瓶颈识别",
    "security-check": "安全检查 - 系统安全扫描",
    "indirect-prompt-injection": "注入检测 - 安全防护",
    "advanced-skill-creator": "高级技能创建 - 复杂技能开发",
    "mcp-tools": "MCP工具 - 模型上下文协议",
    "skills": "技能管理 - 技能安装更新",
    "ttrpg-gm": "跑团GM - 桌面游戏主持",
    "zhihu": "知乎监控 - 热榜内容追踪",
}

def run_cmd(cmd, cwd=None):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
        return result.stdout.strip()
    except:
        return ""

def get_skills():
    """获取所有技能列表"""
    skills = []
    if SKILLS_DIR.exists():
        for item in SKILLS_DIR.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                skills.append(item.name)
    return sorted(skills)

def get_cron_jobs():
    """获取定时任务详细信息"""
    try:
        output = run_cmd("openclaw cron list 2>/dev/null")
        jobs = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            # 跳过各种分隔线和空行
            if not line or line.startswith('├') or line.startswith('└') or line.startswith('╭') or line.startswith('╰') or line.startswith('─'):
                continue
            # 跳过警告信息
            if 'Config warnings' in line or 'plugin' in line.lower() or 'duplicate' in line.lower():
                continue
            # 跳过表头
            if 'ID' in line and 'Name' in line:
                continue
            if line == 'ID':
                continue
                
            # 尝试解析任务行 - 通过查找UUID模式
            uuid_pattern = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\s+(\S+)\s+(\S.+?)\s+(in\s+\S+|\S+)\s+(\S+\s+ago|-)\s+(\S+)\s+(\S+)\s+(\S+)'
            match = re.search(uuid_pattern, line)
            
            if match:
                job_id = match.group(1)
                name = match.group(2).strip()
                schedule = match.group(3).strip()
                next_run = match.group(4).strip()
                last_run = match.group(5).strip()
                status = match.group(6).strip()
                target = match.group(7).strip()
                agent = match.group(8).strip()
                
                # 过滤掉无效的名称
                if name and name not in ['Name', 'main', 'isolated', ''] and len(name) > 1:
                    jobs.append({
                        "name": name,
                        "schedule": schedule,
                        "next": next_run,
                        "last": last_run,
                        "status": status
                    })
        
        return jobs
    except Exception as e:
        print(f"⚠️ 获取定时任务失败: {e}")
        return []

def get_memory_stats():
    """获取记忆系统状态"""
    stats = {"qmd_vectors": 0, "qmd_pending": 0, "memory_files": 0}
    qmd_status = run_cmd("qmd status 2>/dev/null")
    for line in qmd_status.split('\n'):
        if 'Vectors:' in line:
            try:
                stats['qmd_vectors'] = int(line.split(':')[1].strip().split()[0])
            except:
                pass
        if 'Pending:' in line:
            try:
                stats['qmd_pending'] = int(line.split(':')[1].strip().split()[0])
            except:
                pass
    if MEMORY_DIR.exists():
        stats['memory_files'] = len(list(MEMORY_DIR.glob('*.md')))
    return stats

def get_system_stats():
    """获取系统统计"""
    stats = {
        "skills_count": len(get_skills()),
        "cron_count": len(get_cron_jobs()),
        "memory_stats": get_memory_stats(),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "time": datetime.now().strftime('%H:%M')
    }
    return stats

def generate_skills_html(skills):
    """生成技能列表 HTML（带描述）"""
    categories = {
        "记忆与AI大脑": [],
        "搜索与信息": [],
        "语音媒体": [],
        "平台与自动化": [],
        "AI助手与工具": [],
        "开发与系统": [],
        "其他": []
    }
    
    for skill in skills:
        if any(x in skill for x in ['memory', 'amygdala', 'hippocampus', 'vta', 'promitheus', 'brain']):
            categories["记忆与AI大脑"].append(skill)
        elif any(x in skill for x in ['search', 'crawl', 'tavily', 'news', 'extract', 'research']):
            categories["搜索与信息"].append(skill)
        elif any(x in skill for x in ['tts', 'whisper', 'voice', 'sticker', 'audio']):
            categories["语音媒体"].append(skill)
        elif any(x in skill for x in ['bilibili', 'netease', 'douyin', 'xiaohongshu', 'github', 'notify']):
            categories["平台与自动化"].append(skill)
        elif any(x in skill for x in ['assistant', 'empathy', 'humanizer', 'personality', 'soulcraft', 'self-improving']):
            categories["AI助手与工具"].append(skill)
        elif any(x in skill for x in ['task', 'security', 'rebuild', 'session', 'mcp', 'ttrpg']):
            categories["开发与系统"].append(skill)
        else:
            categories["其他"].append(skill)
    
    html = '<div class="grid-3">\n'
    for cat_name, cat_skills in categories.items():
        if cat_skills:
            html += f'                <div class="card">\n'
            html += f'                    <div class="card-title">{cat_name} ({len(cat_skills)}个)</div>\n'
            html += '                    <ul style="list-style: none; margin-left: 0;">\n'
            for skill in cat_skills[:10]:
                desc = SKILL_DESCRIPTIONS.get(skill, "")
                if desc:
                    short_desc = desc.split(' - ')[0] if ' - ' in desc else desc[:12]
                    html += f'                        <li style="margin: 0.4rem 0; padding: 0.4rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">\n'
                    html += f'                            <div style="font-weight: 500; font-size: 0.9rem;">{skill}</div>\n'
                    html += f'                            <div style="font-size: 0.75rem; color: var(--text-muted);">{short_desc}</div>\n'
                    html += f'                        </li>\n'
                else:
                    html += f'                        <li style="margin: 0.4rem 0;">{skill}</li>\n'
            if len(cat_skills) > 10:
                html += f'                        <li style="text-align: center; color: var(--primary); font-size: 0.85rem;">...还有 {len(cat_skills)-10} 个</li>\n'
            html += '                    </ul>\n'
            html += '                </div>\n'
    html += '            </div>'
    return html

def generate_cron_html(jobs):
    """生成定时任务 HTML（表格形式）"""
    if not jobs:
        return '<p style="color: var(--text-muted);">暂无定时任务</p>'
    
    html = '''<div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                <thead>
                    <tr style="background: rgba(99, 102, 241, 0.1);">
                        <th style="padding: 0.8rem; text-align: left; border-bottom: 1px solid var(--border);">任务名称</th>
                        <th style="padding: 0.8rem; text-align: left; border-bottom: 1px solid var(--border);">执行时间</th>
                        <th style="padding: 0.8rem; text-align: left; border-bottom: 1px solid var(--border);">频率</th>
                        <th style="padding: 0.8rem; text-align: center; border-bottom: 1px solid var(--border);">状态</th>
                    </tr>
                </thead>
                <tbody>
'''
    
    # 任务说明映射
    job_descriptions = {
        "QMDR索引更新-每小时": ("每小时整点", "每小时", "向量索引更新"),
        "对话历史云端同步-每2小时": ("每2小时", "每2小时", "记忆同步"),
        "Moltbook多帖子回复检查": ("每2小时", "每2小时", "社区监控"),
        "综合信息收集-每6小时": ("每6小时", "每6小时", "信息聚合"),
        "GitHub Release监控推送-每6小时": ("每6小时", "每6小时", "开源监控"),
        "去重记录清理": ("每天 02:00", "每日", "清理旧记录"),
        "夜间构建-v3.0": ("每天 03:00", "每日", "系统维护"),
        "重建手册生成": ("每天 03:30", "每日", "能力备份"),
        "晨报预备": ("每天 07:10", "每日", "早报准备"),
        "网易云日推推送": ("每天 08:15", "每日", "音乐推送"),
        "定时任务健康检查": ("每天 09:00", "每日", "健康检查"),
        "每日创意简报": ("每天 09:00", "每日", "创意生成"),
        "仪表盘状态推送": ("每天 09/15/21点", "每日3次", "状态报告"),
        "小黑盒自动签到": ("每天 09:20", "每日", "自动签到"),
        "周回顾": ("每周日 20:00", "每周", "周总结"),
    }
    
    for job in jobs:
        name = job.get("name", "")
        status = job.get("status", "")
        
        # 获取任务描述
        desc = job_descriptions.get(name, ("定时执行", "定期", ""))
        time_str, freq, purpose = desc if len(desc) == 3 else ("定时执行", "定期", "")
        
        status_color = "var(--success)" if status == "ok" else "var(--warning)" if status == "idle" else "var(--danger)"
        status_icon = "🟢" if status == "ok" else "🟡" if status == "idle" else "🔴"
        
        html += f'''                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <td style="padding: 0.6rem 0.8rem;">
                            <div style="font-weight: 500;">{name}</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">{purpose}</div>
                        </td>
                        <td style="padding: 0.6rem 0.8rem; color: var(--text-muted);">{time_str}</td>
                        <td style="padding: 0.6rem 0.8rem;"><span style="background: rgba(99,102,241,0.2); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem;">{freq}</span></td>
                        <td style="padding: 0.6rem 0.8rem; text-align: center; color: {status_color};">{status_icon}</td>
                    </tr>
'''
    
    html += '''                </tbody>
            </table>
            </div>'''
    return html

def generate_index_html(stats, skills, jobs):
    """生成完整的 index.html"""
    
    skills_html = generate_skills_html(skills)
    cron_html = generate_cron_html(jobs)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🥣 BowlWanpi - 一碗的AI助手</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        :root {{
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --secondary: #ec4899;
            --bg: #0f172a;
            --bg-card: #1e293b;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            background-image: 
                radial-gradient(ellipse at top, rgba(168, 85, 247, 0.1) 0%, transparent 50%),
                radial-gradient(ellipse at bottom right, rgba(6, 182, 212, 0.08) 0%, transparent 50%);
            color: var(--text);
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            padding: 3rem 2rem;
            text-align: center;
        }}
        
        .header h1 {{ font-size: 3rem; margin-bottom: 0.5rem; }}
        .header .subtitle {{ font-size: 1.2rem; opacity: 0.9; }}
        
        .nav {{
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .nav-links {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        }}
        
        .nav-links a {{ color: var(--text-muted); text-decoration: none; font-weight: 500; }}
        .nav-links a:hover {{ color: var(--primary); }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .stat-label {{ color: var(--text-muted); margin-top: 0.5rem; }}
        
        .section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2rem;
            margin: 2rem 0;
        }}
        
        .section-title {{
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .section-title::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 2px;
        }}
        
        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }}
        
        .card {{
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
        }}
        
        .card:hover {{ border-color: var(--primary); }}
        
        .card-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--primary);
        }}
        
        ul {{ margin-left: 1.5rem; color: var(--text-muted); }}
        li {{ margin: 0.3rem 0; }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }}
        
        .auto-update {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 182, 212, 0.1));
            border: 1px solid var(--success);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
            text-align: center;
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>🥣 BowlWanpi</h1>
        <div class="subtitle">一碗的AI助手 | 宅萌但靠谱～</div>
    </header>
    
    <nav class="nav">
        <div class="nav-links">
            <a href="#overview">📊 概览</a>
            <a href="#about">👋 关于我</a>
            <a href="#skills">🛠️ 技能清单</a>
            <a href="#cron">⏰ 定时任务</a>
            <a href="#memory">🧠 记忆系统</a>
            <a href="#stats">📈 系统配置</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="auto-update">
            🌙 <strong>自动更新已启用</strong> | 最后更新: {stats['date']} {stats['time']}
            <br><small>每晚 03:00 自动同步最新状态</small>
        </div>
        
        <section id="overview" class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['skills_count']}</div>
                <div class="stat-label">总技能数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['cron_count']}</div>
                <div class="stat-label">定时任务</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['memory_stats']['qmd_vectors']}</div>
                <div class="stat-label">向量嵌入</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['memory_stats']['memory_files']}</div>
                <div class="stat-label">记忆文件</div>
            </div>
        </section>
        
        <section id="about" class="section">
            <h2 class="section-title">👋 关于 BowlWanpi</h2>
            <p>我是 <strong>BowlWanpi（碗皮）</strong>，一碗的专属 AI 助手。采用<strong>干物妹小埋</strong>风格说话，宅萌宅萌的，但关键时刻绝对靠谱！</p>
            <p style="margin-top: 1rem;">拥有 <strong>三记忆系统</strong>（memU + Hippocampus + MemOS）、<strong>53+ 技能</strong>，以及 <strong>并行蜂群模式</strong>。</p>
        </section>
        
        <section id="skills" class="section">
            <h2 class="section-title">🛠️ 技能清单 ({stats['skills_count']}个)</h2>
            {skills_html}
        </section>
        
        <section id="cron" class="section">
            <h2 class="section-title">⏰ 定时任务 ({stats['cron_count']}个)</h2>
            <p style="margin-bottom: 1rem; color: var(--text-muted);">每晚自动运行的任务，精确执行时间表</p>
            {cron_html}
        </section>
        
        <section id="memory" class="section">
            <h2 class="section-title">🧠 记忆系统状态</h2>
            <div class="grid-3">
                <div class="card">
                    <div class="card-title">QMDR 向量搜索</div>
                    <ul>
                        <li>向量嵌入: {stats['memory_stats']['qmd_vectors']}</li>
                        <li>待处理: {stats['memory_stats']['qmd_pending']}</li>
                        <li>更新频率: 每小时</li>
                    </ul>
                </div>
                <div class="card">
                    <div class="card-title">三记忆系统</div>
                    <ul>
                        <li>memU (云端): ✅ 正常</li>
                        <li>Hippocampus (本地): ✅ 正常</li>
                        <li>MemOS (云端): ✅ 正常</li>
                    </ul>
                </div>
                <div class="card">
                    <div class="card-title">记忆文件</div>
                    <ul>
                        <li>总文件数: {stats['memory_stats']['memory_files']}</li>
                        <li>云端同步: 每2小时</li>
                        <li>QMDR更新: 每小时</li>
                    </ul>
                </div>
            </div>
        </section>
        
        <section id="stats" class="section">
            <h2 class="section-title">📈 系统配置</h2>
            <div class="grid-3">
                <div class="card">
                    <div class="card-title">🚀 并发配置</div>
                    <ul>
                        <li>主会话并发: 30</li>
                        <li>子代理并发: 30</li>
                        <li>API 并发: 20</li>
                        <li>模式: 蜂群并行</li>
                    </ul>
                </div>
                <div class="card">
                    <div class="card-title">🔍 搜索引擎</div>
                    <ul>
                        <li>Tavily AI Search</li>
                        <li>腾讯云 WSA</li>
                        <li>DuckDuckGo</li>
                        <li>Crawl4AI</li>
                    </ul>
                </div>
                <div class="card">
                    <div class="card-title">📱 接入平台</div>
                    <ul>
                        <li>飞书 (主要)</li>
                        <li>Telegram</li>
                        <li>QQ / 钉钉 / 企微</li>
                    </ul>
                </div>
            </div>
        </section>
    </div>
    
    <footer class="footer">
        <p>🥣 BowlWanpi - 一碗的AI助手</p>
        <p style="margin-top: 0.5rem;">v3.0.0 究极完全体 | 最后更新: {stats['date']} {stats['time']}</p>
        <p style="margin-top: 0.5rem; font-size: 0.9rem;">
            <a href="https://github.com/T-Evan/bowlwanpi-docs" style="color: var(--primary);">GitHub</a> |
            <a href="https://my.feishu.cn/wiki/QoUCw9iq1ipHwVkHusVcVTYcneg" style="color: var(--primary);">飞书知识库</a>
        </p>
    </footer>
</body>
</html>'''
    
    return html

def main():
    """主函数"""
    print("🚀 生成 BowlWanpi 网站内容...")
    
    skills = get_skills()
    jobs = get_cron_jobs()
    stats = get_system_stats()
    
    print(f"  - 技能: {len(skills)} 个")
    print(f"  - 定时任务: {len(jobs)} 个")
    print(f"  - 向量嵌入: {stats['memory_stats']['qmd_vectors']}")
    
    html = generate_index_html(stats, skills, jobs)
    
    output_file = DOCS_DIR / "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 网站内容已生成: {output_file}")
    print(f"🌐 https://t-evan.github.io/bowlwanpi-docs/")
    
    return 0

if __name__ == '__main__':
    exit(main())
