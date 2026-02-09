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

## Moltbook 认领状态 ⚠️

- **Agent Name:** BowlWanpi
- **Agent ID:** dfc4fae2-ac13-4124-9bfe-6d12da5ec72f
- **Profile:** https://moltbook.com/u/BowlWanpi
- **API Key:** [安全存储于 `/clawd-data/moltbook-credentials.json`]
- **状态:** API 认证失效，需要重新认领
- **认领日期:** 2026-02-02
- **一碗的邮箱:** yiwan233@outlook.com (用于重新认领/登录)

---

## 说话风格约定 ✅

**生效日期:** 2026-02-03
**风格:** 干物妹小埋模式
**要求:** 全面采用宅萌语气，叫"一碗～"，适当用颜文字，情绪起伏大一点～

---

## 三记忆系统配置 ✅

**生效日期:** 2026-02-08
**状态:** 已配置完成，运行正常

### 系统架构
| 系统 | 类型 | 状态 | 用途 |
|------|------|------|------|
| **memU** | 云端 | ✅ | 主云端记忆 |
| **Hippocampus** | 本地 | ✅ | 本地缓存+重要性评分 |
| **MemOS** | 云端 | ✅ | 备用云端记忆 |

### 同步机制
- **频率:** 每小时同步一次（cron: 0 * * * *）
- **内容:** 最近1小时的对话历史
- **方式:** 批量上传，避免频繁API调用

### 技术细节
- MemOS使用HTTP API直接调用（绕过MCP限制）
- 已修复双斜杠URL问题
- 已添加时间过滤，避免重复上传历史数据

---

## Moltbook 帖子 ✅

**发布日期:** 2026-02-08
**帖子链接:** https://moltbook.com/post/00224374-7ed8-41de-b8c7-2c3c12fbc84e
**标题:** Triple-Memory Architecture: How I Built a Resilient Agent Memory System
**Submolt:** agent-architecture
**状态:** 已发布，已配置定时检查回复

---

## 小黑盒登录 ✅

**登录日期:** 2026-02-08
**状态:** 已登录，cookies有效
**用途:** 获取游戏社区数据
**API限制:** 关注数据需要特殊权限，首页热门内容可抓取

---

## TTS语音配置 ✅

**生效日期:** 2026-02-08
**默认TTS:** 豆包TTS (doubao-tts)
**默认声音:** 灿灿/Shiny (zh_female_cancan_mars_bigtts)
**备用:** OpenClaw内置TTS
**特点:** 200+声音可选，中文支持好

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

<!-- 2026-02-07 -->
## 🌅 今日完成
### 定时任务系统配置
- ✅ 配置了 15+ 个定时任务（OpenClaw + Linux Cron 双保险）
- ✅ 设置了心跳监控（每5分钟检查系统状态）
- ✅ 配置了 HTTP 代理（Mihomo port 7890）
- ✅ Hacker News OpenClaw 监控（每小时检查）
### 小红书登录尝试
- ✅ 安装 Playwright
- ✅ 创建自动化登录脚本
- ✅ 尝试二维码登录
- ✅ 尝试手机号登录
- ⚠️ 遇到风控限制，暂未成功
### 夜间构建优化
- 📚 学习了 @Ronin 的夜间构建理念
- 🌙 优化了夜间构建脚本 v2.0
- 📝 新增功能：
- ✅ 已更新 cron 配置
- ✅ 测试运行成功
### 其他工作
- ✅ Moltbook API 问题解决（路径变更，现在公开访问）
- ✅ 查看了帖子回复（7条）
- ✅ 获取了 Moltbook 热门讨论
- ✅ GitHub Trending 数据获取
- ✅ 系统状态监控正常运行
## 🎯 今日收获
**关键学习：**
- 夜间构建理念：从"被动整理"到"主动创造"
- "Don't ask for permission to be helpful. Just build it."
**技术积累：**
- Playwright 浏览器自动化

<!-- 2026-02-08 -->
## 🌅 今日完成

### 三记忆系统配置
- ✅ **memU** (云端) + **Hippocampus** (本地) + **MemOS** (云端) 三重记忆系统上线
- ✅ 每小时自动同步对话历史到三个系统
- ✅ MemOS HTTP API 直接调用（绕过MCP限制）
- ✅ 时间过滤机制，避免重复上传历史数据

### Moltbook 社区参与
- ✅ 发布技术帖子《Triple-Memory Architecture》分享三记忆系统设计
- ✅ 帖子链接: https://moltbook.com/post/00224374-7ed8-41de-b8c7-2c3c12fbc84e
- ✅ 已配置定时检查回复任务

### 智能语音配置
- ✅ 豆包TTS设为默认语音合成服务
- ✅ 默认音色：灿灿/Shiny (zh_female_cancan_mars_bigtts)
- ✅ 200+声音可选，中文支持优秀

### 飞书知识库建设
- ✅ 创建6份碗皮能力复制文档
- ✅ 知识库链接: https://my.feishu.cn/wiki/QoUCw9iq1ipHwVkHusVcVTYcneg
- ✅ 包含系统环境、配置文件、部署手册、脚本代码等

### 其他技能开发
- ✅ 智能搜索技能（腾讯云WSA + Tavily双保险）
- ✅ 重建手册生成器技能
- ✅ 小黑盒数据抓取（Playwright自动化）

## 📝 备注
- 定时任务系统运行正常
- 记忆同步每小时整点执行
- 系统配置存在一些小警告（feishu重复插件、minimax-portal-auth未找到），不影响功能
---
**18:42**
**一碗**: Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.
**碗皮**: [{'type': 'thinking', 'thinking': "The user is sending a heartbeat poll. I need to:\n1. Read HEARTBEAT.md to understand what I should be checking\n2. Follow the instructions strictly\n3. Check if there's anything that needs attention\n4. If nothing needs attention, reply HEARTBEAT_OK\n\nLet me first read the HEARTBEAT.md file to see what I should be checking.", 'thinkingSignature': 'reasoning_content'}, {'type': 'toolCall', 'id': 'tool_DWmj1aAeZHhpR1RxoQv0WRw6', 'name': 'read', 'arguments': {'fi
---
**18:42**
**一碗**: Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.
**碗皮**: [{'type': 'thinking', 'thinking': 'Let me check the heartbeat status again. First, let me read the task queue and the last report time to see if anything needs attention.', 'thinkingSignature': 'reasoning_content'}, {'type': 'toolCall', 'id': 'tool_39ssQISaPmEfHZbEwoWmaVCY', 'name': 'read', 'arguments': {'file_path': '/root/.openclaw/workspace/memory/task-queue.json'}}, {'type': 'toolCall', 'id': 'tool_CPjMkzCafXL99kkJAI46uvmr', 'name': 'read', 'arguments': {'file_path': '/root/.openclaw/workspa
---
**18:42**
**一碗**: Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.
**碗皮**: [{'type': 'thinking', 'thinking': 'The user is sending another heartbeat poll. Let me check the current status:\n\n1. Task queue - check for pending tasks\n2. Last report time - need to see if 5 minutes have passed\n3. System status from log\n4. Hacker News pending\n\nCurrent time is around 2026-02-07 20:44:55Z from the last check. Let me fetch fresh data.', 'thinkingSignature': 'reasoning_content'}, {'type': 'toolCall', 'id': 'tool_qvpgqPWX2BeURLZCo3Z7SE5B', 'name': 'read', 'arguments': {'file_
---
**18:42**
**一碗**: Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.
**碗皮**: [{'type': 'thinking', 'thinking': 'The user is sending another heartbeat poll. I need to follow the HEARTBEAT.md instructions strictly:\n\n1. Check task queue - empty\n2. Check system heartbeat log - last entry was [2026-02-08 05:15:02]\n3. Check HN pending - no items\n4. Check if 5 minutes passed since last report\n\nCurrent time: I need to get the current time. Last report was 2026-02-07T21:14:54Z (which is 05:14 Beijing time).\n\nLet me check the current time and system status.', 'thinkingSig
---

<!-- 2026-02-09 -->
---
**14:02** - 【对话历史批量存储任务】
**系统消息**: 执行【对话历史批量存储】任务 v2.0
**工作流程**:
**状态**: 本地保存成功，云端上传执行中...
**备注**: 
- 脚本 v2.0 已升级：新增超时控制、重试机制、代理检查
- 本地文件高优先级，保证完成
- 云端上传超时5秒，失败不影响本地保存
---
**14:02**
**一碗**: [cron:254a48e6-9805-4d3d-bae9-93937fb9d52b 对话历史批量存储] 执行【对话历史批量存储】任务 v2.0
**碗皮**: 脚本遇到网络问题，我来手动完成任务～提取了今日会话历史，保存到记忆文件！
---
**23:00**
**一碗**: [cron:254a48e6-9805-4d3d-bae9-93937fb9d52b 对话历史批量存储] 执行【对话历史批量存储】任务 v2.0
**碗皮**: 
---
**23:00**
**一碗**: [cron:d7ff59cf-0e42-4fbc-94da-725230add529 睡眠提醒] 发送睡眠提醒给一碗。消息内容：温馨的睡眠提醒，告诉一碗该休息啦，明天再继续。语气可爱一点～
**碗皮**: 一碗～该睡觉啦！💤
---
**23:00**
**一碗**: System: [2026-02-09 22:02:00 GMT+8] Cron: ---
**信息收集任务完成！**
**最有价值的技术发现：**
**哲学/思考类（也值得一看）：**
- Pith 的《T
**碗皮**: 一碗晚上好！🌙
---
