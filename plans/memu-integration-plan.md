# 🧠 memU 接入计划（方案 A - API 直连）

## 📋 执行步骤

### Phase 1: 准备工作（今晚/明天）

**1.1 注册 memU 账号**
- 访问: https://app.memu.so/
- 注册账号
- 获取 API Key
- 记录到: `~/.openclaw/workspace/secrets/memu-credentials.json`

**1.2 安装依赖**
```bash
pip install memu-py
```

**1.3 配置环境**
```bash
export MEMU_API_KEY="your_api_key"
export MEMU_BASE_URL="https://api.memu.pro/v1"
```

---

### Phase 2: 核心模块开发

**2.1 创建 memU 客户端模块**
文件: `~/.openclaw/workspace/modules/memu_client.py`

```python
"""
memU 记忆客户端
为 BowlWanpi 提供持久记忆能力
"""
from memu import MemUService
import os

class BowlWanpiMemory:
    def __init__(self):
        self.service = MemUService(
            api_key=os.getenv("MEMU_API_KEY"),
            base_url=os.getenv("MEMU_BASE_URL", "https://api.memu.pro/v1")
        )
        self.user_id = "bowlwanpi_user"  # 一碗的用户ID
    
    def memorize_conversation(self, content: str, metadata: dict = None):
        """存储对话记忆"""
        return self.service.memorize(
            content=content,
            user_id=self.user_id,
            metadata=metadata or {}
        )
    
    def retrieve_context(self, query: str, limit: int = 5):
        """检索相关记忆"""
        return self.service.retrieve(
            query=query,
            user_id=self.user_id,
            limit=limit
        )
    
    def get_user_profile(self):
        """获取用户画像（偏好、习惯等）"""
        return self.service.get_profile(self.user_id)
```

**2.2 创建记忆管理 Skill**
文件: `~/.openclaw/workspace/skills/memu-bridge/SKILL.md`

```yaml
---
name: memu-bridge
description: 连接 memU 记忆系统，为 BowlWanpi 提供持久记忆能力
---

# memU 记忆桥接

## 功能
- 自动存储重要对话
- 检索相关历史上下文
- 预测用户意图
- 维护用户画像

## 使用场景
- 用户提到重要信息时自动记忆
- 回答前检索相关历史
- 预测用户下一步需求
```

**2.3 集成到 OpenClaw 会话流程**

修改 BowlWanpi 的核心逻辑：

```python
# 在会话开始时
from modules.memu_client import BowlWanpiMemory

memory = BowlWanpiMemory()

# 1. 检索相关记忆
context = memory.retrieve_context(user_message)

# 2. 将记忆注入系统提示
enhanced_prompt = f"""
{base_system_prompt}

## 相关记忆
{context}
"""

# 3. 生成回复
response = generate_response(enhanced_prompt)

# 4. 存储重要信息
if is_important(user_message, response):
    memory.memorize_conversation(
        content=f"User: {user_message}\nAssistant: {response}",
        metadata={"type": "conversation", "timestamp": now()}
    )
```

---

### Phase 3: 高级功能

**3.1 意图预测**
```python
def predict_user_intent(self, recent_messages: list) -> str:
    """基于记忆预测用户下一步需求"""
    profile = self.get_user_profile()
    # 分析模式，预测意图
    return predicted_intent
```

**3.2 主动记忆整理**
- 夜间构建时自动归档
- 生成记忆摘要
- 清理过期记忆

**3.3 记忆可视化**
- 生成记忆图谱
- 展示用户兴趣演变
- 时间线视图

---

### Phase 4: 测试与优化

**4.1 功能测试**
- [ ] 记忆存储测试
- [ ] 检索准确性测试
- [ ] 性能测试（延迟 < 500ms）
- [ ] 错误处理测试

**4.2 用户体验优化**
- [ ] 记忆命中提示（"我记得你之前说过..."）
- [ ] 记忆管理命令（/forget, /remember）
- [ ] 隐私控制（敏感信息过滤）

---

## 💰 成本预估

**memU 定价（参考）：**
- 免费版: 有限请求次数
- 付费版: 按调用量计费

**我们的用量预估：**
- 每日对话: ~100 轮
- 记忆操作: ~200 次/天
- 预计费用: $X/月（需要实际测试）

---

## ⚠️ 风险提示

1. **API 依赖**：依赖 memU 服务可用性
2. **隐私数据**：对话内容会发送到 memU 服务器
3. **成本控制**：需要监控 API 调用量
4. **网络延迟**：每次调用增加 100-500ms 延迟

---

## 🎯 成功标准

- [x] 能自动存储重要对话
- [x] 能准确检索相关历史
- [x] 响应时间增加 < 1秒
- [x] 一碗感觉"碗皮更懂我了"

---

## 📅 时间线

**今晚（2月7日）：**
- [ ] 注册 memU 账号
- [ ] 获取 API Key
- [ ] 基础模块设计

**明天（2月8日）：**
- [ ] 安装依赖
- [ ] 开发核心模块
- [ ] 基础集成测试

**后天（2月9日）：**
- [ ] 高级功能
- [ ] 用户体验优化
- [ ] 正式上线

---

## 🤔 今晚要做的事

1. 注册 memU 账号 → https://app.memu.so/
2. 将 API Key 保存到安全位置
3. 告诉我 Key 已准备好（不要发送 Key 本身！）

然后明天开始开发！💪

---

*制定时间: 2026-02-07 23:16*
*方案: A - API 直连*
