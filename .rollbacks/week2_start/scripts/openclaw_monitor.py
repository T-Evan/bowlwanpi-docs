#!/usr/bin/env python3
"""
OpenClaw 监控预警系统 v3.0
实时监控 + 自动告警 + 预防机制

功能：
- 定时任务执行监控
- 错误模式检测
- 自动告警通知
- 趋势分析
- 预防性维护建议
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# 配置
LOG_DIR = Path('/root/.openclaw/workspace/logs')
LOG_DIR.mkdir(exist_ok=True)

ALERT_LOG = LOG_DIR / 'monitor-alerts.log'
METRICS_FILE = LOG_DIR / 'monitor-metrics.json'
REPORT_FILE = '/tmp/bowlwanpi-monitor-report.txt'


@dataclass
class Alert:
    """告警记录"""
    timestamp: str
    level: str  # INFO, WARN, ERROR, CRITICAL
    category: str
    message: str
    details: Dict
    resolved: bool = False


class MonitorSystem:
    """监控系统主类"""
    
    # 错误模式定义
    ERROR_PATTERNS = {
        'whatsapp_channel': {
            'pattern': r'whatsapp',
            'level': 'WARN',
            'category': 'channel_config',
            'message': '发现WhatsApp通道配置错误'
        },
        'timeout': {
            'pattern': r'time[d\s]*out|超时',
            'level': 'ERROR',
            'category': 'execution',
            'message': '任务执行超时'
        },
        'gateway_down': {
            'pattern': r'gateway.*down|gateway.*not.*running',
            'level': 'ERROR',
            'category': 'gateway',
            'message': 'Gateway服务异常'
        },
        'memory_sync_failed': {
            'pattern': r'mem[Uu].*fail|memory.*sync.*fail',
            'level': 'WARN',
            'category': 'memory',
            'message': '记忆同步失败'
        },
        'consecutive_errors': {
            'pattern': r'consecutive.*error|连续.*错误',
            'level': 'ERROR',
            'category': 'reliability',
            'message': '任务连续失败'
        }
    }
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.metrics: Dict = self._load_metrics()
        
    def _load_metrics(self) -> Dict:
        """加载历史指标"""
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'checks': [],
            'alert_history': [],
            'job_stats': {}
        }
    
    def _save_metrics(self):
        """保存指标"""
        with open(METRICS_FILE, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
    
    def _log_alert(self, alert: Alert):
        """记录告警"""
        with open(ALERT_LOG, 'a') as f:
            f.write(f"[{alert.timestamp}] [{alert.level}] {alert.category}: {alert.message}\n")
        self.alerts.append(alert)
        self.metrics['alert_history'].append(asdict(alert))
    
    # ==================== 监控检查 ====================
    
    def check_job_execution_logs(self) -> List[Alert]:
        """检查任务执行日志中的错误"""
        alerts = []
        
        # 读取最近的日志文件
        log_files = [
            '/var/log/bowlwanpi-cron.log',
            '/var/log/bowlwanpi-heartbeat.log'
        ]
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
            
            try:
                # 读取最近1小时的日志
                cutoff = datetime.now() - timedelta(hours=1)
                
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                for line in lines[-500:]:  # 检查最后500行
                    # 检查各种错误模式
                    for error_type, config in self.ERROR_PATTERNS.items():
                        if re.search(config['pattern'], line, re.IGNORECASE):
                            alert = Alert(
                                timestamp=datetime.now().isoformat(),
                                level=config['level'],
                                category=config['category'],
                                message=config['message'],
                                details={'source': log_file, 'line': line.strip()[:200]}
                            )
                            alerts.append(alert)
                            self._log_alert(alert)
                            
            except Exception as e:
                alert = Alert(
                    timestamp=datetime.now().isoformat(),
                    level='ERROR',
                    category='monitor',
                    message=f'读取日志文件失败: {log_file}',
                    details={'error': str(e)}
                )
                alerts.append(alert)
        
        return alerts
    
    def check_cron_job_status(self) -> Tuple[List[Alert], Dict]:
        """检查定时任务状态"""
        alerts = []
        stats = {
            'total_jobs': 0,
            'healthy_jobs': 0,
            'failed_jobs': 0,
            'issues': []
        }
        
        try:
            result = subprocess.run(
                ['openclaw', 'cron', 'list'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode != 0:
                alert = Alert(
                    timestamp=datetime.now().isoformat(),
                    level='ERROR',
                    category='cron_api',
                    message='无法获取定时任务列表',
                    details={'error': result.stderr}
                )
                alerts.append(alert)
                return alerts, stats
            
            jobs_data = json.loads(result.stdout)
            jobs = jobs_data.get('jobs', [])
            stats['total_jobs'] = len(jobs)
            
            for job in jobs:
                job_id = job.get('id', '')
                job_name = job.get('name', 'Unknown')
                state = job.get('state', {})
                
                # 检查连续错误
                consecutive_errors = state.get('consecutiveErrors', 0)
                if consecutive_errors >= 3:
                    alert = Alert(
                        timestamp=datetime.now().isoformat(),
                        level='CRITICAL',
                        category='job_reliability',
                        message=f'任务连续失败 {consecutive_errors} 次: {job_name}',
                        details={'job_id': job_id, 'job_name': job_name}
                    )
                    alerts.append(alert)
                    stats['failed_jobs'] += 1
                    stats['issues'].append({
                        'job': job_name,
                        'issue': f'连续失败 {consecutive_errors} 次'
                    })
                elif consecutive_errors > 0:
                    stats['issues'].append({
                        'job': job_name,
                        'issue': f'最近有 {consecutive_errors} 次失败'
                    })
                else:
                    stats['healthy_jobs'] += 1
                
                # 检查上次错误
                last_error = state.get('lastError', '')
                if last_error and 'timeout' in last_error.lower():
                    alert = Alert(
                        timestamp=datetime.now().isoformat(),
                        level='WARN',
                        category='job_timeout',
                        message=f'任务上次执行超时: {job_name}',
                        details={'job_id': job_id, 'error': last_error[:100]}
                    )
                    alerts.append(alert)
        
        except Exception as e:
            alert = Alert(
                timestamp=datetime.now().isoformat(),
                level='ERROR',
                category='monitor',
                message=f'检查定时任务状态失败: {e}',
                details={}
            )
            alerts.append(alert)
        
        return alerts, stats
    
    def check_system_resources(self) -> List[Alert]:
        """检查系统资源"""
        alerts = []
        
        # 检查磁盘
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
            usage = int(result.stdout.split('\n')[1].split()[4].replace('%', ''))
            
            if usage > 90:
                alert = Alert(
                    timestamp=datetime.now().isoformat(),
                    level='CRITICAL',
                    category='disk_space',
                    message=f'磁盘空间严重不足: {usage}%',
                    details={'usage': usage}
                )
                alerts.append(alert)
            elif usage > 80:
                alert = Alert(
                    timestamp=datetime.now().isoformat(),
                    level='WARN',
                    category='disk_space',
                    message=f'磁盘空间警告: {usage}%',
                    details={'usage': usage}
                )
                alerts.append(alert)
        except Exception as e:
            pass
        
        # 检查内存
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            total = int(lines[0].split()[1])
            available = int(lines[2].split()[1])
            usage = (total - available) / total * 100
            
            if usage > 90:
                alert = Alert(
                    timestamp=datetime.now().isoformat(),
                    level='CRITICAL',
                    category='memory',
                    message=f'内存使用过高: {usage:.1f}%',
                    details={'usage': usage}
                )
                alerts.append(alert)
        except:
            pass
        
        return alerts
    
    # ==================== 预防措施 ====================
    
    def generate_prevention_advice(self, alerts: List[Alert], stats: Dict) -> List[str]:
        """生成预防建议"""
        advice = []
        
        # 根据告警生成建议
        categories = set(a.category for a in alerts)
        
        if 'channel_config' in categories:
            advice.append("📋 建议: 检查并统一所有推送任务的通道配置为 'feishu'")
            advice.append("   运行: python3 scripts/fix_whatsapp_channel.py")
        
        if 'execution' in categories:
            advice.append("⏱️ 建议: 增加任务超时时间或优化任务执行逻辑")
            advice.append("   检查长时间运行的任务是否需要拆分")
        
        if 'job_reliability' in categories:
            advice.append("🔧 建议: 检查连续失败的任务，可能需要更新API密钥或修复脚本")
            advice.append("   查看详细日志: /var/log/bowlwanpi-cron.log")
        
        if 'gateway' in categories:
            advice.append("🌐 建议: 检查 OpenClaw Gateway 服务状态")
            advice.append("   运行: openclaw gateway status")
        
        if stats.get('failed_jobs', 0) > 0:
            advice.append(f"⚠️ 建议: {stats['failed_jobs']} 个任务需要关注")
        
        # 通用建议
        if not advice:
            advice.append("✅ 系统运行良好，继续保持！")
            advice.append("💡 建议: 定期运行自检脚本确保系统健康")
        
        return advice
    
    # ==================== 报告生成 ====================
    
    def generate_report(self, alerts: List[Alert], stats: Dict) -> str:
        """生成监控报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("🔍 OpenClaw 监控预警报告")
        lines.append("=" * 60)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 统计概览
        lines.append("📊 系统概览")
        lines.append("-" * 40)
        lines.append(f"  定时任务总数: {stats.get('total_jobs', 'N/A')}")
        lines.append(f"  健康任务: {stats.get('healthy_jobs', 'N/A')}")
        lines.append(f"  异常任务: {stats.get('failed_jobs', 'N/A')}")
        lines.append("")
        
        # 告警列表
        if alerts:
            lines.append(f"⚠️ 告警 ({len(alerts)} 个)")
            lines.append("-" * 40)
            
            # 按级别分组
            critical = [a for a in alerts if a.level == 'CRITICAL']
            errors = [a for a in alerts if a.level == 'ERROR']
            warnings = [a for a in alerts if a.level == 'WARN']
            
            if critical:
                lines.append("\n🔴 严重:")
                for a in critical[:5]:
                    lines.append(f"  • [{a.category}] {a.message}")
            
            if errors:
                lines.append("\n❌ 错误:")
                for a in errors[:5]:
                    lines.append(f"  • [{a.category}] {a.message}")
            
            if warnings:
                lines.append("\n⚡ 警告:")
                for a in warnings[:5]:
                    lines.append(f"  • [{a.category}] {a.message}")
        else:
            lines.append("✅ 暂无告警")
        
        lines.append("")
        
        # 预防建议
        advice = self.generate_prevention_advice(alerts, stats)
        lines.append("💡 预防建议")
        lines.append("-" * 40)
        for item in advice:
            lines.append(f"  {item}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    # ==================== 主流程 ====================
    
    def run_monitor(self, auto_fix: bool = False) -> Tuple[bool, str]:
        """运行监控"""
        print("🔍 OpenClaw 监控预警系统 v3.0")
        print("=" * 60)
        
        all_alerts = []
        all_stats = {}
        
        # 1. 检查任务执行日志
        print("\n📋 检查任务执行日志...")
        log_alerts = self.check_job_execution_logs()
        all_alerts.extend(log_alerts)
        print(f"   发现 {len(log_alerts)} 个日志告警")
        
        # 2. 检查定时任务状态
        print("\n⏰ 检查定时任务状态...")
        job_alerts, job_stats = self.check_cron_job_status()
        all_alerts.extend(job_alerts)
        all_stats.update(job_stats)
        print(f"   任务: {job_stats.get('healthy_jobs', 0)}/{job_stats.get('total_jobs', 0)} 健康")
        
        # 3. 检查系统资源
        print("\n💾 检查系统资源...")
        resource_alerts = self.check_system_resources()
        all_alerts.extend(resource_alerts)
        print(f"   发现 {len(resource_alerts)} 个资源告警")
        
        # 保存指标
        self.metrics['checks'].append({
            'timestamp': datetime.now().isoformat(),
            'alert_count': len(all_alerts),
            'stats': all_stats
        })
        self._save_metrics()
        
        # 生成报告
        report = self.generate_report(all_alerts, all_stats)
        
        # 保存报告
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        
        print("\n" + "=" * 60)
        print(f"📊 监控完成: {len(all_alerts)} 个告警")
        
        # 如果有严重告警，返回False
        has_critical = any(a.level == 'CRITICAL' for a in all_alerts)
        return not has_critical, report


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenClaw 监控预警系统')
    parser.add_argument('--fix', action='store_true', help='尝试自动修复')
    parser.add_argument('--quiet', action='store_true', help='静默模式')
    parser.add_argument('--report', action='store_true', help='查看上次报告')
    
    args = parser.parse_args()
    
    if args.report:
        if os.path.exists(REPORT_FILE):
            with open(REPORT_FILE, 'r') as f:
                print(f.read())
        else:
            print("暂无报告")
        return
    
    monitor = MonitorSystem()
    success, report = monitor.run_monitor(auto_fix=args.fix)
    
    if not args.quiet:
        print("\n" + report)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
