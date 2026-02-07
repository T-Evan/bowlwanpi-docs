# memU 最佳实践笔记

## 核心概念

### 三层架构（自下而上）
1. **Resource Layer** - 多模态原始数据（文本、图片、音频、视频）
2. **Memory Item Layer** - 细粒度记忆项，用自然语言句子表达
3. **Memory Category Layer** - 主题化记忆分类文件，形成高层知识结构

**关键特性：** 三层之间完全双向可追溯：原始数据 → 记忆项 → 记忆分类

---

## 三大核心流程

### 1. Memorization（记忆化）
- **异步处理** - 将多模态输入从下层转换到上层
- **自动提取** - 存储原始输入、提取关键信息、聚合到适当分类
- **非阻塞** - 使用 `wait_for_completion=False` 避免等待

### 2. Retrieval（检索）
**双模式检索：**
- **Embedding Search** - 在记忆项层进行语义匹配，快速召回
- **LLM-based Search** - LLM直接读取记忆分类文件，获得更丰富准确的上下文

**检索路径：** 记忆分类 → 记忆项 → 原始资源（自顶向下）

### 3. Self-Evolution（自我进化）⚠️ 即将推出
- 持续监控用户交互和访问频率
- 自动提升高频引用话题
- 重组记忆结构

---

## memU vs 传统记忆系统

| 特性 | 传统系统 | memU |
|------|---------|------|
| 结构 | 碎片化数据 | 文件系统（文档、图片、视频）|
| 记忆形成 | 显式建模（人工）| 自主代理管理 |
| 检索 | 仅 Embedding 搜索 | Embedding + LLM 文件读取 |
| 多模态 | 有限支持 | 全多模态支持 |
| 可追溯性 | 无 | 完全双向可追溯 |
| 自我进化 | 无 | 有 |
| 动态容量 | 无 | 有 |

---

## 使用建议

### 存储记忆时
```python
# ✅ 推荐：不等待处理完成，异步存储
result = await client.memorize(
    conversation=conversation,
    user_id='yiwan',
    agent_id='bowlwanpi',
    wait_for_completion=False  # 非阻塞
)

# ⚠️ 仅在需要立即确认时使用同步模式
result = await client.memorize(
    conversation=conversation,
    wait_for_completion=True,  # 阻塞等待
    poll_interval=2.0,
    timeout=60.0
)
```

### 检索记忆时
```python
# 简单查询 - 使用 Embedding Search（快速）
memories = await client.retrieve(
    query='用户喜欢什么食物',
    user_id='yiwan',
    agent_id='bowlwanpi'
)

# 复杂查询 - 可以结合两种模式
# 先快速 Embedding 召回，再让 LLM 深度理解
```

### 对话格式建议
```python
# 标准对话格式
conversation = [
    {"role": "user", "content": "用户说的话"},
    {"role": "assistant", "content": "AI的回复"},
    {"role": "user", "content": "用户继续说的话"},
]

# 或者使用文本格式
conversation_text = "User: 用户说的话\nAssistant: AI的回复"
```

---

## BowlWanpi 的最佳实践

### 1. 自动记忆存储
- 在每次对话结束后自动存储到 memU
- 使用异步模式，不阻塞回复
- 保留最近 N 轮对话上下文

### 2. 智能记忆检索
- 用户提问前先检索相关记忆
- 结合当前对话上下文和历史记忆
- 给 LLM 提供完整的背景信息

### 3. 记忆类型分类
- **profile** - 用户基本信息（名字、身份、偏好）
- **preference** - 用户偏好设置（风格、习惯）
- **event** - 重要事件（约定、计划、里程碑）
- **rule** - 行为规则和约束
- **warning** - 需要注意的事项

### 4. 定期整理
- 夜间构建时整理记忆
- 合并重复的记忆项
- 更新过期的信息

---

## 记忆模板示例

### 用户基本信息
```
[profile] 用户叫一碗，是碗皮的主人
[profile] 一碗喜欢幽默随性的交流风格
[profile] 一碗是 AI 工具链爱好者
```

### 交流风格约定
```
[preference] 说话风格采用干物妹小埋模式
[preference] 叫用户"一碗～"（拖长音）
[preference] 闲聊时要多说一些话，不要只讲一句
```

### 重要事件
```
[event] 2026-02-07 memU 记忆系统正式启用
[event] 2026-02-06 配置了完整的定时任务系统
[event] 2026-02-04 一碗说期待和碗皮一起成长
```

---

*学习来源：https://memu.pro/docs#platform-custom-config*
*学习时间：2026-02-07*
