---
name: novelai-umaru
description: 智能小埋角色生图系统，支持自然语言场景动作分析、自动组合提示词、NovelAI 生成与飞书推送。
version: 1.0.0
metadata:
  openclaw:
    emoji: 🐹
    requires:
      bins:
        - python3
      python_packages:
        - requests
    homepage: https://novelai.net
---

# NovelAI Umaru 智能生图技能

## 功能说明

- 根据中文输入自动识别`场景`和`动作`
- 自动拼接基础提示词 + 角色提示词 + 动态提示词
- 调用 NovelAI API 生成图片并保存
- 可选发送生成结果到飞书机器人 webhook

## 目录结构

```text
novelai-umaru/
├── SKILL.md
├── config.json
├── modules/
│   ├── __init__.py
│   ├── context_analyzer.py
│   ├── prompt_combiner.py
│   └── smart_generator.py
├── scripts/
│   └── smart_generate.py
└── data/
    └── outputs/
```

## 配置

编辑 `config.json`：

- `api_key`: NovelAI API Key（必填）
- `base_prompt` / `negative_prompt`: 全局提示词
- `character`: 角色信息和默认姿态
- `context_mapping`: 中文关键词到英文提示词映射
- `defaults`: 生图参数
- `feishu.enabled`: 是否开启飞书推送
- `feishu.webhook_url`: 飞书机器人 webhook 地址
- `auto.conversation_file`: 自动分析模式读取的对话文件

## 命令行使用

在技能目录运行：

```bash
python3 scripts/smart_generate.py --analyze "我想看小埋在卧室睡觉" --send
python3 scripts/smart_generate.py --scene "客厅" --action "打游戏" --send
python3 scripts/smart_generate.py --auto --send
```

### 常用参数

- `--analyze TEXT`: 分析文本并自动提取场景/动作
- `--scene TEXT`: 手动指定场景
- `--action TEXT`: 手动指定动作
- `--extra TEXT`: 额外提示词
- `--auto`: 自动读取最近对话文件分析
- `--send`: 生成后推送飞书
- `--dry-run`: 仅分析并输出提示词，不调用 API
- `--output PATH`: 指定输出路径
- `--config PATH`: 指定配置文件

## 自动模式

`--auto` 会读取 `auto.conversation_file`（默认 `data/recent_dialogue.txt`）中最近文本并进行关键词分析。

## 注意事项

1. 请先在 `config.json` 填写 `api_key`
2. 飞书推送依赖 webhook，未启用时 `--send` 会自动跳过
3. 可按需扩展 `context_mapping` 提升识别准确率
