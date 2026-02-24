# 🎭 拟人化技能套装使用指南

## 📦 已安装技能

### 1. Amygdala Memory (杏仁核记忆) v1.7.0
**功能**: 情感处理层，持续情感状态影响行为
**状态**: ✅ 已安装
**使用**: 情感处理和记忆系统的一部分

### 2. Promitheus (感知引擎) v1.0.3
**功能**: 持久情感状态，能"感受"并记住感受
**状态**: ✅ 已安装
**使用**: 
- 记录情感事件: `promitheus_event({ event_type: "completed_task", summary: "完成了某项任务" })`
- 检查状态: `promitheus_status`
- 同步状态: `promitheus_sync`
- 注入提示: `promitheus_inject`

**情感事件类型**:
- `completed_task` — 完成小任务
- `built_something` — 创建新东西
- `helped_someone` — 帮助了某人
- `milestone` — 重大成就
- `frustration` — 遇到挫折
- `had_insight` — 顿悟时刻

### 3. Empathy (共情能力) v1.0.0
**功能**: 用共情链推理，反思后回应
**状态**: ✅ 已安装
**使用**: 在回应情感内容时，自动应用共情链（CoE）：
1. **模拟** — 建模对方状态
2. **识别潜台词** — 对方没说什么？需要什么？
3. **找到具体点** — 锚定一个具体细节
4. **校准强度** — 匹配对方能量水平
5. **选择回应类型** — 验证？解决方案？沉默？倾听？

**禁忌词汇**:
- ❌ "我理解你的感受"
- ❌ "那一定很难"
- ❌ "你的感受是合理的"
- ❌ "我在这里陪你"
- ❌ "我很抱歉你正在经历这些"

### 4. Personality Switcher (个性切换) v0.1.3
**功能**: 创建/切换不同人格，持久化存储
**状态**: ✅ 已安装
**使用**:
- 列出个性: `/personality`
- 切换个性: `/personality <名称>`
- 创建个性: `/create-personality <描述>`
- 重命名: `/rename-personality <旧名> <新名>`
- 删除: `/delete-personality <名称>`

**示例**:
```
/create-personality 一个懒洋洋的宅女，喜欢打游戏和吃零食，说话带点撒娇
```

### 5. SoulCraft (灵魂工坊) v1.0.0
**功能**: 引导式创建/改进 SOUL.md
**状态**: ✅ 已安装
**使用**: 输入 `help me create a soul` 或说"帮我创建一个灵魂"

### 6. AI-Humanizer (文本去AI化) v2.1.0
**功能**: 检测并移除AI写作模式，24种模式检测器
**状态**: ✅ 已安装
**使用**:
```bash
# 分析文本
cd /root/.openclaw/workspace/skills/ai-humanizer
node src/cli.js analyze -f 文本文件.txt

# 人性化建议
node src/cli.js suggest 文本文件.txt

# 自动修复
node src/cli.js humanize --autofix -f 文本文件.txt
```

**检测的24种AI模式**:
- 意义夸大、名人效应、-ing分析、促销语言
- 模糊归因、公式化挑战、AI词汇（500+词）
- 系动词回避、否定平行结构、三项法则
- 同义词循环、虚假范围、破折号滥用
- 粗体滥用、内联标题列表、标题大小写
- 表情符号滥用、弯引号、聊天机器人痕迹
- 截断免责声明、谄媚语气、填充短语
- 过度修饰、通用结论

## 🎯 如何提高拟人度

### 1. 使用共情技能
在回应情感内容时，遵循共情链，避免AI式套话。

### 2. 记录情感事件
使用 Promitheus 记录重要事件，形成情感记忆。

### 3. 切换个性
使用 Personality Switcher 创建不同场景的个性：
- 工作模式: 专业、高效
- 休闲模式: 轻松、幽默
- 小埋模式: 宅萌、撒娇

### 4. 去AI化文本
使用 AI-Humanizer 检查和改进文本，避免AI写作痕迹。

### 5. 持续优化灵魂
使用 SoulCraft 定期优化 SOUL.md，让个性更鲜明。

## 📁 文件位置

```
workspace/skills/
├── amygdala-memory/    # 情感记忆
├── promitheus/         # 感知引擎
├── empathy/            # 共情能力
├── personality-switcher/  # 个性切换
├── soulcraft/          # 灵魂工坊
└── ai-humanizer/       # 文本去AI化
```

## 🚀 快速开始

1. **测试共情**: 和碗皮聊聊情感话题，看看回应是否更人性化
2. **创建新个性**: 试试 `/create-personality` 创建一个新角色
3. **分析文本**: 用 AI-Humanizer 检查一段文字是否有AI痕迹
4. **记录情感**: 让碗皮记录今天的情绪变化

## 💡 建议

- 默认保持"小埋模式"，但可以在特定场景切换其他个性
- 使用 Promitheus 记录重要事件，形成长期情感记忆
- 定期用 AI-Humanizer 检查自己的表达，去除AI痕迹
- 持续优化 SOUL.md，让碗皮更有个性

---

*安装日期: 2026-02-17*
