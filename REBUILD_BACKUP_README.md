# 重建脚本备份说明

## 📦 重建关键文件

以下文件是重建 BowlWanpi 的关键，已加入定时备份：

| 文件 | 位置 | 备份位置 | 说明 |
|------|------|----------|------|
| rebuild_bowlwanpi.py | workspace/ | /clawd-data/workspace-backup/ | 完整重建脚本 |
| REBUILD_CHECKLIST.md | workspace/ | /clawd-data/workspace-backup/ | 重建检查清单 |
| verify-rebuild-scripts.sh | workspace/scripts/ | /clawd-data/workspace-backup/scripts/ | 重建脚本验证工具 |
| backup.sh | workspace/scripts/ | /clawd-data/workspace-backup/scripts/ | 备份脚本 |

## 🔄 备份策略

### 定时备份
- **频率**: 每4小时
- **方式**: System Cron (/etc/cron.d/workspace-backup)
- **脚本**: /clawd-data/backup-workspace.sh
- **目标**: /clawd-data/workspace-backup/

### 特殊处理
- 重建脚本会额外备份到 `rebuild-scripts/YYYYMMDD/` 目录
- 保留30天的重建脚本历史版本
- 自动验证脚本完整性

### Git 备份
- 夜间构建时自动 git commit
- 提交信息包含 "包含重建脚本和检查清单"

## 🛡️ 保护措施

### 自动验证
- 脚本: `scripts/verify-rebuild-scripts.sh`
- 运行: 夜间构建时自动检查
- 功能:
  - 检查重建脚本是否存在
  - 验证文件完整性（文件大小）
  - 如缺失或损坏，从备份自动恢复

### 恢复方法

如果重建脚本丢失或损坏：

```bash
# 方法1: 从备份恢复
cp /clawd-data/workspace-backup/rebuild_bowlwanpi.py ~/.openclaw/workspace/
cp /clawd-data/workspace-backup/REBUILD_CHECKLIST.md ~/.openclaw/workspace/

# 方法2: 运行验证脚本（自动恢复）
~/.openclaw/workspace/scripts/verify-rebuild-scripts.sh

# 方法3: 从 git 历史恢复
cd ~/.openclaw/workspace
git log --oneline --all -- rebuild_bowlwanpi.py
git checkout <commit> -- rebuild_bowlwanpi.py
```

## ☁️ 云端记忆备份

重建脚本的核心信息也已存储到云端记忆系统：

- **memU**: 重建手册摘要
- **Hippocampus**: 最高重要度存储
- **MemOS**: 快速检索备份

即使本地和备份盘都损坏，仍可从云端记忆获取重建信息。

## 📋 重建检查清单

完整的重建步骤见: `REBUILD_CHECKLIST.md`

---

**创建时间**: 2026-02-08  
**最后更新**: 2026-02-08
