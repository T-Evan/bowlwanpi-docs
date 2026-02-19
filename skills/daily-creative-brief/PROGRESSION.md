# 等级 + 成就一体化系统

已整合为统一进度系统，核心脚本：

- 自动等级成长（XP -> 升级）
- 自动成就解锁
- 自动每日任务 / 每周任务 / 赛季任务奖励

- `scripts/progression_system.py`：统一管理 XP、等级、称号、成就、连胜、羁绊、任务面板
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

查看任务面板（每日/每周/赛季进度）：

```bash
python3 skills/daily-creative-brief/scripts/progression_system.py quests
```

查看赛季商店与购买：

```bash
python3 skills/daily-creative-brief/scripts/progression_system.py shop
python3 skills/daily-creative-brief/scripts/progression_system.py buy xp_booster
```

查看天赋树与升级：

```bash
python3 skills/daily-creative-brief/scripts/progression_system.py talents
python3 skills/daily-creative-brief/scripts/progression_system.py upgrade-talent social_sync
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
- 连胜加成：
  - 每日连胜额外 +2 XP（上限 +20）

## 升级曲线

- Lv1 -> Lv2：100 XP
- 之后每级需求 +50 XP（线性增长）

## 每日/每周任务（自动）

当前内置任务：

- 每日专注：当天完成 3 个任务（+25 XP, +5点）
- 每日精进：当天完成 1 个 skill 任务（+20 XP, +5点）
- 每日专注：当天完成 3 个任务（+25 XP, +5点）
- 每日精进：当天完成 1 个 skill 任务（+20 XP, +5点）
- 沟通练习：当天完成 2 个 content 任务（+18 XP, +4点）
- 周度建设者：当周完成 10 个任务（+80 XP, +15点）
- 周度挑战：当周完成 3 个困难/史诗任务（+90 XP, +20点）
- 能力进化：当周完成 4 个 skill 任务（+70 XP, +12点）

## 赛季系统（按月）

- 完成赛季任务会获得赛季代币（用于赛季商店）
- 赛季商店当前可购买：XP 增幅芯片、羁绊挂件、连胜护盾
- 每月有商店主题，主题商品会降价（自动切换）
- 连胜护盾已生效：跨天断签时会自动消耗 1 个护盾保住连胜
- 赛季阶位越高，可用天赋点越多（每提升 1 个阶位 +1 天赋点）

- 赛季周期：每自然月（例如 `2026-02`）
- 赛季任务：
  - 赛季耐力赛：60 个任务（+320 XP, +80点）
  - 赛季技能大师：24 个 skill 任务（+280 XP, +70点）
  - 赛季高难挑战：12 个困难/史诗任务（+300 XP, +75点）
- 赛季阶位：根据任务积分自动提升（每 100 任务积分 +1 阶）

## 数据文件

- `memory/bowlwanpi-level.json`：等级总档（含 quests 状态）
- `pkm/achievements/progress.json`：成就明细与统计
- `pkm/daily/creations-YYYY-MM-DD.json`：每日任务日志
