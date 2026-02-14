#!/usr/bin/env python3
"""
碗皮自愈系统 v1.0
自动检测和修复常见问题
"""

import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# 配置
REPORT_FILE = "/tmp/bowlwanpi-healing-report.txt"
WORKSPACE = "/root/.openclaw/workspace"
MIHOMO_PORT = 7890
DISK_WARNING = 90  # 磁盘使用率警告阈值
MEM_WARNING = 90   # 内存使用率警告阈值

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def check_proxy():
    """检查 Mihomo 代理状态"""
    log("检查代理健康...")
    try:
        # 检查端口是否开放
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             f"http://localhost:{MIHOMO_PORT}"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip() in ["200", "302", "400", "404"]:
            return {"status": "ok", "message": f"Mihomo 代理正常 (端口 {MIHOMO_PORT})"}
        
        # 检查进程是否存在
        ps_result = subprocess.run(
            ["pgrep", "-x", "mihomo"],
            capture_output=True, timeout=2
        )
        if ps_result.returncode == 0:
            return {"status": "warning", "message": "Mihomo 进程存在但端口不响应"}
        else:
            return {"status": "error", "message": "Mihomo 未运行"}
    except Exception as e:
        return {"status": "error", "message": f"检查失败: {str(e)}"}

def restart_proxy():
    """尝试重启 Mihomo 代理"""
    log("尝试重启 Mihomo...")
    try:
        # 杀掉现有进程
        subprocess.run(["pkill", "-x", "mihomo"], capture_output=True, timeout=5)
        time.sleep(1)
        # 启动新进程
        subprocess.Popen(
            ["/usr/local/bin/mihomo", "-d", "/etc/mihomo"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        time.sleep(2)
        return {"status": "fixed", "message": "Mihomo 已重启"}
    except Exception as e:
        return {"status": "error", "message": f"重启失败: {str(e)}"}

def check_disk():
    """检查磁盘空间"""
    log("检查磁盘空间...")
    try:
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            usage = int(parts[4].replace('%', ''))
            return {
                "status": "warning" if usage > DISK_WARNING else "ok",
                "message": f"磁盘使用 {usage}% ({parts[2]} / {parts[1]})",
                "usage": usage
            }
    except Exception as e:
        return {"status": "error", "message": f"检查失败: {str(e)}"}

def check_memory():
    """检查内存使用"""
    log("检查内存使用...")
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        
        mem_total = 0
        mem_available = 0
        for line in lines:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemAvailable:'):
                mem_available = int(line.split()[1])
        
        if mem_total > 0:
            usage = int((1 - mem_available / mem_total) * 100)
            return {
                "status": "warning" if usage > MEM_WARNING else "ok",
                "message": f"内存使用 {usage}%",
                "usage": usage
            }
    except Exception as e:
        return {"status": "error", "message": f"检查失败: {str(e)}"}

def check_cron_jobs():
    """检查定时任务配置"""
    log("检查定时任务...")
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        
        issues = []
        if "isolated" in output.lower() and "conflict" in output.lower():
            issues.append("发现 isolated 冲突")
        if "disabled" in output.lower():
            issues.append("有禁用的任务")
        
        return {
            "status": "warning" if issues else "ok",
            "message": "; ".join(issues) if issues else "定时任务正常"
        }
    except Exception as e:
        return {"status": "error", "message": f"检查失败: {str(e)}"}

def check_tencent_search():
    """检查腾讯云搜索配置"""
    log("检查腾讯云搜索配置...")
    creds_file = f"{WORKSPACE}/secrets/tencent-credentials.json"
    skill_env = f"{WORKSPACE}/skills/intelligent-search/.env"
    
    if os.path.exists(creds_file) or os.path.exists(skill_env):
        return {"status": "ok", "message": "腾讯云搜索配置存在"}
    return {"status": "warning", "message": "腾讯云搜索配置缺失"}

def clean_logs():
    """清理旧日志"""
    log("清理旧日志...")
    try:
        # 清理 /tmp 下的大型日志
        result = subprocess.run(
            ["find", "/tmp", "-name", "*.log", "-size", "+10M", "-mtime", "+3"],
            capture_output=True, text=True, timeout=10
        )
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        cleaned = 0
        for f in files:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                    cleaned += 1
                except:
                    pass
        
        return {
            "status": "fixed" if cleaned > 0 else "ok",
            "message": f"清理了 {cleaned} 个旧日志文件"
        }
    except Exception as e:
        return {"status": "error", "message": f"清理失败: {str(e)}"}

def generate_report(results, fixes, alerts):
    """生成报告"""
    report = []
    report.append("=" * 50)
    report.append(f"🩺 碗皮自愈系统报告")
    report.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 50)
    
    report.append("\n📊 检查结果:")
    for name, result in results.items():
        icon = "✅" if result["status"] == "ok" else "⚠️" if result["status"] == "warning" else "❌"
        report.append(f"  {icon} {name}: {result['message']}")
    
    if fixes:
        report.append("\n🔧 自动修复:")
        for fix in fixes:
            report.append(f"  ✅ {fix}")
    
    if alerts:
        report.append("\n🚨 需要人工处理:")
        for alert in alerts:
            report.append(f"  ❌ {alert}")
    
    report.append("\n" + "=" * 50)
    
    report_text = "\n".join(report)
    
    with open(REPORT_FILE, 'w') as f:
        f.write(report_text)
    
    return report_text

def main():
    log("🩺 自愈系统启动...")
    
    results = {}
    fixes = []
    alerts = []
    
    # 各项检查
    results["代理健康"] = check_proxy()
    results["磁盘空间"] = check_disk()
    results["内存使用"] = check_memory()
    results["定时任务"] = check_cron_jobs()
    results["腾讯云搜索"] = check_tencent_search()
    
    # 自动修复逻辑
    if results["代理健康"]["status"] == "error":
        fix_result = restart_proxy()
        if fix_result["status"] == "fixed":
            fixes.append(fix_result["message"])
            results["代理健康"] = {"status": "ok", "message": "已自动重启"}
        else:
            alerts.append(f"代理无法自动修复: {fix_result['message']}")
    
    # 日志清理
    log_result = clean_logs()
    if log_result["status"] == "fixed":
        fixes.append(log_result["message"])
    
    # 检查警告项
    for name, result in results.items():
        if result["status"] == "warning":
            alerts.append(f"{name}: {result['message']}")
    
    # 生成报告
    report = generate_report(results, fixes, alerts)
    
    # 输出到控制台
    print("\n" + report)
    
    # 返回状态
    if alerts:
        log("⚠️ 有告警需要关注")
        return 1
    elif fixes:
        log("🔧 已自动修复一些问题")
        return 0
    else:
        log("✅ 全部正常")
        return 0

if __name__ == "__main__":
    sys.exit(main())
