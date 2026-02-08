#!/bin/bash
# 重建脚本保护脚本
# 检查关键重建文件是否存在，如缺失则从备份恢复

WORKSPACE="/root/.openclaw/workspace"
BACKUP="/clawd-data/workspace-backup"
LOG="/var/log/bowlwanpi-rebuild-protection.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] 检查重建脚本..." >> "$LOG"

REBUILD_FILES=(
    "rebuild_bowlwanpi.py"
    "REBUILD_CHECKLIST.md"
)

MISSING=0

for file in "${REBUILD_FILES[@]}"; do
    if [ ! -f "$WORKSPACE/$file" ]; then
        echo "[$DATE] 警告: $file 不存在!" >> "$LOG"
        
        # 尝试从备份恢复
        if [ -f "$BACKUP/$file" ]; then
            cp "$BACKUP/$file" "$WORKSPACE/"
            echo "[$DATE] 已从备份恢复: $file" >> "$LOG"
        else
            echo "[$DATE] 错误: 备份中也没有 $file!" >> "$LOG"
            MISSING=$((MISSING + 1))
        fi
    else
        # 验证文件完整性
        FILE_SIZE=$(stat -c%s "$WORKSPACE/$file" 2>/dev/null || echo "0")
        if [ "$FILE_SIZE" -lt 100 ]; then
            echo "[$DATE] 警告: $file 文件过小 (${FILE_SIZE} bytes)，可能已损坏" >> "$LOG"
            
            # 尝试从备份恢复
            if [ -f "$BACKUP/$file" ]; then
                cp "$BACKUP/$file" "$WORKSPACE/"
                echo "[$DATE] 已从备份恢复: $file" >> "$LOG"
            fi
        fi
    fi
done

if [ $MISSING -eq 0 ]; then
    echo "[$DATE] 所有重建脚本正常" >> "$LOG"
else
    echo "[$DATE] 错误: $MISSING 个重建文件缺失!" >> "$LOG"
fi

# 输出状态（用于监控）
if [ -f "$WORKSPACE/rebuild_bowlwanpi.py" ]; then
    REBUILD_SIZE=$(stat -c%s "$WORKSPACE/rebuild_bowlwanpi.py")
    echo "重建脚本状态: OK (${REBUILD_SIZE} bytes)"
else
    echo "重建脚本状态: MISSING"
    exit 1
fi
