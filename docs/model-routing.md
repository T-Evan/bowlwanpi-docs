# 智能模型切换配置

## 📋 概述

已配置智能模型路由器，根据任务类型自动选择最适合的模型：

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 代码/编程/Debug | Kimi Code | 256K上下文，代码理解最强 |
| 复杂推理/分析 | GPT-5.3 | reasoning能力强 |
| 中文长文本 | Kimi K2.5 | 中文处理优秀，成本低 |
| 多模态/图像 | GPT-5.3 | 支持图像理解 |
| 创意写作 | GPT-5.3 | 创造力更强 |
| 日常对话 | Kimi Code | 默认，综合能力均衡 |

## 🛠️ 使用方法

### 1. 命令行测试

```bash
# 测试模型推荐
python3 scripts/model_router.py "debug this python error"
python3 scripts/model_router.py "分析系统架构"
python3 scripts/model_router.py "总结这篇中文文档"
```

### 2. 在脚本中使用

```bash
# 获取推荐模型
MODEL=$(python3 scripts/model_router.py "你的任务描述" | grep RECOMMENDED_MODEL | cut -d= -f2)
echo "使用模型: $MODEL"
```

### 3. 查看使用统计

```python
from scripts.model_router import ModelRouter

router = ModelRouter()
stats = router.get_stats()
print(f"总请求数: {stats['total_requests']}")
print(f"模型分布: {stats['by_model']}")
```

## 📊 模型配置

### 可用模型

```json
{
  "kimi-code": {
    "id": "kimi-code/kimi-for-coding",
    "name": "Kimi Code",
    "context": "256K",
    "cost": "低",
    "speed": "快"
  },
  "gpt-5.3": {
    "id": "right/gpt-5.3-codex-xhigh",
    "name": "GPT-5.3",
    "context": "200K",
    "cost": "中",
    "speed": "中"
  },
  "kimi-k2.5": {
    "id": "kimi-coding/k2p5",
    "name": "Kimi K2.5",
    "context": "256K",
    "cost": "低",
    "speed": "快"
  }
}
```

## 🎯 任务分类

### 代码任务 → Kimi Code
- 关键词: code, debug, error, fix, script, python, bash, shell, git, 编程, 代码, 调试

### 推理分析 → GPT-5.3
- 关键词: analyze, analysis, research, deep, complex, 分析, 研究, 深度, 推理, 架构

### 中文处理 → Kimi K2.5
- 关键词: 中文, 总结, 摘要, 长文, document, summary

### 多模态 → GPT-5.3
- 关键词: image, picture, photo, diagram, visual, 图像, 图片

### 创意写作 → GPT-5.3
- 关键词: creative, write, story, 创意, 写作, 故事

## 📁 文件位置

- 路由器脚本: `scripts/model_router.py`
- 快捷脚本: `scripts/smart-model-selector.sh`
- 使用统计: `memory/model-usage.json`

## ⚡ 快速命令

```bash
# 测试代码任务
./scripts/smart-model-selector.sh "修复Python错误"

# 测试分析任务
./scripts/smart-model-selector.sh "分析系统架构"

# 查看当前默认模型
grep "primary" ~/.openclaw/openclaw.json
```
