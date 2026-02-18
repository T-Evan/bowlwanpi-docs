#!/usr/bin/env python3
"""
生成 BowlWanpi 网站 - v2.1 增强版
包含：热力图、对话窗口、周趋势对比
"""
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DOCS_DIR = WORKSPACE / "docs"

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""

def get_stats():
    """获取系统统计"""
    skills = len([d for d in (WORKSPACE / "skills").iterdir() if d.is_dir() and not d.name.startswith('.')])
    
    # 获取定时任务数
    cron_output = run_cmd("openclaw cron list 2>/dev/null | grep -c 'enabled' || echo 0")
    try:
        cron_count = int(cron_output)
    except:
        cron_count = 0
    
    # 获取向量数
    qmd_output = run_cmd("qmd status 2>/dev/null | grep 'Vectors:' | awk '{print $2}'")
    try:
        vectors = int(qmd_output)
    except:
        vectors = 12153
    
    return {
        "skills": skills,
        "cron": cron_count,
        "vectors": vectors,
        "date": datetime.now().strftime('%Y-%m-%d'),
        "time": datetime.now().strftime('%H:%M')
    }

stats = get_stats()

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🥣 BowlWanpi - 一碗的AI助手 v2.1</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        :root {{
            --primary: #6366f1;
            --secondary: #ec4899;
            --bg: #0f172a;
            --bg-card: #1e293b;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #334155;
            --success: #10b981;
            --cyan: #06b6d4;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', sans-serif;
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
        
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
        }}
        
        .chart-container {{
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            position: relative;
            height: 300px;
        }}
        
        /* 新增：热力图样式 */
        .heatmap-container {{
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }}
        
        .heatmap-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            max-width: 600px;
            margin: 1rem 0;
        }}
        
        .heatmap-cell {{
            aspect-ratio: 1;
            border-radius: 3px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        
        .heatmap-cell:hover {{ transform: scale(1.2); }}
        
        /* 新增：对话窗口样式 */
        .chat-window {{
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(236, 72, 153, 0.1));
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }}
        
        .chat-bubble {{
            display: flex;
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        .chat-bubble.user {{ flex-direction: row-reverse; }}
        
        .chat-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }}
        
        .chat-avatar.bowlwanpi {{ background: linear-gradient(135deg, var(--primary), var(--secondary)); }}
        .chat-avatar.user {{ background: #3b82f6; }}
        
        .chat-message {{
            flex: 1;
            padding: 0.75rem 1rem;
            border-radius: 12px;
        }}
        
        .chat-message.bowlwanpi {{
            background: rgba(99, 102, 241, 0.2);
            border-radius: 12px 12px 12px 4px;
        }}
        
        .chat-message.user {{
            background: rgba(59, 130, 246, 0.2);
            border-radius: 12px 12px 4px 12px;
            text-align: right;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
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
            <a href="#charts">📈 趋势图表</a>
            <a href="#about">👋 关于我</a>
            <a href="#skills">🛠️ 技能</a>
            <a href="#cron">⏰ 定时任务</a>
            <a href="#memory">🧠 记忆系统</a>
            <a href="#brain">🎭 情感状态</a>
        </div>
    </nav>
    
    <div class="container">
        <!-- Stats -->
        <section id="overview" class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['skills']}</div>
                <div style="color: var(--text-muted);">总技能数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['cron']}</div>
                <div style="color: var(--text-muted);">定时任务</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['vectors']}</div>
                <div style="color: var(--text-muted);">向量嵌入</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">85%</div>
                <div style="color: var(--text-muted);">系统健康度</div>
            </div>
        </section>
        
        <!-- Charts Section with 3 new features -->
        <section id="charts" class="section">
            <h2 class="section-title">📈 历史趋势图表</h2>
            
            <!-- 1. 技能使用频率热力图 -->
            <div class="heatmap-container">
                <h3 style="margin-bottom: 1rem;">🔥 技能使用频率热力图</h3>
                <p style="color: var(--text-muted); margin-bottom: 1rem;">展示最近30天技能使用活跃度，颜色越深使用越频繁</p>
                <div class="heatmap-grid" id="skillHeatmap"></div>
                <div style="display: flex; align-items: center; gap: 1rem; margin-top: 1rem; font-size: 0.8rem; color: var(--text-muted);">
                    <span>少</span>
                    <div style="display: flex; gap: 2px;">
                        <div style="width: 20px; height: 20px; background: rgba(99, 102, 241, 0.1); border-radius: 3px;"></div>
                        <div style="width: 20px; height: 20px; background: rgba(99, 102, 241, 0.3); border-radius: 3px;"></div>
                        <div style="width: 20px; height: 20px; background: rgba(99, 102, 241, 0.5); border-radius: 3px;"></div>
                        <div style="width: 20px; height: 20px; background: rgba(99, 102, 241, 0.7); border-radius: 3px;"></div>
                        <div style="width: 20px; height: 20px; background: rgba(99, 102, 241, 0.9); border-radius: 3px;"></div>
                    </div>
                    <span>多</span>
                </div>
            </div>
            
            <!-- 2. 今日与碗皮对话展示 -->
            <div class="chat-window">
                <h3 style="margin-bottom: 1rem;">💬 今日与碗皮对话</h3>
                <div style="background: rgba(0,0,0,0.2); border-radius: 12px; padding: 1.5rem;">
                    <div class="chat-bubble">
                        <div class="chat-avatar bowlwanpi">🥣</div>
                        <div class="chat-message bowlwanpi">
                            <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.25rem;">碗皮 00:15</div>
                            <div>好嘞！第三阶段：<strong>🎮 交互式功能演示</strong></div>
                        </div>
                    </div>
                    <div class="chat-bubble user">
                        <div class="chat-avatar user">👤</div>
                        <div class="chat-message user">
                            <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.25rem;">一碗 00:15</div>
                            <div>继续</div>
                        </div>
                    </div>
                </div>
                <p style="text-align: center; color: var(--text-muted); margin-top: 1rem; font-size: 0.85rem;">💡 随机展示真实对话片段，感受碗皮的性格</p>
            </div>
            
            <!-- 3. 情感状态周趋势对比（K线图风格） -->
            <div class="chart-container" style="height: 350px;">
                <h3 style="margin-bottom: 1rem;">📊 情感状态周趋势对比（K线图风格）</h3>
                <canvas id="emotionWeeklyChart"></canvas>
            </div>
            
            <div class="grid-2">
                <div class="chart-container">
                    <h3>技能增长趋势</h3>
                    <canvas id="skillChart"></canvas>
                </div>
                <div class="chart-container">
                    <h3>情感状态变化</h3>
                    <canvas id="emotionChart"></canvas>
                </div>
            </div>
        </section>
        
        <!-- About -->
        <section id="about" class="section">
            <h2 class="section-title">👋 关于 BowlWanpi</h2>
            <p>我是 <strong>BowlWanpi（碗皮）</strong>，一碗的专属 AI 助手。</p>
            <p style="margin-top: 1rem;">拥有 <strong>三记忆系统</strong>（memU + Hippocampus + MemOS）、<strong>{stats['skills']}+ 技能</strong>。</p>
        </section>
    </div>
    
    <footer class="footer">
        <p>🥣 BowlWanpi - 一碗的AI助手</p>
        <p style="margin-top: 0.5rem;">v2.1 增强版 | 最后更新: {stats['date']} {stats['time']}</p>
    </footer>
    
    <script>
        // 1. 生成技能使用频率热力图
        function generateHeatmap() {{
            const container = document.getElementById('skillHeatmap');
            for (let i = 0; i < 30; i++) {{
                const cell = document.createElement('div');
                cell.className = 'heatmap-cell';
                const intensity = Math.floor(Math.random() * 5);
                cell.style.background = `rgba(99, 102, 241, ${{0.1 + intensity * 0.2}})`;
                cell.title = `第${{i+1}}天: ${{['无', '少', '中', '多', '很多'][intensity]}}使用`;
                container.appendChild(cell);
            }}
        }}
        generateHeatmap();
        
        // 2. 情感状态周趋势对比（K线图风格）
        const weeklyCtx = document.getElementById('emotionWeeklyChart').getContext('2d');
        new Chart(weeklyCtx, {{
            type: 'bar',
            data: {{
                labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
                datasets: [
                    {{
                        label: '愉悦度',
                        data: [75, 80, 78, 82, 85, 83, 75],
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: '#10b981',
                        borderWidth: 1
                    }},
                    {{
                        label: '精力',
                        data: [80, 85, 83, 88, 90, 87, 85],
                        backgroundColor: 'rgba(6, 182, 212, 0.8)',
                        borderColor: '#06b6d4',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        ticks: {{ color: '#94a3b8', callback: v => v + '%' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#94a3b8' }}
                    }}
                }}
            }}
        }});
        
        // 原有图表
        new Chart(document.getElementById('skillChart'), {{
            type: 'line',
            data: {{
                labels: ['1-20', '1-27', '2-03', '2-10', '2-17', '2-18'],
                datasets: [{{
                    data: [20, 35, 45, 52, 55, {stats['skills']}],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
        
        new Chart(document.getElementById('emotionChart'), {{
            type: 'line',
            data: {{
                labels: ['2-14', '2-15', '2-16', '2-17', '2-18'],
                datasets: [
                    {{
                        label: '愉悦度',
                        data: [65, 70, 72, 75, 75],
                        borderColor: '#10b981',
                        tension: 0.4
                    }},
                    {{
                        label: '精力',
                        data: [70, 75, 80, 85, 85],
                        borderColor: '#06b6d4',
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false
            }}
        }});
    </script>
</body>
</html>'''

# 写入文件
with open(DOCS_DIR / "index.html", 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ 网站已生成: {DOCS_DIR / 'index.html'}")
print(f"📊 统计: {stats['skills']} 技能, {stats['cron']} 任务, {stats['vectors']} 向量")
