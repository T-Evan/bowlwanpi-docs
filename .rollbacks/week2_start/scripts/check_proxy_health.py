#!/usr/bin/env python3
"""
网络代理健康检查脚本
每小时检查 Mihomo 代理状态
"""
import subprocess
import json
import os
from datetime import datetime

PROXY_PORT = 7890
LOG_FILE = '/root/.openclaw/workspace/memory/proxy-health.log'

def check_mihomo_process():
    """检查 Mihomo 进程是否在运行"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'mihomo'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def check_proxy_port():
    """检查代理端口是否可用"""
    try:
        # 测试通过代理访问 Google
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
             '--max-time', '10',
             '--proxy', f'http://127.0.0.1:{PROXY_PORT}',
             'https://www.google.com'],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout.strip() == '200'
    except:
        return False

def get_system_load():
    """获取系统负载"""
    try:
        with open('/proc/loadavg', 'r') as f:
            load = f.read().split()[0]
        return load
    except:
        return 'unknown'

def main():
    """主检查流程"""
    timestamp = datetime.now().isoformat()
    
    # 检查状态
    mihomo_running = check_mihomo_process()
    proxy_working = check_proxy_port()
    load = get_system_load()
    
    status = {
        'timestamp': timestamp,
        'mihomo_running': mihomo_running,
        'proxy_working': proxy_working,
        'port': PROXY_PORT,
        'system_load': load
    }
    
    # 记录日志
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} | Mihomo: {'✅' if mihomo_running else '❌'} | Proxy: {'✅' if proxy_working else '❌'} | Load: {load}\n")
    
    # 如果异常，生成告警
    issues = []
    if not mihomo_running:
        issues.append("❌ Mihomo 进程未运行")
    if not proxy_working:
        issues.append(f"❌ 代理端口 {PROXY_PORT} 不可用")
    
    if issues:
        alert = f"⚠️ 代理健康检查告警\n\n"
        alert += f"时间: {timestamp}\n"
        alert += f"\n".join(issues)
        alert += f"\n\n系统负载: {load}"
        alert += f"\n\n建议: 检查 Mihomo 服务状态，可能需要重启"
        
        # 写入告警文件
        with open('/tmp/bowlwanpi-proxy-alert.txt', 'w') as f:
            f.write(alert)
        
        print(alert)
        return False  # 有异常
    else:
        print(f"✅ 代理健康检查通过 | Load: {load}")
        return True  # 正常

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
