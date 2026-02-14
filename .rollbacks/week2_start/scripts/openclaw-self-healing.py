#!/usr/bin/env python3
"""
OpenClaw Self-Healing System
BowlWanpi 自愈系统 - CLI 入口

Usage:
  openclaw healing           # 运行完整检查
  openclaw healing --quick   # 快速检查
  openclaw healing --fix     # 检查并尝试修复
  openclaw healing --report  # 生成报告
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

sys.path.insert(0, '/root/.openclaw/workspace')

# 配置
LOG_FILE = '/root/.openclaw/workspace/memory/self-healing.log'
REPORT_FILE = '/tmp/bowlwanpi-healing-report.txt'
CACHE_FILE = '/root/.openclaw/workspace/memory/self-healing-cache.json'


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


class SelfHealingSystem:
    """自愈系统主类"""
    
    def __init__(self):
        self.issues = []
        self.fixed = []
        self.manual_required = []
        self.verbose = True
        
    def log(self, message: str, level: str = "INFO", color: str = None):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 颜色映射
        color_map = {
            "ERROR": Colors.RED,
            "WARN": Colors.YELLOW,
            "SUCCESS": Colors.GREEN,
            "INFO": Colors.BLUE
        }
        
        prefix_color = color or color_map.get(level, Colors.BLUE)
        log_entry = f"{prefix_color}[{timestamp}] [{level}]{Colors.RESET} {message}"
        
        if self.verbose:
            print(log_entry)
        
        # 同时写入文件
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] [{level}] {message}\n")
    
    # ==================== 检测项 ====================
    
    def check_proxy(self) -> Tuple[bool, str]:
        """检查代理健康"""
        try:
            # 检查 Mihomo 进程
            result = subprocess.run(['pgrep', '-f', 'mihomo'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False, "Mihomo 进程未运行"
            
            # 测试代理连接
            env = os.environ.copy()
            env['http_proxy'] = 'http://127.0.0.1:7890'
            env['https_proxy'] = 'http://127.0.0.1:7890'
            
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                 '--max-time', '10', '--proxy', 'http://127.0.0.1:7890',
                 'https://www.google.com'],
                capture_output=True, text=True, timeout=15, env=env
            )
            
            if result.stdout.strip() != '200':
                return False, f"代理连接失败"
            
            return True, "代理正常"
        except Exception as e:
            return False, f"检查异常: {e}"
    
    def check_disk_space(self) -> Tuple[bool, str]:
        """检查磁盘空间"""
        try:
            result = subprocess.run(['df', '-h', '/'], 
                                  capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                usage = lines[1].split()[4].replace('%', '')
                usage_int = int(usage)
                if usage_int > 90:
                    return False, f"磁盘空间不足: {usage}%"
                elif usage_int > 80:
                    return True, f"磁盘空间警告: {usage}%"
                return True, f"磁盘空间正常: {usage}%"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def check_memory(self) -> Tuple[bool, str]:
        """检查内存使用"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            total = int(lines[0].split()[1])
            available = int(lines[2].split()[1])
            usage = (total - available) / total * 100
            
            if usage > 90:
                return False, f"内存使用过高: {usage:.1f}%"
            elif usage > 80:
                return True, f"内存使用警告: {usage:.1f}%"
            return True, f"内存使用正常: {usage:.1f}%"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def check_openclaw_status(self) -> Tuple[bool, str]:
        """检查 OpenClaw 状态"""
        try:
            result = subprocess.run(
                ['openclaw', 'status'],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return True, "OpenClaw 运行正常"
            return False, "OpenClaw 状态异常"
        except Exception as e:
            return False, f"检查失败: {e}"
    
    # ==================== 自动修复 ====================
    
    def fix_proxy(self) -> bool:
        """尝试修复代理"""
        try:
            self.log("尝试重启 Mihomo 服务...", "INFO")
            subprocess.run(['pkill', '-f', 'mihomo'], capture_output=True, timeout=5)
            subprocess.Popen(
                ['/usr/local/bin/mihomo', '-f', '/etc/mihomo/config.yaml'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            import time
            time.sleep(3)
            ok, msg = self.check_proxy()
            if ok:
                self.log("✅ 代理修复成功", "SUCCESS")
                return True
            else:
                self.log(f"❌ 代理修复失败", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ 修复异常: {e}", "ERROR")
            return False
    
    def clean_logs(self) -> bool:
        """清理旧日志"""
        try:
            self.log("清理旧日志文件...", "INFO")
            # 清理7天前的日志
            cutoff = datetime.now() - timedelta(days=7)
            
            log_files = [
                '/root/.openclaw/workspace/memory/nightly-build.log',
                '/root/.openclaw/workspace/memory/proxy-health.log',
                '/root/.openclaw/workspace/memory/self-healing.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                    
                    # 保留最近7天
                    new_lines = []
                    for line in lines:
                        try:
                            if line.startswith('['):
                                timestamp_str = line[1:].split(']')[0]
                                log_time = datetime.fromisoformat(timestamp_str)
                                if log_time > cutoff:
                                    new_lines.append(line)
                            else:
                                new_lines.append(line)
                        except:
                            new_lines.append(line)
                    
                    with open(log_file, 'w') as f:
                        f.writelines(new_lines[-5000:])
            
            self.log("✅ 日志清理完成", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"❌ 清理失败: {e}", "ERROR")
            return False
    
    # ==================== 主流程 ====================
    
    def check_cron_delivery(self) -> Tuple[bool, str]:
        """检查定时任务通道配置"""
        issues = []
        
        try:
            # 读取 cron 列表（通过 cron list 命令，然后解析文本输出）
            result = subprocess.run(
                ['openclaw', 'cron', 'list'],
                capture_output=True, text=True, timeout=30
            )
            
            # 简单文本解析
            output = result.stdout
            
            # 检查输出中是否有明显错误
            if 'whatsapp' in output.lower():
                issues.append("发现 whatsapp 通道配置")
            
            if result.returncode != 0:
                return False, f"无法读取 cron 列表: 命令返回错误"
            
            # 如果能读取到一些任务信息，说明大部分是正常的
            job_count = output.count('name:')
            
            if issues:
                return False, f"发现 {len(issues)} 个问题: " + "; ".join(issues)
            return True, f"检查约 {job_count} 个任务，通道配置正常"
            
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def run_checks(self, auto_fix: bool = False, quick: bool = False):
        """运行检查"""
        self.log("="*60, "INFO", Colors.BLUE)
        self.log("🔧 OpenClaw Self-Healing System v1.0", "INFO", Colors.BLUE)
        self.log("="*60, "INFO", Colors.BLUE)
        
        checks = [
            ("代理健康", self.check_proxy, self.fix_proxy if auto_fix else None),
            ("磁盘空间", self.check_disk_space, self.clean_logs if auto_fix else None),
            ("内存使用", self.check_memory, None),
            ("定时任务通道", self.check_cron_delivery, None),  # 新增
        ]
        
        if not quick:
            checks.extend([
                ("OpenClaw状态", self.check_openclaw_status, None),
            ])
        
        for name, check_func, fix_func in checks:
            self.log(f"\n🔍 检查: {name}")
            ok, msg = check_func()
            
            if ok:
                level = "WARN" if "警告" in msg else "SUCCESS"
                self.log(f"✅ {name}: {msg}", level)
            else:
                self.log(f"❌ {name}: {msg}", "ERROR")
                self.issues.append((name, msg))
                
                if fix_func:
                    self.log(f"🔧 尝试自动修复...", "INFO")
                    if fix_func():
                        self.fixed.append(name)
                        ok2, msg2 = check_func()
                        if ok2:
                            self.log(f"✅ {name} 修复成功", "SUCCESS")
                        else:
                            self.manual_required.append((name, msg2))
                    else:
                        self.manual_required.append((name, msg))
                else:
                    self.manual_required.append((name, msg))
        
        self.log("\n" + "="*60, "INFO", Colors.BLUE)
        self.log(f"📊 检查完成: 发现 {len(self.issues)} 个问题", "INFO")
        self.log(f"   自动修复: {len(self.fixed)} | 需人工: {len(self.manual_required)}", "INFO")
        
        return len(self.manual_required) == 0
    
    def generate_report(self) -> str:
        """生成报告"""
        if not self.issues:
            return "✅ 所有检查通过，系统健康"
        
        report = "🔧 Self-Healing Report\n"
        report += "="*40 + "\n\n"
        
        if self.fixed:
            report += "✅ 已自动修复:\n"
            for item in self.fixed:
                report += f"  • {item}\n"
            report += "\n"
        
        if self.manual_required:
            report += "⚠️ 需要人工处理:\n"
            for name, msg in self.manual_required:
                report += f"  • {name}: {msg}\n"
            report += "\n"
        
        report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        return report


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(
        description='OpenClaw Self-Healing System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # 运行完整检查
  %(prog)s --quick      # 快速检查
  %(prog)s --fix        # 检查并尝试修复
  %(prog)s --report     # 生成报告
        """
    )
    parser.add_argument('--quick', action='store_true', help='快速模式（跳过耗时检查）')
    parser.add_argument('--fix', action='store_true', help='自动修复模式')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--quiet', action='store_true', help='静默模式')
    
    args = parser.parse_args()
    
    healing = SelfHealingSystem()
    healing.verbose = not args.quiet
    
    if args.report:
        # 读取上次报告
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, 'r') as f:
                print(f.read())
        else:
            print("暂无报告，请先运行检查")
        return
    
    # 运行检查
    success = healing.run_checks(
        auto_fix=args.fix,
        quick=args.quick
    )
    
    # 生成报告
    report = healing.generate_report()
    
    if report and report != "✅ 所有检查通过，系统健康":
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        if not args.quiet:
            print("\n" + report)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
