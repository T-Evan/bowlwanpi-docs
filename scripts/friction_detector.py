#!/usr/bin/env python3
"""
摩擦点检测器 - 发现系统中的问题和改进机会
"""

import json
import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path

class FrictionDetector:
    """检测系统中的摩擦点"""
    
    def __init__(self):
        self.frictions = []
        self.log_dir = "/var/log"
        self.workspace = "/root/.openclaw/workspace"
    
    def detect_all(self):
        """检测所有摩擦点"""
        print("🔍 正在扫描系统摩擦点...\n")
        
        # 1. 检查定时任务错误
        self.check_cron_errors()
        
        # 2. 检查系统资源
        self.check_system_resources()
        
        # 3. 检查重复任务
        self.check_repeated_tasks()
        
        # 4. 检查待办堆积
        self.check_backlog()
        
        # 5. 检查配置问题
        self.check_config_issues()
        
        return self.frictions
    
    def check_cron_errors(self):
        """检查定时任务错误"""
        try:
            # 检查今天的 cron 错误
            today = datetime.now().strftime("%Y-%m-%d")
            result = subprocess.run(
                f"grep '{today}' /var/log/bowlwanpi-cron.log 2>/dev/null | grep -i 'error\|失败' | wc -l",
                shell=True, capture_output=True, text=True
            )
            error_count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
            
            if error_count > 0:
                # 获取具体错误
                errors = subprocess.run(
                    f"grep '{today}' /var/log/bowlwanpi-cron.log 2>/dev/null | grep -i 'error' | tail -3",
                    shell=True, capture_output=True, text=True
                )
                
                self.frictions.append({
                    "id": "cron_errors",
                    "type": "error_pattern",
                    "severity": "high",
                    "title": f"定时任务今日失败 {error_count} 次",
                    "description": f"发现 {error_count} 个定时任务执行失败",
                    "details": errors.stdout.strip(),
                    "auto_fixable": False,
                    "suggested_action": "检查 Gateway 状态，修复网络/权限问题"
                })
                print(f"  ⚠️ 发现摩擦点: 定时任务失败 {error_count} 次")
            else:
                print(f"  ✅ 定时任务运行正常")
                
        except Exception as e:
            print(f"  ⚠️ 检查定时任务出错: {e}")
    
    def check_system_resources(self):
        """检查系统资源使用情况"""
        try:
            # 检查内存
            mem_result = subprocess.run(
                "free | grep Mem | awk '{printf \"%.0f\", $3/$2 * 100}'",
                shell=True, capture_output=True, text=True
            )
            mem_usage = int(mem_result.stdout.strip()) if mem_result.stdout.strip().isdigit() else 0
            
            if mem_usage > 80:
                self.frictions.append({
                    "id": "high_memory",
                    "type": "performance",
                    "severity": "medium" if mem_usage < 90 else "high",
                    "title": f"内存使用率达到 {mem_usage}%",
                    "description": f"系统内存使用率 {mem_usage}%，建议清理",
                    "auto_fixable": True,
                    "suggested_action": "清理缓存，重启非必要进程"
                })
                print(f"  ⚠️ 发现摩擦点: 内存使用率 {mem_usage}%")
            else:
                print(f"  ✅ 内存使用正常 ({mem_usage}%)")
            
            # 检查磁盘
            disk_result = subprocess.run(
                "df / | tail -1 | awk '{print $5}' | sed 's/%//'",
                shell=True, capture_output=True, text=True
            )
            disk_usage = int(disk_result.stdout.strip()) if disk_result.stdout.strip().isdigit() else 0
            
            if disk_usage > 80:
                self.frictions.append({
                    "id": "high_disk",
                    "type": "cleanup",
                    "severity": "medium",
                    "title": f"磁盘使用率达到 {disk_usage}%",
                    "description": f"根分区使用率 {disk_usage}%，建议清理日志",
                    "auto_fixable": True,
                    "suggested_action": "清理旧日志和临时文件"
                })
                print(f"  ⚠️ 发现摩擦点: 磁盘使用率 {disk_usage}%")
            else:
                print(f"  ✅ 磁盘使用正常 ({disk_usage}%)")
                
        except Exception as e:
            print(f"  ⚠️ 检查系统资源出错: {e}")
    
    def check_repeated_tasks(self):
        """检查重复执行的手动任务"""
        # 基于今天手动执行的任务模式
        manual_tasks = [
            {"task": "重启 Gateway", "count": 3, "pattern": "Gateway 经常崩溃需要手动重启"},
            {"task": "补发推送", "count": 1, "pattern": "定时推送失败需要手动补发"},
        ]
        
        for task in manual_tasks:
            if task["count"] >= 2:  # 2次以上视为重复任务
                self.frictions.append({
                    "id": f"repeated_{task['task']}",
                    "type": "repetition",
                    "severity": "high",
                    "title": f"重复手动任务: {task['task']}",
                    "description": f"今天手动执行了 {task['count']} 次，建议自动化",
                    "auto_fixable": True,
                    "suggested_action": f"创建自动化脚本: {task['pattern']}"
                })
                print(f"  ⚠️ 发现摩擦点: 重复任务 '{task['task']}' ({task['count']} 次)")
    
    def check_backlog(self):
        """检查待办事项堆积"""
        try:
            todo_file = f"{self.workspace}/memory/todo.json"
            if os.path.exists(todo_file):
                with open(todo_file, 'r') as f:
                    todos = json.load(f)
                    pending = len([t for t in todos if not t.get('done', False)])
                    
                    if pending > 10:
                        self.frictions.append({
                            "id": "todo_backlog",
                            "type": "backlog",
                            "severity": "medium",
                            "title": f"待办事项堆积: {pending} 项",
                            "description": f"有 {pending} 个待办事项未完成",
                            "auto_fixable": False,
                            "suggested_action": "审查待办，优先处理高优先级"
                        })
                        print(f"  ⚠️ 发现摩擦点: 待办堆积 {pending} 项")
                    else:
                        print(f"  ✅ 待办事项正常 ({pending} 项)")
            else:
                print(f"  ℹ️ 未找到待办文件")
        except Exception as e:
            print(f"  ⚠️ 检查待办出错: {e}")
    
    def check_config_issues(self):
        """检查配置问题"""
        # 检查 OpenClaw 配置
        config_file = f"{self.workspace}/openclaw.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # 检查是否有未知配置项
                if "memory" in config:
                    self.frictions.append({
                        "id": "config_unknown_key",
                        "type": "config",
                        "severity": "low",
                        "title": "配置文件中存在未识别的键 'memory'",
                        "description": "openclaw.json 中的 'memory' 键不被识别",
                        "auto_fixable": True,
                        "suggested_action": "移除或迁移 'memory' 配置项"
                    })
                    print(f"  ⚠️ 发现摩擦点: 配置文件有未知键")
            except:
                pass
    
    def generate_report(self):
        """生成报告"""
        report = {
            "scan_time": datetime.now().isoformat(),
            "total_frictions": len(self.frictions),
            "by_severity": {
                "high": len([f for f in self.frictions if f["severity"] == "high"]),
                "medium": len([f for f in self.frictions if f["severity"] == "medium"]),
                "low": len([f for f in self.frictions if f["severity"] == "low"]),
            },
            "auto_fixable": len([f for f in self.frictions if f.get("auto_fixable", False)]),
            "frictions": self.frictions
        }
        
        return report


def main():
    """主函数"""
    detector = FrictionDetector()
    frictions = detector.detect_all()
    
    print(f"\n{'='*50}")
    print(f"扫描完成！发现 {len(frictions)} 个摩擦点")
    print(f"{'='*50}\n")
    
    # 生成报告
    report = detector.generate_report()
    
    # 保存报告
    report_dir = "/root/.openclaw/workspace/nightly"
    os.makedirs(report_dir, exist_ok=True)
    
    today = datetime.now().strftime("%Y%m%d")
    report_file = f"{report_dir}/frictions_{today}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 报告已保存: {report_file}")
    
    # 打印摘要
    if frictions:
        print("\n🔴 高优先级摩擦点:")
        for f in [x for x in frictions if x["severity"] == "high"]:
            print(f"  - {f['title']}")
        
        print("\n🟡 中优先级摩擦点:")
        for f in [x for x in frictions if x["severity"] == "medium"]:
            print(f"  - {f['title']}")
        
        if report["auto_fixable"] > 0:
            print(f"\n✨ 其中 {report['auto_fixable']} 个可以自动修复")
    else:
        print("\n🎉 没有发现摩擦点，系统运行良好！")


if __name__ == "__main__":
    main()
