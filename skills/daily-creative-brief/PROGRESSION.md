# 等级 + 成就一体化系统

已整合为统一进度系统，核心脚本：

- 自动等级成长（XP -> 升级）
- 自动成就解锁
- 自动每日任务 / 每周任务奖励

- `scripts/progression_system.py`：统一管理 XP、等级、成就、连胜
- `scripts/log_creation.py`：记录任务完成并自动奖励
- `dashboard/dashboard_text_report.py`：读取真实进度并展示

## 使用

记录一次任务（自动给 XP、检查升级、解锁成就）：

```bash
python3 skills/daily-creative-brief/scripts/log_creation.py "完成中文热榜增强" --type skill --difficulty 困难
```

查看当前状态：

```bash
python3 skills/daily-creative-brief/scripts/progression_system.py status
```

## XP 规则

- 难度基础分：
  - 简单 +10
  - 普通 +20
  - 困难 +35
  - 史诗 +60
- 类型加成：
  - skill +8
  - auto +6
  - content +4
  - explore +3

## 升级曲线

- Lv1 -> Lv2：100 XP
- 之后每级需求 +50 XP（线性增长）

## 每日/每周任务（自动）

当前内置任务：

- 每日专注：当天完成 3 个任务（+25 XP, +5点）
- 每日精进：当天完成 1 个 skill 任务（+20 XP, +5点）
- 周度建设者：当周完成 10 个任务（+80 XP, +15点）
- 周度挑战：当周完成 3 个困难/史诗任务（+90 XP, +20点）

## 数据文件

- `memory/bowlwanpi-level.json`：等级总档（含 quests 状态）
- `pkm/achievements/progress.json`：成就明细与统计
- `pkm/daily/creations-YYYY-MM-DD.json`：每日任务日志
