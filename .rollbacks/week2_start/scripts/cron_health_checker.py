#!/usr/bin/env python3
"""
定时任务健康检查器 - 详细版
深度检查 cron 任务的执行状态、错误模式和成功率
"""

import json
import subprocess
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class CronHealthChecker:
    """详细的定时任务健康检查"""
    
    def __init__(self):
        self.log_file = "/var/log/bowlwanpi-cron.log"
        self.heartbeat_log = "/var/log/bowlwanpi-heartbeat.log"
        self.check_window_hours = 24  # 检查最近24小时
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "tasks": {},
            "errors": [],
            "recommendations": []
        }
    
    def check_all(self):
        """执行所有检查"""
        print("🔍 开始详细定时任务健康检查...\n")
        
        # 1. 检查 cron 服务状态
        self.check_cron_service()
        
        # 2. 分析日志文件
        self.analyze_cron_logs()
        
        # 3. 检查任务执行成功率
        self.check_success_rate()
        
        # 4. 检查错误模式
        self.analyze_error_patterns()
        
        # 5. 检查任务延迟
        self.check_task_delays()
        
        # 6. 检查资源使用
        self.check_resource_usage()
        
        # 7. 检查依赖服务
        self.check_dependencies()
        
        return self.results
    
    def check_cron_service(self):
        """检查 cron 服务状态"""
        print("📋 检查 cron 服务状态...")
        
        try:
            # 检查 cron 进程
            result = subprocess.run(
                ["pgrep", "-x", "cron"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pid = result.stdout.strip()
                self.results["summary"]["cron_running"] = True
                self.results["summary"]["cron_pid"] = pid
                print(f"  ✅ cron 服务运行中 (PID: {pid})")
            else:
                self.results["summary"]["cron_running"] = False
                self.results["errors"].append({
                    "severity": "critical",
                    "message": "cron 服务未运行",
                    "action": "systemctl start cron"
                })
                print("  ❌ cron 服务未运行")
            
            # 检查 crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                jobs = [line for line in result.stdout.split('\n') 
                       if line.strip() and not line.startswith('#')]
                self.results["summary"]["total_cron_jobs"] = len(jobs)
                print(f"  ✅ 找到 {len(jobs)} 个 cron 任务")
            else:
                self.results["summary"]["total_cron_jobs"] = 0
                print("  ⚠️ 无法读取 crontab")
                
        except Exception as e:
            print(f"  ❌ 检查失败: {e}")
    
    def analyze_cron_logs(self):
        """分析 cron 日志"""
        print("\n📊 分析 cron 日志...")
        
        if not os.path.exists(self.log_file):
            print(f"  ⚠️ 日志文件不存在: {self.log_file}")
            return
        
        try:
            # 获取今天的日期
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # 读取日志
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                logs = f.read()
            
            # 统计今天的任务
            today_logs = [line for line in logs.split('\n') 
                         if today in line or yesterday in line]
            
            # 解析任务
            task_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] === (.+?) ==='
            
            tasks = defaultdict(lambda: {
                "runs": 0,
                "success": 0,
                "errors": 0,
                "last_run": None,
                "last_status": None,
                "error_messages": []
            })
            
            for line in today_logs:
                # 检查任务开始
                match = re.search(task_pattern, line)
                if match:
                    timestamp, task_name = match.groups()
                    tasks[task_name]["runs"] += 1
                    tasks[task_name]["last_run"] = timestamp
                    tasks[task_name]["last_status"] = "started"
                
                # 检查错误
                if "ERROR" in line or "error" in line.lower():
                    # 找到最近的任务
                    for task_name in tasks:
                        if task_name in line or (tasks[task_name]["last_status"] == "started"):
                            tasks[task_name]["errors"] += 1
                            tasks[task_name]["error_messages"].append(line)
                            tasks[task_name]["last_status"] = "error"
                            break
                
                # 检查成功完成（假设没有错误就是成功）
                if "完成" in line or "success" in line.lower():
                    for task_name in tasks:
                        if tasks[task_name]["last_status"] == "started":
                            tasks[task_name]["success"] += 1
                            tasks[task_name]["last_status"] = "success"
                            break
            
            self.results["tasks"] = dict(tasks)
            
            # 打印摘要
            total_runs = sum(t["runs"] for t in tasks.values())
            total_errors = sum(t["errors"] for t in tasks.values())
            
            print(f"  📈 今日运行任务: {len(tasks)} 个")
            print(f"  🔄 总执行次数: {total_runs}")
            print(f"  ❌ 错误次数: {total_errors}")
            
            if total_errors > 0:
                print(f"  ⚠️ 错误率: {(total_errors/total_runs*100):.1f}%")
            
            # 详细任务列表
            print("\n  📋 任务详情:")
            for task_name, stats in sorted(tasks.items()):
                status = "✅" if stats["errors"] == 0 else "❌"
                print(f"    {status} {task_name}: 运行 {stats['runs']} 次, 错误 {stats['errors']} 次")
                
        except Exception as e:
            print(f"  ❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()
    
    def check_success_rate(self):
        """检查任务成功率"""
        print("\n📈 检查成功率...")
        
        low_success_tasks = []
        
        for task_name, stats in self.results["tasks"].items():
            if stats["runs"] > 0:
                success_rate = (stats["runs"] - stats["errors"]) / stats["runs"] * 100
                
                if success_rate < 50:
                    severity = "critical"
                elif success_rate < 80:
                    severity = "warning"
                else:
                    severity = "ok"
                
                if severity != "ok":
                    low_success_tasks.append({
                        "task": task_name,
                        "success_rate": success_rate,
                        "severity": severity
                    })
        
        if low_success_tasks:
            print(f"  ⚠️ 发现 {len(low_success_tasks)} 个低成功率任务:")
            for task in low_success_tasks:
                icon = "🔴" if task["severity"] == "critical" else "🟡"
                print(f"    {icon} {task['task']}: {task['success_rate']:.1f}%")
                
                self.results["recommendations"].append({
                    "type": "low_success_rate",
                    "task": task["task"],
                    "rate": task["success_rate"],
                    "action": f"检查 {task['task']} 的执行环境和依赖"
                })
        else:
            print("  ✅ 所有任务成功率正常")
    
    def analyze_error_patterns(self):
        """分析错误模式"""
        print("\n🔍 分析错误模式...")
        
        error_patterns = defaultdict(int)
        
        for task_name, stats in self.results["tasks"].items():
            for error_msg in stats.get("error_messages", []):
                # 提取错误类型
                if "Gateway is not running" in error_msg:
                    error_patterns["Gateway 未运行"] += 1
                elif "timeout" in error_msg.lower():
                    error_patterns["超时"] += 1
                elif "permission" in error_msg.lower() or "权限" in error_msg:
                    error_patterns["权限问题"] += 1
                elif "network" in error_msg.lower() or "连接" in error_msg:
                    error_patterns["网络问题"] += 1
                else:
                    error_patterns["其他错误"] += 1
        
        if error_patterns:
            print("  📊 错误模式统计:")
            for pattern, count in sorted(error_patterns.items(), key=lambda x: -x[1]):
                print(f"    • {pattern}: {count} 次")
                
                if pattern == "Gateway 未运行":
                    self.results["recommendations"].append({
                        "type": "error_pattern",
                        "pattern": pattern,
                        "count": count,
                        "action": "检查 Gateway 自动重启机制，或调整任务执行顺序"
                    })
                elif pattern == "超时":
                    self.results["recommendations"].append({
                        "type": "error_pattern",
                        "pattern": pattern,
                        "count": count,
                        "action": "增加超时时间，或优化任务执行效率"
                    })
        else:
            print("  ✅ 没有发现常见错误模式")
    
    def check_task_delays(self):
        """检查任务执行延迟"""
        print("\n⏰ 检查任务延迟...")
        
        # 理想执行时间 vs 实际执行时间
        expected_times = {
            "网易云日推": "08:00",
            "早晨简报": "08:30",
            "微博热搜": "08:30",
            "Product Hunt": "09:00",
            "知乎热榜": "10:00",
            "B站热门": "12:00",
            "信息收集": "14:00"
        }
        
        delays = []
        
        for task_name, stats in self.results["tasks"].items():
            for expected_name, expected_time in expected_times.items():
                if expected_name in task_name:
                    if stats["last_run"]:
                        actual_time = datetime.strptime(
                            stats["last_run"], 
                            "%Y-%m-%d %H:%M:%S"
                        )
                        expected_hour, expected_min = map(int, expected_time.split(":"))
                        expected_datetime = actual_time.replace(
                            hour=expected_hour, 
                            minute=expected_min, 
                            second=0
                        )
                        
                        delay = (actual_time - expected_datetime).total_seconds() / 60
                        
                        if delay > 5:  # 延迟超过5分钟
                            delays.append({
                                "task": task_name,
                                "expected": expected_time,
                                "actual": actual_time.strftime("%H:%M"),
                                "delay_minutes": int(delay)
                            })
        
        if delays:
            print(f"  ⚠️ 发现 {len(delays)} 个任务延迟:")
            for delay in delays:
                print(f"    • {delay['task']}: 延迟 {delay['delay_minutes']} 分钟")
        else:
            print("  ✅ 任务执行时间正常")
    
    def check_resource_usage(self):
        """检查资源使用"""
        print("\n💾 检查资源使用...")
        
        try:
            # 检查日志文件大小
            if os.path.exists(self.log_file):
                size_mb = os.path.getsize(self.log_file) / (1024 * 1024)
                print(f"  📄 cron 日志大小: {size_mb:.1f} MB")
                
                if size_mb > 100:
                    self.results["recommendations"].append({
                        "type": "resource",
                        "issue": "日志文件过大",
                        "size_mb": size_mb,
                        "action": "清理旧日志或启用日志轮转"
                    })
        except Exception as e:
            print(f"  ⚠️ 无法检查资源: {e}")
    
    def check_dependencies(self):
        """检查依赖服务"""
        print("\n🔗 检查依赖服务...")
        
        dependencies = {
            "OpenClaw Gateway": "openclaw gateway status",
            "Mihomo Proxy": "pgrep -f mihomo",
            "Git": "git --version"
        }
        
        for name, check_cmd in dependencies.items():
            try:
                result = subprocess.run(
                    check_cmd,
                    shell=True,
                    capture_output=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    print(f"  ✅ {name}: 正常")
                else:
                    print(f"  ❌ {name}: 异常")
                    self.results["recommendations"].append({
                        "type": "dependency",
                        "service": name,
                        "action": f"检查 {name} 是否已启动"
                    })
            except Exception as e:
                print(f"  ⚠️ {name}: 检查失败 ({e})")
    
    def generate_report(self):
        """生成详细报告"""
        report_lines = [
            "# 🔍 定时任务健康检查报告\n",
            f"**检查时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**检查窗口:** 最近 {self.check_window_hours} 小时\n\n",
            "## 📊 摘要\n\n"
        ]
        
        summary = self.results["summary"]
        report_lines.append(f"- **cron 服务:** {'✅ 运行中' if summary.get('cron_running') else '❌ 未运行'}\n")
        report_lines.append(f"- **cron 任务数:** {summary.get('total_cron_jobs', 0)} 个\n")
        report_lines.append(f"- **今日运行任务:** {len(self.results['tasks'])} 个\n")
        
        total_errors = sum(t.get("errors", 0) for t in self.results["tasks"].values())
        report_lines.append(f"- **今日错误数:** {total_errors} 次\n\n")
        
        # 任务详情
        if self.results["tasks"]:
            report_lines.append("## 📋 任务执行详情\n\n")
            report_lines.append("| 任务 | 运行次数 | 成功 | 错误 | 状态 |\n")
            report_lines.append("|------|----------|------|------|------|\n")
            
            for task_name, stats in sorted(self.results["tasks"].items()):
                status = "✅" if stats["errors"] == 0 else "❌"
                success = stats["runs"] - stats["errors"]
                report_lines.append(
                    f"| {task_name} | {stats['runs']} | {success} | {stats['errors']} | {status} |\n"
                )
            
            report_lines.append("\n")
        
        # 推荐行动
        if self.results["recommendations"]:
            report_lines.append("## 💡 推荐行动\n\n")
            
            for i, rec in enumerate(self.results["recommendations"], 1):
                report_lines.append(f"{i}. **{rec.get('type', '建议')}**\n")
                if 'task' in rec:
                    report_lines.append(f"   - 任务: {rec['task']}\n")
                if 'action' in rec:
                    report_lines.append(f"   - 建议: {rec['action']}\n")
                report_lines.append("\n")
        else:
            report_lines.append("## 💡 推荐行动\n\n✅ 所有检查通过，暂无建议\n")
        
        return "".join(report_lines)
    
    def save_report(self):
        """保存报告"""
        report_dir = "/root/.openclaw/workspace/health-checks"
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存 JSON
        json_file = f"{report_dir}/cron_health_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # 保存 Markdown
        md_file = f"{report_dir}/cron_health_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())
        
        print(f"\n📄 报告已保存:")
        print(f"   JSON: {json_file}")
        print(f"   Markdown: {md_file}")
        
        return md_file


def main():
    """主函数"""
    checker = CronHealthChecker()
    results = checker.check_all()
    
    # 保存报告
    report_file = checker.save_report()
    
    # 如果发现问题，返回非零退出码
    critical_errors = [e for e in results["errors"] if e.get("severity") == "critical"]
    if critical_errors:
        print(f"\n🔴 发现 {len(critical_errors)} 个严重问题")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
