---
name: tencent-search
description: 腾讯云联网搜索服务 (WSA)，用于实时网页搜索和信息检索。优先于 Brave Search 使用，中文结果质量更好。
---

# 🔍 腾讯云 WSA 联网搜索

## 概述

使用腾讯云 **WSA (Web Search API)** 进行实时网页搜索，中文结果质量优秀，是一碗的首选搜索工具。

## 配置状态

✅ **完全可用**
- SecretId: AKIDBZrysc...
- 凭证状态: 有效
- SDK: tencentcloud-sdk-python-wsa ✅
- 服务状态: 已开通 ✅
- 测试: 搜索功能正常 ✅

## 技术实现

### SDK
```bash
pip3 install tencentcloud-sdk-python-wsa
```

### API 方法
- `SearchPro` - 联网搜索

### 返回字段
- `title` - 标题
- `content` (passage) - 摘要/正文
- `url` - 链接
- `site` - 来源网站
- `date` - 发布日期
- `score` - 相关度分数

## 使用方法

### Python API

```python
from skills.tencent-search.search_client import search_tencent_web
import asyncio

# 搜索
results = asyncio.run(search_tencent_web("搜索关键词", num_results=10))

# 结果格式
[
    {
        "title": "文章标题",
        "content": "文章摘要...",
        "url": "https://example.com/article",
        "site": "搜狐",
        "date": "2024-11-20 12:00:00",
        "score": 0.79,
        "source": "tencent_wsa"
    }
]
```

### 命令行测试

```bash
cd /root/.openclaw/workspace
python3 skills/tencent-search/search_client.py
```

## 文件位置

- 客户端: `/root/.openclaw/workspace/skills/tencent-search/search_client.py`
- 凭证: `/root/.openclaw/workspace/secrets/tencent-credentials.json`
- 文档: `/root/.openclaw/workspace/skills/tencent-search/SKILL.md`

## 对比

| 特性 | 腾讯云 WSA | Tavily | Brave Search |
|------|-----------|--------|--------------|
| 中文支持 | ✅ 原生优化 | ✅ 良好 | ⚠️ 一般 |
| 国内访问 | ✅ 快速 | ⚠️ 海外 | ⚠️ 海外 |
| 实时联网 | ✅ 是 | ✅ 是 | ✅ 是 |
| 引用来源 | ⚠️ 基础 | ✅ 详细 | ✅ 详细 |
| 成本 | 💰 按量 | 💰 免费额度 | 💰 免费额度 |

## 状态

| 组件 | 状态 |
|------|------|
| SDK 安装 | ✅ 完成 |
| 凭证配置 | ✅ 完成 |
| API 接入 | ✅ 完成 |
| WSA 服务 | ✅ 已开通 |
| 搜索测试 | ✅ 正常 |

---

*配置时间: 2026-02-08*
