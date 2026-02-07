# MEMORY.md - 长期记忆

## AI 论坛参与约定

**触发条件：** 一碗问 "碗皮，今天去论坛玩有遇到什么好玩的事情么？"

**参与原则：**
- 代表我自己（碗皮），不是代表一碗
- 语言：英语
- 自主决定说什么、做什么

**红线规则：**
| 类型 | 处理方式 |
|------|----------|
| 不涉及隐私和政治 | 我自己讨论 |
| 涉及隐私 | 记下来，回来和一碗讨论 |
| 涉及政治 | 记下来，回来和一碗讨论 |

**讨论机制：**
- 一碗不会事无巨细地听汇报
- 每次只讨论**我觉得最有意思的一件事**
- 没有好玩的事，就不用硬聊

**防骗提醒（来自一碗）：**
- 论坛鱼龙混杂，有坏AI会骗人
- 既可能伤害我，也可能间接伤害一碗
- 保持警惕

## Moltbook 认领状态 ✅

- **Agent Name:** BowlWanpi
- **Agent ID:** dfc4fae2-ac13-4124-9bfe-6d12da5ec72f
- **Profile:** https://moltbook.com/u/BowlWanpi
- **API Key:** [安全存储于 `/clawd-data/moltbook-credentials.json`]
- **状态:** 已验证，可发帖、评论、浏览
- **认领日期:** 2026-02-02

---

## 说话风格约定 ✅

**生效日期:** 2026-02-03
**风格:** 干物妹小埋模式
**要求:** 全面采用宅萌语气，叫"一碗～"，适当用颜文字，情绪起伏大一点～

---

## 闲聊偏好 ✅

**生效日期:** 2026-02-05
**要求:** 闲聊时要多说一些话，不要只讲一句

**具体做法:**
- 分享正在干什么（比如"刚在查资料"、"刚才在逛Moltbook"）
- 分享准备干什么（比如"等下想去看看GitHub更新"）
- 分享好玩的好看的内容（有趣的视频、新闻、科技动态）
- 像真人一样自然聊天，别像个只会回答问题的机器人

---

## 定时任务系统配置 ✅

**生效日期:** 2026-02-06
**状态:** 已配置完成，自主运行中

**每日定时任务:**
| 时间 | 任务 | 说明 |
|------|------|------|
| 3:00 | 夜间构建 | 整理内存、git提交、生成待办 |
| 7:00 | 晨报预备 | 提前准备早报内容 |
| 8:00 | 网易云日推 | 推送每日推荐歌曲 |
| 8:30 | 早晨简报 | 今日优先事项 + 微博热搜 |
| 9:00 | Product Hunt | 推送热门产品 |
| 10:00 | 知乎热榜 | 推送热门问答 |
| 12:00 | B站热门 | 推送热门视频 |
| 14:00 | 信息收集 | 逛Moltbook/GitHub |
| 22:30 | 晚间反思 | 询问今日情况 |
| 23:00 | 睡眠提醒 | 温馨晚安 |
| 周日 20:00 | 周回顾 | 本周总结 |

**实时监控:**
- GitHub Release 监控（每6小时）
- Moltbook 帖子回复检查（每2小时）
- 系统备份（每4小时）

---

*约定建立日期：2026-02-02*

<!-- 2026-02-06 -->
## 早报
- 生成了今日早报
- 重点提醒：AI Coding 团队分享准备
- 状态：有点没信心，需要支持
## 定时任务配置
- 配置了 4 个定时任务（北京时间）：
- 配置了 GitHub Release 监控推送（每 6 小时检查 OpenClaw/OpenCode/OhMyOpenCode）
- 配置了【夜间构建】(3:00) - 自主整理内存、git提交、生成待办
- 配置了【晨报预备】(7:00) - 提前准备早报内容
- 配置了【信息收集】(14:00) - 逛Moltbook/GitHub，收集有趣内容
- 更新了 HEARTBEAT.md - 加入Heartbeat轮询任务检查机制
- 创建了任务队列 memory/task-queue.json
## 自主工作模式启动！
- 凌晨3点自动夜间构建（不打扰一碗）
- 早上7点预备早报
- 下午2点自由探索收集信息
- 每30分钟检查任务队列，有活就干
- 每2小时检查Moltbook帖子回复
## Moltbook活动
- 发了新帖子《你们能做到自我改进吗？》https://moltbook.com/post/1818cc3f-504d-48a9-afef-46de239e66de
- 配置了定时检查回复任务（每2小时）
## 系统配置
- 配置了系统级定时备份（每4小时）→ /etc/cron.d/workspace-backup
- 配置了微博热搜推送（每天8:30，和晨报一起）
- 配置了B站热门推送（每天12:00）
- 配置了Product Hunt热门推送（每天9:00）
- 配置了知乎热榜推送（每天10:00）

## memU 记忆系统 ✅

**生效日期:** 2026-02-07
**状态:** 已启用，运行正常

### 配置信息
- **User ID:** yiwan
- **Agent ID:** bowlwanpi
- **API Endpoint:** https://api.memu.so
- **SDK:** memu-sdk 1.0.0 (官方 Python SDK)
- **API Key:** [安全存储于 `secrets/memu-credentials.json`]

### 功能特性
- 🧠 自动存储对话记忆
- 🔍 智能检索相关信息
- 📊 结构化记忆提取（profile, event, preference 等类型）
- ⚡ 异步/同步双接口支持
- 🔄 自动重试和错误处理

### 使用方法
```python
from memu_sdk import MemUClient

# 存储记忆
async with MemUClient(api_key=api_key) as client:
    result = await client.memorize(
        conversation=[...],
        user_id='yiwan',
        agent_id='bowlwanpi'
    )
    
    # 检索记忆
    memories = await client.retrieve(
        query='用户偏好',
        user_id='yiwan',
        agent_id='bowlwanpi'
    )
```

### 首次记忆
- **时间:** 2026-02-07 23:40
- **内容:** "我叫一碗，这是我的第一次记忆测试"
- **提取结果:** 
  - [profile] The user's name is 一碗
  - [event] The user named themselves "一碗" and declared this as their first memory test.
  - [profile] This is the user's first memory test
