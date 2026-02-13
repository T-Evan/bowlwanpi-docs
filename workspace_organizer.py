#!/usr/bin/env python3
"""
Workspace自动整理工具 🗂️
自动归类零散文件，保持工作区整洁

功能：
- 自动识别文件类型
- 移动到对应目录
- 生成整理报告
- 支持撤销操作
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict


@dataclass
class FileOperation:
    """文件操作记录"""
    source: str
    destination: str
    operation: str
    timestamp: str


class WorkspaceOrganizer:
    """Workspace整理器"""
    
    # 保护文件列表（不移动这些核心文件）
    PROTECTED_FILES = [
        "AGENTS.md",
        "TOOLS.md",
        "BOOTSTRAP.md",
        "MEMORY.md",
        "IDENTITY.md",
        "SOUL.md",
        "USER.md",
        "HEARTBEAT.md",
        "CAPABILITIES.md",
        "QUICK_START.md",
        "REBUILD_CHECKLIST.md",
        "workspace_organizer.py"  # 自己也不能移动
    ]
    FILE_PATTERNS = {
        "scripts": {
            "extensions": [".py", ".sh", ".js", ".ts"],
            "prefixes": ["push_", "check_", "sync_", "rebuild_"],
            "patterns": ["*loop*", "*message*", "*daily*", "*server*"]
        },
        "config": {
            "extensions": [".json", ".yaml", ".yml", ".toml", ".env"],
            "names": ["config", "settings", ".env"]
        },
        "docs": {
            "extensions": [".md", ".txt", ".rst"],
            "patterns": ["README*", "CHANGELOG*", "CONTRIBUTING*"]
        },
        "data": {
            "extensions": [".csv", ".json", ".db", ".sqlite"],
            "patterns": ["*data*", "*backup*"]
        }
    }
    
    def __init__(self, workspace_path: str = None):
        if workspace_path is None:
            self.workspace = Path.home() / ".openclaw/workspace"
        else:
            self.workspace = Path(workspace_path)
        
        self.log_file = self.workspace / ".organizer_log.json"
        self.operations: List[FileOperation] = []
        
    def scan_workspace(self) -> Tuple[Dict[str, List[Path]], List[str]]:
        """扫描workspace，识别需要整理的文件，返回(文件分类, 保护文件列表)"""
        files_to_organize = {
            "scripts": [],
            "config": [],
            "docs": [],
            "data": [],
            "unknown": []
        }
        protected_found = []
        
        # 扫描根目录的文件（不包括子目录）
        for item in self.workspace.iterdir():
            if item.is_file() and not item.name.startswith('.'):
                # 跳过保护文件
                if item.name in self.PROTECTED_FILES:
                    protected_found.append(item.name)
                    continue
                category = self._categorize_file(item)
                files_to_organize[category].append(item)
        
        return files_to_organize, protected_found
    
    def _categorize_file(self, file_path: Path) -> str:
        """分类文件"""
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()
        
        # 检查scripts
        if suffix in self.FILE_PATTERNS["scripts"]["extensions"]:
            for prefix in self.FILE_PATTERNS["scripts"]["prefixes"]:
                if name.startswith(prefix):
                    return "scripts"
            for pattern in self.FILE_PATTERNS["scripts"]["patterns"]:
                if self._match_pattern(name, pattern):
                    return "scripts"
        
        # 检查config
        if suffix in self.FILE_PATTERNS["config"]["extensions"]:
            return "config"
        for config_name in self.FILE_PATTERNS["config"]["names"]:
            if config_name in name:
                return "config"
        
        # 检查docs
        if suffix in self.FILE_PATTERNS["docs"]["extensions"]:
            return "docs"
        
        # 检查data
        if suffix in self.FILE_PATTERNS["data"]["extensions"]:
            return "data"
        
        return "unknown"
    
    def _match_pattern(self, name: str, pattern: str) -> bool:
        """简单模式匹配"""
        pattern = pattern.replace("*", "")
        return pattern in name
    
    def organize(self, dry_run: bool = True) -> Dict:
        """
        执行整理
        
        Args:
            dry_run: 如果为True，只预览不实际移动
        """
        files, protected = self.scan_workspace()
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "protected": protected,
            "moved": [],
            "created_dirs": [],
            "errors": [],
            "summary": {}
        }
        
        for category, file_list in files.items():
            if not file_list or category == "unknown":
                continue
            
            # 创建目标目录
            target_dir = self.workspace / category
            if not target_dir.exists() and not dry_run:
                target_dir.mkdir(exist_ok=True)
                report["created_dirs"].append(str(target_dir))
            
            # 移动文件
            for file_path in file_list:
                target_path = target_dir / file_path.name
                
                # 检查冲突
                if target_path.exists():
                    report["errors"].append({
                        "file": str(file_path),
                        "error": "目标文件已存在"
                    })
                    continue
                
                if dry_run:
                    report["moved"].append({
                        "source": str(file_path),
                        "destination": str(target_path),
                        "status": "预览"
                    })
                else:
                    try:
                        shutil.move(str(file_path), str(target_path))
                        report["moved"].append({
                            "source": str(file_path),
                            "destination": str(target_path),
                            "status": "已移动"
                        })
                        
                        # 记录操作
                        self.operations.append(FileOperation(
                            source=str(file_path),
                            destination=str(target_path),
                            operation="move",
                            timestamp=datetime.now().isoformat()
                        ))
                    except Exception as e:
                        report["errors"].append({
                            "file": str(file_path),
                            "error": str(e)
                        })
        
        # 统计
        for category, moves in [(c, [m for m in report["moved"] 
                                      if c in m["destination"]]) 
                                for c in ["scripts", "config", "docs", "data"]]:
            report["summary"][category] = len(moves)
        
        # 保存日志
        if not dry_run:
            self._save_log()
        
        return report
    
    def _save_log(self):
        """保存操作日志"""
        existing_logs = []
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                existing_logs = json.load(f)
        
        existing_logs.extend([asdict(op) for op in self.operations])
        
        with open(self.log_file, 'w') as f:
            json.dump(existing_logs, f, indent=2)
    
    def undo_last(self) -> List[str]:
        """撤销最后一次操作"""
        if not self.log_file.exists():
            return ["没有可撤销的操作"]
        
        with open(self.log_file, 'r') as f:
            logs = json.load(f)
        
        if not logs:
            return ["没有可撤销的操作"]
        
        # 撤销最后一批操作
        undone = []
        last_timestamp = logs[-1]["timestamp"]
        
        for log in reversed(logs[:]):
            if log["timestamp"] == last_timestamp:
                try:
                    shutil.move(log["destination"], log["source"])
                    undone.append(f"已撤销: {log['destination']} -> {log['source']}")
                    logs.remove(log)
                except Exception as e:
                    undone.append(f"撤销失败: {e}")
        
        # 保存更新后的日志
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        return undone
    
    def print_report(self, report: Dict):
        """打印整理报告"""
        print("\n" + "=" * 60)
        print("🗂️  Workspace整理报告")
        print("=" * 60)
        
        mode = "🔍 预览模式" if report["dry_run"] else "✅ 执行模式"
        print(f"\n{mode}")
        print(f"时间: {report['timestamp']}")
        
        # 显示保护文件
        if report.get("protected"):
            print(f"\n🔒 保护文件 ({len(report['protected'])} 个，已跳过):")
            for fname in report["protected"]:
                print(f"  ✓ {fname}")
        
        if report["created_dirs"]:
            print("\n📁 创建目录:")
            for dir_path in report["created_dirs"]:
                print(f"  + {dir_path}")
        
        if report["moved"]:
            print(f"\n📦 移动文件 ({len(report['moved'])} 个):")
            for move in report["moved"]:
                status_icon = "👁️" if report["dry_run"] else "✓"
                print(f"  {status_icon} {move['source'].split('/')[-1]}")
                print(f"     -> {move['destination']}")
        
        if report["errors"]:
            print(f"\n⚠️  错误 ({len(report['errors'])} 个):")
            for error in report["errors"]:
                print(f"  ✗ {error['file']}: {error['error']}")
        
        print("\n📊 分类统计:")
        for category, count in report["summary"].items():
            if count > 0:
                print(f"  {category}: {count} 个文件")
        
        if not report["dry_run"]:
            print("\n💡 提示: 如需撤销，运行 python3 workspace_organizer.py undo")


def main():
    import sys
    
    organizer = WorkspaceOrganizer()
    
    if len(sys.argv) < 2:
        # 默认预览模式
        print("🔍 扫描Workspace...")
        files, protected = organizer.scan_workspace()
        
        if protected:
            print(f"\n🔒 保护文件 ({len(protected)} 个):")
            for fname in protected:
                print(f"  ✓ {fname}")
        
        print("\n📋 发现以下需要整理的文件:")
        for category, file_list in files.items():
            if file_list:
                print(f"\n{category.upper()} ({len(file_list)} 个):")
                for f in file_list:
                    print(f"  - {f.name}")
        
        print("\n💡 运行 'python3 workspace_organizer.py run' 执行整理")
        print("   运行 'python3 workspace_organizer.py preview' 预览详情")
        return
    
    command = sys.argv[1]
    
    if command == "preview":
        report = organizer.organize(dry_run=True)
        organizer.print_report(report)
    
    elif command == "run":
        # 先预览
        print("🔍 预览模式...")
        preview = organizer.organize(dry_run=True)
        organizer.print_report(preview)
        
        if preview["moved"]:
            print("\n⚡ 是否执行整理? (需要手动确认)")
            print("💡 实际使用时可以去掉确认步骤")
            # 这里可以添加用户确认逻辑
            
            # 执行整理
            print("\n🚀 执行整理...")
            report = organizer.organize(dry_run=False)
            organizer.print_report(report)
    
    elif command == "undo":
        undone = organizer.undo_last()
        print("\n↩️ 撤销操作:")
        for msg in undone:
            print(f"  {msg}")
    
    elif command == "scan":
        files, protected = organizer.scan_workspace()
        
        if protected:
            print(f"\n🔒 保护文件 ({len(protected)} 个):")
            for fname in protected:
                print(f"  ✓ {fname}")
        
        print("\n📊 文件分类:")
        for category, file_list in files.items():
            if file_list:
                print(f"\n{category}: {len(file_list)} 个")
                for f in file_list:
                    print(f"  - {f.name}")
    
    else:
        print("未知命令。可用命令: preview, run, undo, scan")


if __name__ == "__main__":
    main()
