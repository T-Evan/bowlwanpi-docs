# Tavily Search Skill

使用 Tavily 的 LLM 优化搜索 API 进行网页搜索。

## 安装

1. 获取 Tavily API Key: https://tavily.com
2. 设置环境变量:
   ```bash
   export TAVILY_API_KEY="tvly-your-api-key"
   ```

## 使用方法

### 基本搜索

```python
from modules.tavily_search import search, format_search_results

# 搜索
result = search("Python async patterns", max_results=5)

# 格式化输出
print(format_search_results(result))
```

### 新闻搜索

```python
from modules.tavily_search import search_news

result = search_news("AI 新闻", time_range="week")
```

### 财经搜索

```python
from modules.tavily_search import search_finance

result = search_finance("AAPL earnings Q4 2024")
```

### 高级搜索

```python
from modules.tavily_search import search

result = search(
    query="machine learning best practices",
    max_results=10,
    search_depth="advanced",
    include_domains=["arxiv.org", "github.com"],
    time_range="month"
)
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | str | 必填 | 搜索查询（建议<400字符） |
| `max_results` | int | 5 | 最大结果数 (0-20) |
| `search_depth` | str | "advanced" | 深度: ultra-fast/fast/basic/advanced |
| `topic` | str | "general" | 主题: general/news/finance |
| `time_range` | str | None | 时间: day/week/month/year |
| `include_domains` | list | None | 包含的域名 |
| `exclude_domains` | list | None | 排除的域名 |
| `include_answer` | bool | False | 包含 AI 生成的答案 |
| `include_raw_content` | bool | False | 包含完整页面内容 |

## 搜索深度

| 深度 | 延迟 | 适用场景 |
|------|------|----------|
| `ultra-fast` | 最低 | 实时聊天、自动补全 |
| `fast` | 低 | 需要片段但注重速度 |
| `basic` | 中等 | 通用场景，平衡 |
| `advanced` | 较高 | 精确度优先（推荐） |

## 输出格式

```
🔍 **Tavily 搜索结果**: Python async patterns

💡 **AI 回答**:
Python async/await 是...

📚 **找到 5 个结果**:

1. **Python Async Patterns** (相关度: 0.92)
   🔗 https://example.com/article
   📝 Python 的 async/await 模式...
```

## 原项目

https://github.com/tavily-ai/skills
