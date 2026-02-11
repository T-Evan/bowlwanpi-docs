---
name: intelligent-search
description: 智能搜索聚合技能 - 统一腾讯云 WSA 和 Tavily 搜索能力，支持中英文自动识别、主备切换、高可用搜索。
---

# 🔍 智能搜索 (Intelligent Search)

## 配置

### API Keys

在 `skills/intelligent-search/.env` 文件中配置：

```bash
# Tavily API Key (必需)
TAVILY_API_KEY=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

# 腾讯云 WSA (可选，作为备用)
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key
```

**当前配置状态：** ✅ Tavily API Key 已配置

## 概述

统一的搜索接口，整合 **腾讯云 WSA** 和 **Tavily** 两大搜索引擎，实现：

- ✅ **中英文自动识别** - 智能选择最佳搜索引擎
- ✅ **主备切换** - 主引擎失败自动切换到备用
- ✅ **高可用** - 确保搜索服务不中断
- ✅ **统一格式** - 所有搜索结果格式一致

## 架构

```
用户查询
    ↓
语言检测 (LanguageDetector)
    ↓
搜索路由 (SearchRouter) → 决定主/备引擎
    ↓
主引擎搜索
    ↓ (失败)
备用引擎搜索
    ↓
结果标准化 → 统一格式返回
```

## 搜索引擎

| 引擎 | 特点 | 适用场景 |
|------|------|----------|
| **腾讯云 WSA** | 中文优化、国内快速 | 中文查询、国内新闻 |
| **Tavily** | 引用详细、英文优化 | 英文查询、需要引用 |

## 路由策略

### 默认策略

| 查询类型 | 主引擎 | 备用引擎 |
|----------|--------|----------|
| 纯中文 | 腾讯云 WSA | Tavily |
| 纯英文 | Tavily | 腾讯云 WSA |
| 混合语言 | 腾讯云 WSA | Tavily |
| 需要引用 | Tavily | 腾讯云 WSA |

### 关键词优化

**中文关键词**（自动使用腾讯云 WSA）：
- 中文、中国、国内、新闻、热点
- 微博、知乎、百度、腾讯、阿里
- 字节、抖音、快手、小红书、B站

**英文关键词**（自动使用 Tavily）：
- github、stackoverflow、documentation
- paper、research、arxiv
- python、javascript、code

## 使用方法

### 基础搜索

```python
from skills.intelligent-search.search_engine import smart_search
import asyncio

# 自动选择引擎
result = asyncio.run(smart_search("人工智能"))

# 结果格式
{
    'success': True,
    'query': '人工智能',
    'language': 'zh',
    'primary_provider': 'tencent_wsa',
    'fallback_used': False,
    'results': [
        {
            'title': '...',
            'content': '...',
            'url': '...',
            'source': '搜狐',
            'provider': 'tencent_wsa',
            'score': 0.79,
            'date': '2024-11-20'
        }
    ],
    'total_results': 10
}
```

### 高级选项

```python
# 优先需要引用
result = asyncio.run(smart_search(
    "Python best practices",
    prefer_citations=True  # 优先 Tavily
))

# 强制指定引擎
result = asyncio.run(smart_search(
    "人工智能",
    force_provider='tencent'  # 强制腾讯云 WSA
))

# 指定结果数量
result = asyncio.run(smart_search(
    "人工智能",
    num_results=20
))
```

### 兼容接口

```python
from skills.intelligent-search.search_engine import web_search
import asyncio

# 兼容原 web_search 接口
results = asyncio.run(web_search("搜索词", num_results=10))
```

## 文件结构

```
skills/intelligent-search/
├── SKILL.md                    # 本文档
├── search_engine.py            # 核心搜索引擎
│   ├── LanguageDetector        # 语言检测
│   ├── SearchRouter            # 搜索路由
│   ├── TavilySearchClient      # Tavily 客户端
│   └── IntelligentSearchEngine # 主引擎
└── __init__.py                 # 包初始化
```

## 高可用机制

### 故障检测
- 网络超时 (>30s)
- API 错误返回
- 空结果返回

### 自动切换
1. 主引擎失败 → 立即切换到备用
2. 记录失败日志
3. 返回备用引擎结果
4. 标记 `fallback_used: True`

### 统计监控
```python
engine = IntelligentSearchEngine()
stats = engine.get_search_stats()
# {
#     'total_searches': 100,
#     'fallback_usage': 5,
#     'fallback_rate': 0.05
# }
```

## 配置

### 依赖
- 腾讯云 WSA: `tencentcloud-sdk-python-wsa`
- Tavily: `@tavily/mcp` (npx)

### 凭证
- 腾讯云: `/root/.openclaw/workspace/secrets/tencent-credentials.json`
- Tavily: 已配置在 MCP 中

## 测试

```bash
cd /root/.openclaw/workspace
python3 skills/intelligent-search/search_engine.py
```

## 状态

| 组件 | 状态 |
|------|------|
| 语言检测 | ✅ 完成 |
| 搜索路由 | ✅ 完成 |
| 腾讯云 WSA 集成 | ✅ 完成 |
| Tavily 集成 | ✅ 完成 |
| 主备切换 | ✅ 完成 |
| 结果标准化 | ✅ 完成 |
| 兼容接口 | ✅ 完成 |

---

*配置时间: 2026-02-08*
*版本: 1.0.0*
