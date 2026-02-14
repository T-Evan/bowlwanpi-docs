#!/bin/bash
# BowlWanpi 工作区备份脚本
# 每4小时自动运行，备份所有重要文件到 git

set -e

WORKSPACE="/root/.openclaw/workspace"
BACKUP_LOG="/var/log/bowlwanpi-backup.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 开始备份..." >> "$BACKUP_LOG"

cd "$WORKSPACE"

# 确保重建脚本和检查清单被跟踪
if [ -f "rebuild_bowlwanpi.py" ]; then
    git add rebuild_bowlwanpi.py 2>/dev/null || true
    echo "[$DATE] 添加重建脚本到 git" >> "$BACKUP_LOG"
fi

if [ -f "REBUILD_CHECKLIST.md" ]; then
    git add REBUILD_CHECKLIST.md 2>/dev/null || true
    echo "[$DATE] 添加重建检查清单到 git" >> "$BACKUP_LOG"
fi

# 添加所有变更
git add -A 2>/dev/null || true

# 检查是否有变更需要提交
if git diff --cached --quiet 2>/dev/null; then
    echo "[$DATE] 没有变更需要提交" >> "$BACKUP_LOG"
else
    # 提交变更
    git commit -m "Auto backup: $DATE - 包含重建脚本和检查清单" 2>/dev/null || true
    
    # 推送到远程（如果有配置）
    git push origin main 2>/dev/null || true
    
    echo "[$DATE] 备份完成" >> "$BACKUP_LOG"
fi

# 同时备份到 /clawd-data/workspace-backup/
BACKUP_DIR="/clawd-data/workspace-backup/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 复制关键文件
cp -r "$WORKSPACE/skills" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$WORKSPACE/memory" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$WORKSPACE/secrets" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$WORKSPACE/hooks" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$WORKSPACE/modules" "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$WORKSPACE/scripts" "$BACKUP_DIR/" 2>/dev/null || true

# 复制重建关键文件
cp "$WORKSPACE/rebuild_bowlwanpi.py" "$BACKUP_DIR/" 2>/dev/null || true
cp "$WORKSPACE/REBUILD_CHECKLIST.md" "$BACKUP_DIR/" 2>/dev/null || true
cp "$WORKSPACE/"*.md "$BACKUP_DIR/" 2>/dev/null || true
cp "$WORKSPACE/mcp_config.json" "$BACKUP_DIR/" 2>/dev/null || true

echo "[$DATE] 文件备份到 $BACKUP_DIR" >> "$BACKUP_LOG"

# 清理7天前的备份
find /clawd-data/workspace-backup/ -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true

echo "[$DATE] 备份流程完成" >> "$BACKUP_LOG"
