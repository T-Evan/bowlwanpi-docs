#!/usr/bin/env python3
"""
OpenClaw 自检系统 v2.0
全面检查定时任务配置和推送通道

Usage:
  openclaw selfcheck              # 运行完整自检
  openclaw selfcheck --quick      # 快速检查
  openclaw selfcheck --fix        # 检查并尝试修复
  openclaw selfcheck --report     # 生成报告
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional

sys.path.insert(0, '/root/.openclaw/workspace')

# 配置
LOG_FILE = '/root/.openclaw/workspace/memory/self-check.log'
REPORT_FILE = '/tmp/bowlwanpi-selfcheck-report.txt'
CACHE_FILE = '/root/.openclaw/workspace/memory/self-check-cache.json'


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'


class SelfCheckSystem:
    """自检系统主类"""
    
    def __init__(self):
        self.issues = []
        self.fixed = []
        self.manual_required = []
        self.warnings = []
        self.verbose = True
        
    def log(self, message: str, level: str = "INFO", color: str = None):
        """记录日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        color_map = {
            "ERROR": Colors.RED,
            "WARN": Colors.YELLOW,
            "SUCCESS": Colors.GREEN,
            "INFO": Colors.BLUE,
            "CHECK": Colors.CYAN
        }
        
        prefix_color = color or color_map.get(level, Colors.BLUE)
        log_entry = f"{prefix_color}[{timestamp}] [{level}]{Colors.RESET} {message}"
        
        if self.verbose:
            print(log_entry)
        
        # 写入文件
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] [{level}] {message}\n")
    
    # ==================== 定时任务检查 ====================
    
    def check_cron_jobs(self) -> Tuple[bool, str, List[Dict]]:
        """检查所有定时任务配置"""
        issues = []
        details = []
        
        try:
            # 获取 cron 列表
            result = subprocess.run(
                ['openclaw', 'cron', 'list'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                return False, "无法读取 cron 列表", []
            
            output = result.stdout
            
            # 解析任务（简化解析）
            jobs = self._parse_cron_list(output)
            
            self.log(f"发现 {len(jobs)} 个定时任务", "INFO")
            
            for job in jobs:
                job_issues = []
                
                # 检查1: 通道配置
                if job.get('delivery'):
                    channel = job['delivery'].get('channel', '')
                    if channel == 'whatsapp':
                        job_issues.append(f"❌ 使用不支持的 whatsapp 通道")
                    elif channel and channel != 'feishu':
                        job_issues.append(f"⚠️ 使用非飞书通道: {channel}")
                
                # 检查2: sessionTarget 和 payload 类型匹配
                session_target = job.get('sessionTarget', '')
                payload_kind = job.get('payload', {}).get('kind', '')
                
                if session_target == 'main' and payload_kind != 'systemEvent':
                    job_issues.append(f"⚠️ main session 应该使用 systemEvent")
                elif session_target == 'isolated' and payload_kind != 'agentTurn':
                    job_issues.append(f"⚠️ isolated session 应该使用 agentTurn")
                
                # 检查3: 连续错误
                consecutive_errors = job.get('state', {}).get('consecutiveErrors', 0)
                if consecutive_errors > 3:
                    job_issues.append(f"❌ 连续失败 {consecutive_errors} 次")
                elif consecutive_errors > 0:
                    job_issues.append(f"⚠️ 最近有 {consecutive_errors} 次失败")
                
                # 检查4: 任务超时
                last_error = job.get('state', {}).get('lastError', '')
                if 'timeout' in last_error.lower():
                    job_issues.append(f"⚠️ 上次执行超时")
                
                if job_issues:
                    issues.append({
                        'name': job.get('name', 'Unknown'),
                        'id': job.get('id', '')[:8],
                        'issues': job_issues
                    })
                
                details.append({
                    'name': job.get('name'),
                    'enabled': job.get('enabled'),
                    'channel': channel if job.get('delivery') else None,
                    'issues': job_issues
                })
            
            if issues:
                return False, f"发现 {len(issues)} 个任务有问题", details
            return True, f"所有 {len(jobs)} 个任务配置正常", details
            
        except Exception as e:
            return False, f"检查失败: {e}", []
    
    def _parse_cron_list(self, output: str) -> List[Dict]:
        """解析 cron list 输出"""
        jobs = []
        current_job = {}
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测新任务开始
            if line.startswith('"name":'):
                if current_job:
                    jobs.append(current_job)
                current_job = {'name': line.split(':', 1)[1].strip().strip('",')}
            elif line.startswith('"id":') and current_job:
                current_job['id'] = line.split(':', 1)[1].strip().strip('",')
            elif line.startswith('"enabled":') and current_job:
                current_job['enabled'] = 'true' in line.lower()
            elif line.startswith('"sessionTarget":') and current_job:
                current_job['sessionTarget'] = line.split(':', 1)[1].strip().strip('",')
            elif '"channel":' in line and current_job:
                current_job['delivery'] = {'channel': line.split(':', 1)[1].strip().strip('",')}
            elif line.startswith('"kind":') and current_job:
                if 'payload' not in current_job:
                    current_job['payload'] = {}
                current_job['payload']['kind'] = line.split(':', 1)[1].strip().strip('",')
            elif 'consecutiveErrors' in line and current_job:
                try:
                    match = re.search(r'(\d+)', line)
                    if match:
                        if 'state' not in current_job:
                            current_job['state'] = {}
                        current_job['state']['consecutiveErrors'] = int(match.group(1))
                except:
                    pass
            elif 'lastError' in line and current_job:
                if 'state' not in current_job:
                    current_job['state'] = {}
                current_job['state']['lastError'] = line
        
        if current_job:
            jobs.append(current_job)
        
        return jobs
    
    # ==================== 推送脚本检查 ====================
    
    def check_push_scripts(self) -> Tuple[bool, str, List[Dict]]:
        """检查推送脚本中的通道配置"""
        issues = []
        details = []
        
        scripts_dir = Path('/root/.openclaw/workspace/scripts')
        push_scripts = list(scripts_dir.glob('push_*.py'))
        
        self.log(f"检查 {len(push_scripts)} 个推送脚本", "INFO")
        
        for script in push_scripts:
            script_issues = []
            
            try:
                with open(script, 'r') as f:
                    content = f.read()
                
                # 检查是否有硬编码的 whatsapp
                if 'whatsapp' in content.lower():
                    script_issues.append("发现 whatsapp 引用")
                
                # 检查是否有 message 工具调用但没有指定 channel
                if 'message(' in content and 'channel=' not in content:
                    script_issues.append("message 调用未指定 channel")
                
            except Exception as e:
                script_issues.append(f"读取失败: {e}")
            
            if script_issues:
                issues.append({
                    'script': script.name,
                    'issues': script_issues
                })
            
            details.append({
                'script': script.name,
                'issues': script_issues
            })
        
        if issues:
            return False, f"发现 {len(issues)} 个脚本有问题", details
        return True, f"所有 {len(push_scripts)} 个脚本正常", details
    
    # ==================== 系统健康检查 ====================
    
    def check_proxy(self) -> Tuple[bool, str]:
        """检查代理健康"""
        try:
            result = subprocess.run(['pgrep', '-f', 'mihomo'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False, "Mihomo 进程未运行"
            
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
    
    # ==================== 自动修复 ====================
    
    def fix_cron_delivery(self) -> bool:
        """尝试修复定时任务通道配置"""
        self.log("定时任务通道问题需要手动修复", "WARN")
        self.log("建议操作:", "INFO")
        self.log("  1. 运行: openclaw cron list", "INFO")
        self.log("  2. 找到使用 whatsapp 的任务", "INFO")
        self.log("  3. 运行: openclaw cron update <job-id> --remove-delivery", "INFO")
        self.log("  或使用 gateway config 修改配置", "INFO")
        return False
    
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
    
    # ==================== 主流程 ====================
    
    def run_checks(self, auto_fix: bool = False, quick: bool = False):
        """运行检查"""
        self.log("="*60, "INFO", Colors.BLUE)
        self.log("🔍 OpenClaw 自检系统 v2.0", "INFO", Colors.BLUE)
        self.log("="*60, "INFO", Colors.BLUE)
        
        all_checks = [
            ("📋 定时任务配置", self.check_cron_jobs, self.fix_cron_delivery if auto_fix else None),
            ("📜 推送脚本检查", self.check_push_scripts, None),
        ]
        
        if not quick:
            all_checks.extend([
                ("🌐 代理健康", self.check_proxy, self.fix_proxy if auto_fix else None),
                ("💾 磁盘空间", self.check_disk_space, None),
                ("🧠 内存使用", self.check_memory, None),
            ])
        
        for name, check_func, fix_func in all_checks:
            self.log(f"\n🔍 检查: {name}", "CHECK")
            
            # 特殊处理返回多个值的检查
            if name in ["📋 定时任务配置", "📜 推送脚本检查"]:
                ok, msg, details = check_func()
            else:
                ok, msg = check_func()
                details = None
            
            if ok:
                level = "WARN" if "警告" in msg else "SUCCESS"
                self.log(f"✅ {name}: {msg}", level)
            else:
                self.log(f"❌ {name}: {msg}", "ERROR")
                self.issues.append((name, msg))
                
                # 显示详细信息
                if details:
                    for item in details[:3]:  # 只显示前3个
                        if item.get('issues'):
                            self.log(f"   • {item.get('name', item.get('script', 'Unknown'))}", "WARN")
                            for issue in item['issues'][:2]:
                                self.log(f"     - {issue}", "WARN")
                
                if fix_func:
                    self.log(f"🔧 尝试自动修复...", "INFO")
                    if fix_func():
                        self.fixed.append(name)
                    else:
                        self.manual_required.append((name, msg))
                else:
                    self.manual_required.append((name, msg))
        
        self.log("\n" + "="*60, "INFO", Colors.BLUE)
        self.log(f"📊 检查完成", "INFO")
        self.log(f"   问题: {len(self.issues)} | 已修复: {len(self.fixed)} | 需人工: {len(self.manual_required)}", "INFO")
        
        return len(self.manual_required) == 0
    
    def generate_report(self) -> str:
        """生成报告"""
        report_lines = []
        report_lines.append("🔍 OpenClaw 自检报告 v2.0")
        report_lines.append("="*50)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        if not self.issues:
            report_lines.append("✅ 所有检查通过，系统健康！")
            return "\n".join(report_lines)
        
        if self.fixed:
            report_lines.append("✅ 已自动修复:")
            for item in self.fixed:
                report_lines.append(f"  • {item}")
            report_lines.append("")
        
        if self.manual_required:
            report_lines.append("⚠️ 需要人工处理:")
            for name, msg in self.manual_required:
                report_lines.append(f"  • {name}: {msg}")
            report_lines.append("")
        
        if self.warnings:
            report_lines.append("💡 提示:")
            for warning in self.warnings:
                report_lines.append(f"  • {warning}")
            report_lines.append("")
        
        return "\n".join(report_lines)


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(
        description='OpenClaw 自检系统 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # 运行完整自检
  %(prog)s --quick      # 快速检查（只检查配置）
  %(prog)s --fix        # 检查并尝试修复
  %(prog)s --report     # 查看上次报告
        """
    )
    parser.add_argument('--quick', action='store_true', help='快速模式')
    parser.add_argument('--fix', action='store_true', help='自动修复模式')
    parser.add_argument('--report', action='store_true', help='查看报告')
    parser.add_argument('--quiet', action='store_true', help='静默模式')
    
    args = parser.parse_args()
    
    checker = SelfCheckSystem()
    checker.verbose = not args.quiet
    
    if args.report:
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, 'r') as f:
                print(f.read())
        else:
            print("暂无报告，请先运行检查")
        return
    
    # 运行检查
    success = checker.run_checks(
        auto_fix=args.fix,
        quick=args.quick
    )
    
    # 生成报告
    report = checker.generate_report()
    
    with open(REPORT_FILE, 'w') as f:
        f.write(report)
    
    if not args.quiet:
        print("\n" + report)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
