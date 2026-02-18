# Model Router Skill

智能模型路由系统 - 根据任务类型推荐最适合的AI模型，实现效果与成本的最优平衡。

## 📋 模型策略

| 场景 | 推荐模型 | 理由 | 切换命令 |
|------|----------|------|----------|
| 代码/编程/Debug | 💻 Kimi Code | 256K上下文，代码理解最强 | `/model kimi-code` |
| 复杂推理/分析 | 🧠 GPT-5.3 | reasoning能力强 | `/model right-gpt5.3` |
| 中文长文本 | 🇨🇳 Kimi K2.5 | 中文处理优秀，成本低 | `/model kimi-k2.5` |
| 多模态/图像 | 🧠 GPT-5.3 | 支持图像理解 | `/model right-gpt5.3` |
| 创意写作 | 🧠 GPT-5.3 | 创造力更强 | `/model right-gpt5.3` |
| 日常对话 | 💻 Kimi Code | 默认，综合能力均衡 | `/model kimi-code` |

## 🚀 快速使用

### 方式1: 智能助手（推荐）

发送任务前，先获取模型建议：

```bash
python3 skills/model-router/model_advisor.py "你的任务描述"
```

输出示例：
```
🧠 碗皮觉得用 **GPT-5.3** 更好哦～

💡 理由: 分析推理任务
📈 匹配度: 85%

🎯 快速切换:
   /model right-gpt5.3

✨ GPT-5.3 擅长: 推理, 分析, 创意
```

### 方式2: 详细分析

获取完整的路由分析：

```bash
python3 skills/model-router/auto_router.py "debug this python error"

# 输出JSON格式:
# {
#   "model_id": "kimi-code/kimi-for-coding",
#   "model_alias": "kimi-code",
#   "reason": "检测到编程相关任务 (命中: 2个模式)，使用 Kimi Code"
# }
```

### 方式3: 手动切换

直接切换到指定模型：

```bash
# 查看当前模型
/model

# 切换到代码专家
/model kimi-code

# 切换到推理专家  
/model right-gpt5.3

# 切换到中文专家
/model kimi-k2.5
```

## 🔍 路由规则

系统自动检测以下关键词：

**💻 代码任务 → Kimi Code**
- 关键词: `code`, `python`, `debug`, `script`, `function`, `编程`, `代码`, `.py`

**🧠 推理任务 → GPT-5.3**
- 关键词: `analyze`, `analysis`, `研究`, `分析`, `策略`, `架构`, `优化`

**✨ 创意任务 → GPT-5.3**
- 关键词: `creative`, `write`, `story`, `创意`, `写作`, `故事`, `生成`

**🇨🇳 中文任务 → Kimi K2.5**
- 模式: 大量中文字符(>50个)、`总结`, `摘要`, `翻译`, `文档`

## 📁 文件结构

```
skills/model-router/
├── SKILL.md                    # 本说明文档
├── auto_router.py              # 详细路由器（JSON输出）
├── model_advisor.py            # 智能助手（友好提示）
├── subagent_router.py          # 子代理路由（实验性）
└── README.md                   # 使用指南
```

## ⚠️ 技术限制

**为什么不支持完全自动切换？**

1. OpenClaw 的模型在会话开始时确定
2. `sessions_spawn` 不支持指定模型参数
3. 子代理继承主代理的模型配置

**解决方案**: 使用智能助手提示，手动 `/model` 切换

## 💡 使用技巧

### 技巧1: 任务前缀标记
在消息前加标记帮助识别：
- `[CODE]` - 代码任务
- `[THINK]` - 推理任务  
- `[CN]` - 中文任务
- `[CREATIVE]` - 创意任务

### 技巧2: 快捷命令
```bash
# 代码模式
/model kimi-code

# 思考模式
/model right-gpt5.3

# 中文模式
/model kimi-k2.5
```

## 📝 更新记录

- **2026-02-18** - 初版发布，支持智能助手提示
- **2026-02-18** - 添加子代理路由（实验性）

## 🔮 未来计划

- [ ] 与OpenClaw Gateway集成，实现真正的自动切换
- [ ] 基于历史任务学习用户偏好
- [ ] 添加更多模型支持（MiniMax等）
