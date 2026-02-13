#!/usr/bin/env python3
"""
Workspace数据备份工具 💾
自动备份重要数据到安全位置

功能：
- 备份记忆文件
- 备份配置
- 备份脚本
- 支持增量备份
- 自动清理旧备份
"""

import json
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


class WorkspaceBackup:
    """Workspace备份管理器"""
    
    # 备份配置
    BACKUP_CONFIG = {
        "memory": {
            "paths": ["memory/", "pkm/"],
            "priority": "high"
        },
        "config": {
            "paths": ["config/", "secrets/"],
            "priority": "high"
        },
        "scripts": {
            "paths": ["scripts/"],
            "priority": "medium"
        },
        "skills": {
            "paths": ["skills/"],
            "priority": "medium"
        }
    }
    
    def __init__(self, workspace_path: str = None, backup_dir: str = None):
        if workspace_path is None:
            self.workspace = Path.home() / ".openclaw/workspace"
        else:
            self.workspace = Path(workspace_path)
        
        if backup_dir is None:
            self.backup_dir = Path.home() / ".openclaw/backups"
        else:
            self.backup_dir = Path(backup_dir)
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self, backup_type: str = "full") -> Dict:
        """
        创建备份
        
        Args:
            backup_type: 'full' 或 'incremental'
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"workspace_{backup_type}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        report = {
            "timestamp": timestamp,
            "type": backup_type,
            "backup_path": str(backup_path),
            "files_backed_up": 0,
            "size_mb": 0,
            "items": []
        }
        
        # 执行备份
        for category, config in self.BACKUP_CONFIG.items():
            for path_pattern in config["paths"]:
                source = self.workspace / path_pattern
                if source.exists():
                    dest = backup_path / category / path_pattern.replace("/", "")
                    
                    if source.is_file():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, dest)
                        report["items"].append({
                            "source": str(source),
                            "dest": str(dest),
                            "type": "file"
                        })
                    elif source.is_dir():
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(source, dest)
                        file_count = len(list(dest.rglob("*")))
                        report["items"].append({
                            "source": str(source),
                            "dest": str(dest),
                            "type": "directory",
                            "file_count": file_count
                        })
                        report["files_backed_up"] += file_count
        
        # 创建备份元数据
        metadata = {
            "created_at": datetime.now().isoformat(),
            "type": backup_type,
            "workspace_path": str(self.workspace),
            "items_count": len(report["items"]),
            "files_count": report["files_backed_up"]
        }
        
        with open(backup_path / "backup_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # 计算备份大小
        total_size = sum(
            f.stat().st_size for f in backup_path.rglob("*") if f.is_file()
        )
        report["size_mb"] = round(total_size / (1024 * 1024), 2)
        
        return report
    
    def create_archive(self, backup_path: Path) -> Path:
        """创建压缩归档"""
        archive_path = Path(str(backup_path) + ".tar.gz")
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(backup_path, arcname=backup_path.name)
        
        # 删除原文件夹，保留压缩包
        shutil.rmtree(backup_path)
        
        return archive_path
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        backups = []
        
        for item in self.backup_dir.iterdir():
            if item.name.startswith("workspace_"):
                # 检查是否有元数据
                metadata_file = item / "backup_metadata.json" if item.is_dir() else None
                
                backup_info = {
                    "name": item.name,
                    "path": str(item),
                    "created": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                    "size_mb": 0
                }
                
                # 计算大小
                if item.is_dir():
                    total_size = sum(
                        f.stat().st_size for f in item.rglob("*") if f.is_file()
                    )
                    backup_info["size_mb"] = round(total_size / (1024 * 1024), 2)
                    
                    if metadata_file and metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            backup_info["type"] = metadata.get("type", "unknown")
                            backup_info["files_count"] = metadata.get("files_count", 0)
                elif item.suffix == ".gz":
                    backup_info["size_mb"] = round(item.stat().st_size / (1024 * 1024), 2)
                    backup_info["type"] = "archive"
                
                backups.append(backup_info)
        
        # 按时间排序
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    def restore_backup(self, backup_name: str, target_path: str = None) -> bool:
        """
        恢复备份
        
        Args:
            backup_name: 备份名称
            target_path: 恢复目标路径，默认覆盖当前workspace
        """
        if target_path is None:
            target_path = self.workspace
        else:
            target_path = Path(target_path)
        
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            print(f"❌ 备份不存在: {backup_name}")
            return False
        
        # 如果是压缩包，先解压
        if backup_path.suffix == ".gz":
            print("📦 解压备份...")
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(self.backup_dir)
            backup_path = backup_path.with_suffix('').with_suffix('')
        
        # 恢复文件
        restored_count = 0
        for category_dir in backup_path.iterdir():
            if category_dir.is_dir() and category_dir.name != "backup_metadata.json":
                for item in category_dir.iterdir():
                    target = target_path / item.name
                    
                    if target.exists():
                        if target.is_dir():
                            shutil.rmtree(target)
                        else:
                            target.unlink()
                    
                    if item.is_dir():
                        shutil.copytree(item, target)
                    else:
                        shutil.copy2(item, target)
                    
                    restored_count += 1
        
        print(f"✅ 恢复完成: {restored_count} 个项目")
        return True
    
    def cleanup_old_backups(self, keep_days: int = 7) -> List[str]:
        """
        清理旧备份
        
        Args:
            keep_days: 保留最近几天的备份
        """
        deleted = []
        cutoff = datetime.now() - timedelta(days=keep_days)
        
        for item in self.backup_dir.iterdir():
            if item.name.startswith("workspace_"):
                item_time = datetime.fromtimestamp(item.stat().st_mtime)
                if item_time < cutoff:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    deleted.append(item.name)
        
        return deleted
    
    def print_status(self):
        """打印备份状态"""
        print("\n" + "=" * 60)
        print("💾 Workspace备份状态")
        print("=" * 60)
        
        print(f"\n📁 备份目录: {self.backup_dir}")
        print(f"🎯 工作区: {self.workspace}")
        
        backups = self.list_backups()
        
        if backups:
            print(f"\n📦 备份列表 ({len(backups)} 个):")
            for i, backup in enumerate(backups[:5], 1):  # 只显示最近5个
                print(f"\n  {i}. {backup['name']}")
                print(f"     时间: {backup['created'][:19]}")
                print(f"     大小: {backup['size_mb']} MB")
                if 'type' in backup:
                    print(f"     类型: {backup['type']}")
                if 'files_count' in backup:
                    print(f"     文件: {backup['files_count']} 个")
        else:
            print("\n📭 暂无备份")
        
        # 计算总大小
        total_size = sum(b["size_mb"] for b in backups)
        print(f"\n💾 总占用空间: {total_size:.2f} MB")


def main():
    import sys
    
    backup = WorkspaceBackup()
    
    if len(sys.argv) < 2:
        backup.print_status()
        print("\n💡 可用命令:")
        print("  backup full       - 创建完整备份")
        print("  backup incremental - 创建增量备份")
        print("  list              - 列出所有备份")
        print("  restore <name>   - 恢复指定备份")
        print("  cleanup [days]    - 清理旧备份（默认保留7天）")
        return
    
    command = sys.argv[1]
    
    if command == "backup":
        backup_type = sys.argv[2] if len(sys.argv) > 2 else "full"
        print(f"🚀 创建{backup_type}备份...")
        report = backup.create_backup(backup_type)
        
        print(f"\n✅ 备份完成!")
        print(f"   位置: {report['backup_path']}")
        print(f"   项目: {len(report['items'])} 个")
        print(f"   文件: {report['files_backed_up']} 个")
        print(f"   大小: {report['size_mb']} MB")
        
        # 询问是否压缩
        print("\n📦 是否创建压缩归档? (实际使用时可以自动压缩)")
        
    elif command == "list":
        backup.print_status()
    
    elif command == "restore" and len(sys.argv) > 2:
        backup_name = sys.argv[2]
        print(f"🔄 恢复备份: {backup_name}")
        if backup.restore_backup(backup_name):
            print("✅ 恢复成功")
        else:
            print("❌ 恢复失败")
    
    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        print(f"🧹 清理{days}天前的备份...")
        deleted = backup.cleanup_old_backups(days)
        if deleted:
            print(f"✅ 已删除 {len(deleted)} 个旧备份:")
            for name in deleted:
                print(f"   - {name}")
        else:
            print("📭 没有需要清理的备份")
    
    else:
        print("未知命令")


if __name__ == "__main__":
    main()
