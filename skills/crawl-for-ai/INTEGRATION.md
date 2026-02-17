# Crawl4AI 整合配置

## 状态：✅ 已部署

### 部署方式
- **原计划**: Docker 容器（网络问题未完成）
- **当前方案**: Python pip 安装 ✅

### 安装信息
```
Package: crawl4ai 0.8.0
Location: /usr/local/lib/python3.11/site-packages
Install: pip install crawl4ai -i https://pypi.org/simple
```

## 使用方法

### 命令行脚本
```bash
# 基础抓取
python3 skills/crawl-for-ai/scripts/crawl_page.py "https://example.com"

# JSON 输出
python3 skills/crawl-for-ai/scripts/crawl_page.py "https://example.com" --json

# 详细日志
python3 skills/crawl-for-ai/scripts/crawl_page.py "https://example.com" --verbose --json

# 快捷命令（添加到 .bashrc）
alias crawl='python3 ~/.openclaw/workspace/skills/crawl-for-ai/scripts/crawl_page.py'
```

### Python API
```python
from crawl4ai import AsyncWebCrawler
import asyncio

async def scrape(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        return {
            "title": result.metadata.get("title", ""),
            "markdown": result.markdown,
            "url": result.url
        }

# 使用
data = asyncio.run(scrape("https://example.com"))
```

## 功能对比

| 功能 | Crawl4AI (当前) | Playwright 替代 |
|------|-----------------|-----------------|
| JS 渲染 | ✅ | ✅ |
| Markdown 输出 | ✅ 完整 | ⚠️ 简化 |
| 智能等待 | ✅ 自动 | ⚠️ 固定延迟 |
| 反爬检测 | ✅ 更好 | ⚠️ 基础 |
| 图片提取 | ✅ | ✅ |
| 链接提取 | ✅ | ✅ |
| 速度 | ✅ 快 | ✅ 快 |

## 与现有系统集成

### 1. 替代 lets-go-rss 的 RSSHub 失败场景
当 RSSHub 被风控时（B站/小红书），可使用 Crawl4AI 直接抓取用户主页：
```bash
# 抓取 B站用户主页
python3 crawl_page.py "https://space.bilibili.com/25876945" --json
```

### 2. 配合 Tavily 搜索使用
Tavily 搜索结果页面内容不全时，Crawl4AI 二次抓取：
```python
# 搜索 -> 抓取详情
search_results = tavily_search(query)
for result in search_results:
    detailed = crawl4ai_scrape(result.url)
```

### 3. 定时任务集成
```bash
# 定时抓取（添加到 crontab）
0 */6 * * * python3 crawl_page.py "https://example.com/updates" --json > /tmp/updates.json
```

## 注意事项

1. **首次运行**会自动下载 Playwright 浏览器（约 100MB）
2. **无头模式**默认启用，无需图形界面
3. **并发控制**如需大量抓取，建议使用 asyncio.Semaphore

## 升级路径

### 当前（Python 版）
- 完全可用，功能完整
- 无需 Docker

### 未来（Docker 版）
当网络恢复后，可并行部署 Docker 版本：
```bash
docker run -d --name crawl4ai -p 11234:11234 -p 11235:11235 unclecode/crawl4ai:latest
```

两者 API 兼容，可无缝切换。
