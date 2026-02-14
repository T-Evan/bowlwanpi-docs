#!/usr/bin/env python3
"""
BowlWanpi Self-Healing System v2.0
配置驱动 + 重要性评分 + 智能修复
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Any

sys.path.insert(0, '/root/.openclaw/workspace')

# 配置
CONFIG_FILE = '/root/.openclaw/workspace/config/self-healing.json'
LOG_FILE = '/root/.openclaw/workspace/memory/self-healing.log'
REPORT_FILE = '/tmp/bowlwanpi-healing-report.txt'


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'


class ConfigManager:
    """配置管理器 - 从 bilibili-monitor 学习"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 无法加载配置: {e}，使用默认配置")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "checks": {
                "proxy": {"enabled": True, "auto_fix": True, "priority": "high"},
                "disk": {"enabled": True, "auto_fix": True, "priority": "medium"},
                "memory": {"enabled": True, "auto_fix": False, "priority": "medium"},
            },
            "notification": {"on_manual_required": True}
        }
    
    def get_check(self, name: str) -> Dict:
        """获取检查项配置"""
        return self.config.get("checks", {}).get(name, {})
    
    def is_enabled(self, name: str) -> bool:
        """检查项是否启用"""
        return self.get_check(name).get("enabled", True)
    
    def can_auto_fix(self, name: str) -> bool:
        """是否可以自动修复"""
        return self.get_check(name).get("auto_fix", False)
    
    def get_priority(self, name: str) -> str:
        """获取优先级"""
        return self.get_check(name).get("priority", "medium")


class SelfHealingSystem:
    """自愈系统 v2.0 - 应用 hippocampus 的重要性评分理念"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.issues = []  # (name, msg, priority)
        self.fixed = []   # (name, priority)
        self.manual_required = []  # (name, msg, priority)
        self.verbose = True
        
    def log(self, message: str, level: str = "INFO", color: str = None):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        color_map = {
            "ERROR": Colors.RED,
            "WARN": Colors.YELLOW,
            "SUCCESS": Colors.GREEN,
            "INFO": Colors.BLUE,
            "HIGH": Colors.RED,
            "MEDIUM": Colors.YELLOW,
            "LOW": Colors.CYAN
        }
        
        prefix_color = color or color_map.get(level, Colors.BLUE)
        log_entry = f"{prefix_color}[{timestamp}] [{level}]{Colors.RESET} {message}"
        
        if self.verbose:
            print(log_entry)
        
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] [{level}] {message}\n")
    
    def priority_score(self, priority: str) -> float:
        """优先级转分数 - 学习自 hippocampus"""
        scores = {"high": 0.9, "medium": 0.6, "low": 0.3}
        return scores.get(priority, 0.5)
    
    # ==================== 检测项 ====================
    
    def check_proxy(self) -> Tuple[bool, str, str]:
        """检查代理健康"""
        if not self.config.is_enabled("proxy"):
            return True, "已禁用", "low"
        
        try:
            # 检查 Mihomo 进程
            result = subprocess.run(['pgrep', '-f', 'mihomo'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False, "Mihomo 进程未运行", self.config.get_priority("proxy")
            
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
                return False, f"代理连接失败", self.config.get_priority("proxy")
            
            return True, "代理正常", self.config.get_priority("proxy")
        except Exception as e:
            return False, f"检查异常: {e}", self.config.get_priority("proxy")
    
    def fix_proxy(self) -> bool:
        """修复代理"""
        try:
            self.log("尝试重启 Mihomo 服务...", "INFO")
            subprocess.run(['pkill', '-f', 'mihomo'], capture_output=True, timeout=5)
            subprocess.Popen(
                ['/usr/local/bin/mihomo', '-f', '/etc/mihomo/config.yaml'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            import time
            time.sleep(3)
            ok, msg, _ = self.check_proxy()
            if ok:
                self.log("✅ 代理修复成功", "SUCCESS")
                return True
            return False
        except Exception as e:
            self.log(f"❌ 修复异常: {e}", "ERROR")
            return False
    
    def check_disk(self) -> Tuple[bool, str, str]:
        """检查磁盘空间"""
        if not self.config.is_enabled("disk"):
            return True, "已禁用", "low"
        
        try:
            result = subprocess.run(['df', '-h', '/'], 
                                  capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                usage = int(lines[1].split()[4].replace('%', ''))
                cfg = self.config.get_check("disk")
                critical = cfg.get("threshold_critical", 90)
                warning = cfg.get("threshold_warning", 80)
                
                if usage > critical:
                    return False, f"磁盘空间严重不足: {usage}%", "high"
                elif usage > warning:
                    return True, f"磁盘空间警告: {usage}%", "medium"
                return True, f"磁盘空间正常: {usage}%", self.config.get_priority("disk")
        except Exception as e:
            return False, f"检查失败: {e}", self.config.get_priority("disk")
    
    def clean_logs(self) -> bool:
        """清理日志"""
        try:
            self.log("清理旧日志文件...", "INFO")
            cfg = self.config.config.get("auto_fix_actions", {}).get("clean_logs", {})
            keep_days = cfg.get("keep_days", 7)
            max_lines = cfg.get("max_lines", 5000)
            
            cutoff = datetime.now() - timedelta(days=keep_days)
            log_files = [
                '/root/.openclaw/workspace/memory/nightly-build.log',
                '/root/.openclaw/workspace/memory/proxy-health.log',
                '/root/.openclaw/workspace/memory/self-healing.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                    
                    # 保留最近 N 天 + 最多 N 行
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
                        f.writelines(new_lines[-max_lines:])
            
            self.log("✅ 日志清理完成", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"❌ 清理失败: {e}", "ERROR")
            return False
    
    def check_memory(self) -> Tuple[bool, str, str]:
        """检查内存使用"""
        if not self.config.is_enabled("memory"):
            return True, "已禁用", "low"
        
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            total = int(lines[0].split()[1])
            available = int(lines[2].split()[1])
            usage = (total - available) / total * 100
            
            cfg = self.config.get_check("memory")
            critical = cfg.get("threshold_critical", 90)
            warning = cfg.get("threshold_warning", 80)
            
            if usage > critical:
                return False, f"内存使用过高: {usage:.1f}%", "high"
            elif usage > warning:
                return True, f"内存使用警告: {usage:.1f}%", "medium"
            return True, f"内存使用正常: {usage:.1f}%", self.config.get_priority("memory")
        except Exception as e:
            return False, f"检查失败: {e}", self.config.get_priority("memory")
    
    # ==================== 主流程 ====================
    
    def run_checks(self, quick: bool = False):
        """运行检查 - 按优先级排序"""
        self.log("="*60, "INFO", Colors.BLUE)
        self.log("🔧 BowlWanpi Self-Healing System v2.0", "INFO", Colors.BLUE)
        self.log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", "INFO", Colors.BLUE)
        self.log("="*60, "INFO", Colors.BLUE)
        
        # 定义检查项，带优先级
        checks = [
            ("代理健康", self.check_proxy, self.fix_proxy),
            ("磁盘空间", self.check_disk, self.clean_logs),
            ("内存使用", self.check_memory, None),
        ]
        
        # 按优先级排序（高优先级先检查）
        checks.sort(key=lambda x: self.priority_score(self.config.get_priority(x[0].replace("健康", "").replace("空间", "").replace("使用", "").lower())), reverse=True)
        
        for name, check_func, fix_func in checks:
            check_key = name.replace("健康", "").replace("空间", "").replace("使用", "").lower()
            
            if not self.config.is_enabled(check_key):
                continue
            
            priority = self.config.get_priority(check_key)
            self.log(f"\n🔍 检查: {name} [{priority.upper()}]")
            
            ok, msg, actual_priority = check_func()
            
            if ok:
                level = "WARN" if "警告" in msg else "SUCCESS"
                self.log(f"✅ {name}: {msg}", level)
            else:
                self.log(f"❌ {name}: {msg}", "ERROR", Colors.RED)
                self.issues.append((name, msg, actual_priority))
                
                if self.config.can_auto_fix(check_key) and fix_func:
                    self.log(f"🔧 尝试自动修复...", "INFO", Colors.YELLOW)
                    if fix_func():
                        self.fixed.append((name, actual_priority))
                        ok2, msg2, _ = check_func()
                        if ok2:
                            self.log(f"✅ {name} 修复成功", "SUCCESS")
                        else:
                            self.manual_required.append((name, msg2, actual_priority))
                    else:
                        self.manual_required.append((name, msg, actual_priority))
                else:
                    self.manual_required.append((name, msg, actual_priority))
        
        # 按优先级排序问题
        self.manual_required.sort(key=lambda x: self.priority_score(x[2]), reverse=True)
        
        self.log("\n" + "="*60, "INFO", Colors.BLUE)
        self.log(f"📊 检查完成", "INFO")
        self.log(f"   发现问题: {len(self.issues)} | 自动修复: {len(self.fixed)} | 需人工: {len(self.manual_required)}", "INFO")
        
        return len(self.manual_required) == 0
    
    def generate_report(self) -> str:
        """生成报告 - 按优先级分组"""
        if not self.issues:
            return "✅ 所有检查通过，系统健康"
        
        report = "🔧 Self-Healing Report v2.0\n"
        report += "="*40 + "\n\n"
        
        if self.fixed:
            report += "✅ 已自动修复:\n"
            for name, priority in self.fixed:
                report += f"  • [{priority.upper()}] {name}\n"
            report += "\n"
        
        if self.manual_required:
            report += "⚠️ 需要人工处理（按优先级排序）:\n"
            for name, msg, priority in self.manual_required:
                report += f"  • [{priority.upper()}] {name}: {msg}\n"
            report += "\n"
        
        report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        return report


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(description='BowlWanpi Self-Healing System v2.0')
    parser.add_argument('--quick', action='store_true', help='快速模式')
    parser.add_argument('--report', action='store_true', help='生成报告')
    parser.add_argument('--quiet', action='store_true', help='静默模式')
    
    args = parser.parse_args()
    
    healing = SelfHealingSystem()
    healing.verbose = not args.quiet
    
    if args.report:
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, 'r') as f:
                print(f.read())
        else:
            print("暂无报告")
        return
    
    success = healing.run_checks(quick=args.quick)
    report = healing.generate_report()
    
    if report and report != "✅ 所有检查通过，系统健康":
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        if not args.quiet:
            print("\n" + report)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
