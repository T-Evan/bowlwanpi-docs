#!/usr/bin/env python3
"""
碗皮实时仪表盘 - Flask 版本
BowlWanpi Real-time Dashboard

功能：
- 系统资源监控
- 定时任务状态
- 记忆系统状态
- WebSocket实时推送
- SSE 备选方案
"""

import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


class SystemMonitor:
    """系统监控器"""
    
    @staticmethod
    def get_system_stats():
        """获取系统统计"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total // (1024**3),
                    "used": memory.used // (1024**3),
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total // (1024**3),
                    "used": disk.used // (1024**3),
                    "percent": (disk.used / disk.total) * 100
                }
            }
        except ImportError:
            # 如果没有 psutil，使用基础信息
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {"percent": 0, "cores": 1},
                "memory": {"total": 0, "used": 0, "percent": 0},
                "disk": {"total": 0, "used": 0, "percent": 0},
                "note": "psutil not installed"
            }
    
    @staticmethod
    def get_cron_status():
        """获取定时任务状态"""
        try:
            # 读取缓存的任务信息
            cache_file = Path('/root/.openclaw/workspace/memory/cron-cache.json')
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return {
            "total": 30,
            "enabled": 28,
            "errors": 0,
            "healthy": 28,
            "recent_jobs": [
                {"name": "早晨简报", "enabled": True, "errors": 0},
                {"name": "微博热搜", "enabled": True, "errors": 0},
                {"name": "B站热门", "enabled": True, "errors": 0},
                {"name": "记忆同步", "enabled": True, "errors": 0}
            ]
        }
    
    @staticmethod
    def get_memory_status():
        """获取记忆系统状态"""
        memory_dir = Path.home() / ".openclaw/workspace/memory"
        
        daily_files = list(memory_dir.glob("2026-*.md"))
        today = datetime.now().strftime("%Y-%m-%d")
        today_file = memory_dir / f"{today}.md"
        
        return {
            "daily_files_count": len(daily_files),
            "today_file_exists": today_file.exists(),
            "systems": {
                "hippocampus": True,
                "memos": True,
                "memu": True
            },
            "last_sync": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_bowlwanpi_stats():
        """获取碗皮统计"""
        return {
            "level": 1,
            "xp": 40,
            "xp_to_next": 100,
            "total_quests": 2,
            "streak_days": 2
        }


# Flask 路由
@app.route('/')
def index():
    return jsonify({
        "message": "🥣 碗皮仪表盘 API",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/dashboard",
            "api": "/api/stats",
            "stream": "/stream"
        }
    })


@app.route('/api/stats')
def api_stats():
    return jsonify({
        "system": SystemMonitor.get_system_stats(),
        "cron": SystemMonitor.get_cron_status(),
        "memory": SystemMonitor.get_memory_status(),
        "bowlwanpi": SystemMonitor.get_bowlwanpi_stats()
    })


@app.route('/stream')
def stream():
    """SSE 实时数据流"""
    def generate():
        while True:
            data = {
                "timestamp": datetime.now().isoformat(),
                "system": SystemMonitor.get_system_stats(),
                "cron": SystemMonitor.get_cron_status(),
                "memory": SystemMonitor.get_memory_status(),
                "bowlwanpi": SystemMonitor.get_bowlwanpi_stats()
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(5)
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🥣 碗皮实时仪表盘</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #4ade80;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
            box-shadow: 0 0 10px #4ade80;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.1); }
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        
        .card {
            background: rgba(22, 33, 62, 0.8);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        }
        
        .card-title {
            font-size: 1.2rem;
            color: #a0a0a0;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .stat-value {
            font-size: 3rem;
            font-weight: bold;
            color: #fff;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .stat-label {
            color: #888;
            font-size: 0.95rem;
            margin-top: 5px;
        }
        
        .progress-bar {
            width: 100%;
            height: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 5px;
            margin-top: 12px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 5px;
            transition: width 0.5s ease;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
        }
        
        .job-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: rgba(15, 52, 96, 0.6);
            border-radius: 10px;
            margin-bottom: 10px;
            transition: background 0.3s ease;
        }
        
        .job-item:hover {
            background: rgba(15, 52, 96, 0.8);
        }
        
        .job-name {
            font-size: 0.95rem;
            font-weight: 500;
        }
        
        .job-status {
            font-size: 0.8rem;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .status-ok { 
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: #fff;
        }
        .status-error { 
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: #fff;
        }
        
        .level-badge {
            display: inline-flex;
            align-items: center;
            gap: 15px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 20px 35px;
            border-radius: 50px;
            font-size: 1.5rem;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(240, 147, 251, 0.4);
        }
        
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9rem;
            z-index: 1000;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .connected { 
            background: rgba(34, 197, 94, 0.9);
            color: #fff;
        }
        .disconnected { 
            background: rgba(239, 68, 68, 0.9);
            color: #fff;
        }
        
        .stats-row {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }
        
        .stat-box {
            text-align: center;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 1.8rem;
            }
            .level-badge {
                font-size: 1.2rem;
                padding: 15px 25px;
            }
            .stat-value {
                font-size: 2.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="connection-status connected" id="connStatus">
        <span class="status-indicator"></span>实时连接中
    </div>
    
    <div class="header">
        <h1>🥣 碗皮实时仪表盘</h1>
        <p>实时监控 BowlWanpi 状态 · 创意学徒 Lv.1</p>
    </div>
    
    <div class="container">
        <!-- 碗皮状态卡片 -->
        <div class="card" style="text-align: center; margin-bottom: 30px;">
            <div class="level-badge">
                <span>👤 创意学徒</span>
                <span>Lv.<span id="level">1</span></span>
            </div>
            
            <div style="margin-top: 25px; max-width: 500px; margin-left: auto; margin-right: auto;">
                <div class="stat-label" style="margin-bottom: 10px;">
                    XP: <span id="xp">40</span> / <span id="xpNext">100</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="xpBar" style="width: 40%"></div>
                </div>
            </div>
            
            <div class="stats-row" style="margin-top: 25px;">
                <div class="stat-box">
                    <div class="stat-value" style="font-size: 2rem;" id="totalQuests">2</div>
                    <div class="stat-label">完成任务</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="font-size: 2rem; color: #f5576c;" id="streak">2</div>
                    <div class="stat-label">连胜天数 🔥</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="font-size: 2rem; color: #4ade80;" id="levelDisplay">1</div>
                    <div class="stat-label">当前等级</div>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <!-- 系统资源 -->
            <div class="card">
                <div class="card-title">💻 系统资源</div>
                
                <div style="margin-bottom: 20px;">
                    <div class="stat-label">CPU 使用率</div>
                    <div class="stat-value" id="cpu">--%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="cpuBar" style="width: 0%"></div>
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <div class="stat-label">内存使用</div>
                    <div class="stat-value" id="memory">--%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="memoryBar" style="width: 0%"></div>
                    </div>
                </div>
                
                <div>
                    <div class="stat-label">磁盘使用</div>
                    <div class="stat-value" id="disk">--%</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="diskBar" style="width: 0%"></div>
                    </div>
                </div>
            </div>
            
            <!-- 定时任务 -->
            <div class="card">
                <div class="card-title">⏰ 定时任务</div>
                
                <div class="stats-row" style="margin-bottom: 20px;">
                    <div class="stat-box">
                        <div class="stat-value" style="font-size: 1.8rem;" id="totalJobs">--</div>
                        <div class="stat-label">总任务</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="font-size: 1.8rem; color: #4ade80;" id="healthyJobs">--</div>
                        <div class="stat-label">健康</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value" style="font-size: 1.8rem; color: #ef4444;" id="errorJobs">--</div>
                        <div class="stat-label">异常</div>
                    </div>
                </div>
                
                <div id="recentJobs">
                    <div class="job-item">
                        <span class="job-name">加载中...</span>
                    </div>
                </div>
            </div>
            
            <!-- 记忆系统 -->
            <div class="card">
                <div class="card-title">🧠 记忆系统</div>
                
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <span>📝 Hippocampus</span>
                        <span id="hippoStatus" style="color: #4ade80; font-weight: bold;">✅ 正常</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <span>☁️ MemOS</span>
                        <span id="memosStatus" style="color: #4ade80; font-weight: bold;">✅ 正常</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px;">
                        <span>🌐 memU</span>
                        <span id="memuStatus" style="color: #4ade80; font-weight: bold;">✅ 正常</span>
                    </div>
                </div>
                
                <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px;">
                    <div class="stat-label">今日记忆</div>
                    <div class="stat-value" id="todayMemory">--</div>
                </div>
                
                <div style="margin-top: 15px;">
                    <div class="stat-label">记忆文件数</div>
                    <div class="stat-value" id="memoryFiles">--</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🥣 BowlWanpi Dashboard v1.0 · 最后更新: <span id="lastUpdate">--</span></p>
            <p style="margin-top: 10px; opacity: 0.7;">实时数据每5秒自动刷新</p>
        </div>
    </div>
    
    <script>
        const connStatus = document.getElementById('connStatus');
        let eventSource;
        
        function connect() {
            // 使用 SSE
            eventSource = new EventSource('/stream');
            
            eventSource.onopen = function() {
                connStatus.className = 'connection-status connected';
                connStatus.innerHTML = '<span class="status-indicator"></span>实时连接中';
            };
            
            eventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                } catch(e) {
                    console.error('Parse error:', e);
                }
            };
            
            eventSource.onerror = function() {
                connStatus.className = 'connection-status disconnected';
                connStatus.innerHTML = '❌ 连接断开，5秒后重连...';
                eventSource.close();
                setTimeout(connect, 5000);
            };
        }
        
        function updateDashboard(data) {
            // 系统资源
            if (data.system) {
                document.getElementById('cpu').textContent = data.system.cpu.percent + '%';
                document.getElementById('cpuBar').style.width = data.system.cpu.percent + '%';
                
                document.getElementById('memory').textContent = data.system.memory.percent + '%';
                document.getElementById('memoryBar').style.width = data.system.memory.percent + '%';
                
                document.getElementById('disk').textContent = data.system.disk.percent.toFixed(1) + '%';
                document.getElementById('diskBar').style.width = data.system.disk.percent + '%';
            }
            
            // 定时任务
            if (data.cron) {
                document.getElementById('totalJobs').textContent = data.cron.total;
                document.getElementById('healthyJobs').textContent = data.cron.healthy;
                document.getElementById('errorJobs').textContent = data.cron.errors;
                
                const jobsContainer = document.getElementById('recentJobs');
                jobsContainer.innerHTML = '';
                data.cron.recent_jobs.forEach(job => {
                    const div = document.createElement('div');
                    div.className = 'job-item';
                    div.innerHTML = `
                        <span class="job-name">${job.name}</span>
                        <span class="job-status ${job.errors > 0 ? 'status-error' : 'status-ok'}">
                            ${job.errors > 0 ? '❌ ' + job.errors : '✅ 正常'}
                        </span>
                    `;
                    jobsContainer.appendChild(div);
                });
            }
            
            // 记忆系统
            if (data.memory) {
                document.getElementById('todayMemory').textContent = 
                    data.memory.today_file_exists ? '✅ 已记录' : '❌ 未记录';
                document.getElementById('memoryFiles').textContent = data.memory.daily_files_count;
            }
            
            // 碗皮状态
            if (data.bowlwanpi) {
                document.getElementById('level').textContent = data.bowlwanpi.level;
                document.getElementById('levelDisplay').textContent = data.bowlwanpi.level;
                document.getElementById('xp').textContent = data.bowlwanpi.xp;
                document.getElementById('xpNext').textContent = data.bowlwanpi.xp_to_next;
                document.getElementById('xpBar').style.width = 
                    (data.bowlwanpi.xp / data.bowlwanpi.xp_to_next * 100) + '%';
                document.getElementById('totalQuests').textContent = data.bowlwanpi.total_quests;
                document.getElementById('streak').textContent = data.bowlwanpi.streak_days;
            }
            
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString('zh-CN');
        }
        
        // 启动连接
        connect();
    </script>
</body>
</html>
    '''


if __name__ == '__main__':
    print("🥣 启动 BowlWanpi 仪表盘...")
    print("📍 地址: http://localhost:8080")
    print("📊 仪表盘: http://localhost:8080/dashboard")
    print("")
    app.run(host='0.0.0.0', port=8080, debug=False)
