# Learnings Log

学习、纠正和改进记录

<!-- 记录格式见技能文档 -->

## 2026-02-17 - SSL/连接问题排查实录

### 问题现象
Moltbook API 访问失败，提示 SSL/连接错误

### 排查过程

**Step 1: 验证基础 SSL 连接**
```bash
curl -vI https://www.moltbook.com
```
结果：✅ SSL 握手成功（TLSv1.3），证书有效（Let's Encrypt R12）
- 代理（Mihomo 7890）工作正常
- CONNECT tunnel 建立成功
- 证书验证通过

**Step 2: 验证 Python SSL**
```python
import urllib.request
# 测试1: 基础 HTTPS → 200 OK
# 测试2: 自定义 SSL context → 200 OK  
# 测试3: 使用代理 → 200 OK
```
结果：✅ Python SSL 完全正常

**Step 3: 定位真正问题**
```bash
# 测试各种 API 端点
https://www.moltbook.com/api/posts       → 404 ❌
https://www.moltbook.com/api/v1/posts    → 200 ✅
https://www.moltbook.com/api/v2/posts    → 404 ❌
```

**根因：**
不是 SSL 问题！是 **API 端点配置错误** —— 旧代码使用 `/api/posts`，正确端点是 `/api/v1/posts`

### 解决方案
1. 更新 `moltbook_client.py` 使用正确端点：`https://www.moltbook.com/api/v1`
2. 所有 API 调用改为 `/api/v1/*` 格式

### 经验总结

| 检查项 | 命令/方法 | 目的 |
|--------|-----------|------|
| SSL 基础 | `curl -vI https://...` | 验证 TLS 握手和证书 |
| Python SSL | `urllib.request` 测试 | 排除 Python 环境问题 |
| 端点探测 | 尝试多个 API 路径 | 找到正确的 API 版本 |
| 代理检查 | `env \| grep -i proxy` | 确认代理配置 |

**关键教训：**
- SSL 错误可能只是表象，真正的错误可能被掩盖
- API 升级后（v1 → v2），旧端点可能直接 404
- 先用 curl 测试，再用 Python 复现，分层定位问题

### 相关文件
- `scripts/moltbook_client.py` - 已更新使用 `/api/v1`
- `memory/moltbook-posts-cache.json` - 缓存数据

## [LRN-20260218-001] best_practice

**Logged**: 2026-02-18T20:46:00+08:00
**Priority**: high
**Status**: pending
**Area**: config

### Summary
从“任务执行型助手”切换到“战略决策+执行解耦”的蜂巢式工作模式。

### Details
用户提供了蜂巢框架的进化思路，核心价值不在“术语”，而在运行机制：
1) 战略与执行解耦：复杂任务由主代理负责目标、约束、验收，子代理负责实现。
2) 决策议会化：对关键方案至少进行收益/风险双视角审议，避免单点偏差。
3) 主动心跳化：从被动问答转向定期巡检+异常上报，正常时保持安静。
4) 认知可审计：关键策略调整应留痕（规则文件/提交记录），便于回滚与追溯。
5) 经验堆肥化：长对话沉淀为结构化结论，减少上下文污染。

### Suggested Action
- 将复杂多步骤任务默认路由为“主代理规划 + 子代理执行”。
- 对高影响决策引入固定的“收益/风险”双评估模板。
- 心跳仅推送新增异常，不重复同步历史错误。

### Metadata
- Source: user_feedback
- Related Files: AGENTS.md, HEARTBEAT.md, cron/owner-rules.json
- Tags: hive, delegation, council, heartbeat, memory

