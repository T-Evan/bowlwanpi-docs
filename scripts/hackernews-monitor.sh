#!/bin/bash
# Hacker News OpenClaw 监控脚本
# 每小时检查 HN 上 OpenClaw 相关的新帖子和讨论

export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

CACHE_FILE="/root/.openclaw/workspace/memory/hackernews-openclaw-cache.json"
LOG_FILE="/var/log/bowlwanpi-hackernews.log"
PENDING_MSG="/tmp/bowlwanpi-hackernews-pending.txt"

# 初始化缓存文件
if [ ! -f "$CACHE_FILE" ]; then
    echo "[]" > "$CACHE_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking Hacker News for OpenClaw..." >> "$LOG_FILE"

# 使用 Algolia API 搜索 Hacker News（最近24小时）
YESTERDAY=$(($(date +%s) - 86400))
RESPONSE=$(curl -s --max-time 30 \
    "https://hn.algolia.com/api/v1/search?query=openclaw&tags=story&numericFilters=created_at_i>${YESTERDAY}&hitsPerPage=10" \
    2>/dev/null)

if [ -z "$RESPONSE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Failed to fetch HN data" >> "$LOG_FILE"
    exit 1
fi

# 检查 JSON 有效性
echo "$RESPONSE" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Invalid JSON response" >> "$LOG_FILE"
    exit 1
fi

# 解析并检查新帖子 - 使用管道传递数据
echo "$RESPONSE" | python3 << 'PYTHON_SCRIPT'
import sys, json, os

cache_file = "/root/.openclaw/workspace/memory/hackernews-openclaw-cache.json"
pending_file = "/tmp/bowlwanpi-hackernews-pending.txt"

try:
    response_text = sys.stdin.read()
    data = json.loads(response_text)
    
    # 读取缓存
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except:
        cache = []
    
    cached_ids = {item.get('objectID') for item in cache}
    hits = data.get('hits', [])
    new_posts = []
    
    for hit in hits:
        post_id = hit.get('objectID')
        if post_id and post_id not in cached_ids:
            new_posts.append(hit)
            cache.append(hit)
    
    # 保存更新后的缓存（只保留最近50条）
    with open(cache_file, 'w') as f:
        json.dump(cache[-50:], f, indent=2)
    
    # 如果有新帖子，写入待发送队列
    if new_posts:
        with open(pending_file, 'w') as f:
            for post in new_posts:
                title = post.get('title', '')
                url = post.get('url', '') or f"https://news.ycombinator.com/item?id={post.get('objectID')}"
                hn_url = f"https://news.ycombinator.com/item?id={post.get('objectID')}"
                author = post.get('author', '')
                points = post.get('points', 0)
                comments = post.get('num_comments', 0)
                
                msg = f"🔥 HN New: {title}\n"
                msg += f"👤 {author} | ⬆️ {points} | 💬 {comments}\n"
                msg += f"🔗 {url}\n"
                msg += f"📰 {hn_url}\n"
                msg += "---\n"
                f.write(msg)
        
        print(f"FOUND_NEW:{len(new_posts)}")
    else:
        print("NO_NEW")
        
except Exception as e:
    print(f"ERROR:{e}")
PYTHON_SCRIPT

RESULT=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    hits = data.get('hits', [])
    print(f'TOTAL:{len(hits)}')
except Exception as e:
    print(f'ERROR:{e}')
")

echo "[$(date '+%Y-%m-%d %H:%M:%S')] $RESULT" >> "$LOG_FILE"

# 检查是否有新消息待发送
if [ -f "$PENDING_MSG" ] && [ -s "$PENDING_MSG" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] New posts found, queued for delivery" >> "$LOG_FILE"
fi
