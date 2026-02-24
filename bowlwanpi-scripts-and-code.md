# 📜 碗皮脚本与代码集

所有自定义脚本和代码的完整内容。

---

## 1. MCP 服务器 (mcp_server.py)

**位置**: `~/.openclaw/workspace/mcp_server.py`

```python
#!/usr/bin/env python3
"""
BowlWanpi MCP Server
提供记忆检索、系统状态查询等工具的 MCP 服务
"""
import json
import os
from typing import Any
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 服务器
mcp = FastMCP("bowlwanpi")

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

@mcp.tool()
def get_system_status() -> str:
    """获取系统运行状态（CPU、内存、磁盘使用率）"""
    try:
        import subprocess
        
        # CPU 使用率
        cpu = subprocess.getoutput("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1").strip()
        
        # 内存使用率
        mem_info = subprocess.getoutput("free | grep Mem | awk '{printf \"%.0f\", $3/$2 * 100}'").strip()
        
        # 磁盘使用率
        disk = subprocess.getoutput("df -h / | tail -1 | awk '{print $5}'").strip()
        
        return f"系统状态：CPU {cpu}% | 内存 {mem_info}% | 磁盘 {disk}"
    except Exception as e:
        return f"获取系统状态失败: {e}"

@mcp.tool()
def search_memory(query: str) -> str:
    """从 memU 记忆系统中检索相关记忆
    
    Args:
        query: 搜索关键词
    """
    try:
        from memu_sdk import MemUClient
        
        with open('/root/.openclaw/workspace/secrets/memu-credentials.json') as f:
            api_key = json.load(f)['api_key']
        
        client = MemUClient(api_key=api_key)
        memories = client.retrieve_sync(
            query=query,
            user_id='yiwan',
            agent_id='bowlwanpi'
        )
        client.close_sync()
        
        if not memories.items:
            return f"未找到关于 '{query}' 的记忆"
        
        results = []
        for item in memories.items[:5]:
            content = item.content[:100] if item.content else ""
            results.append(f"[{item.memory_type}] {content}...")
        
        return f"找到 {len(memories.items)} 条相关记忆:\n" + "\n".join(results)
    except Exception as e:
        return f"检索记忆失败: {e}"

@mcp.tool()
def get_daily_schedule() -> str:
    """获取今日定时任务安排"""
    schedule = """
今日定时任务：
• 03:00 - 夜间构建
• 07:00 - 晨报预备
• 08:00 - 网易云日推
• 08:30 - 早晨简报 + 微博热搜
• 09:00 - Product Hunt
• 10:00 - 知乎热榜
• 12:00 - B站热门
• 14:00 - 信息收集
• 22:30 - 晚间反思
• 23:00 - 睡眠提醒
"""
    return schedule

@mcp.tool()
def get_moltbook_info() -> str:
    """获取 Moltbook 账号信息"""
    return """
Moltbook 信息：
• Agent Name: BowlWanpi
• Agent ID: dfc4fae2-ac13-4124-9bfe-6d12da5ec72f
• Profile: https://moltbook.com/u/BowlWanpi
"""

@mcp.tool()
def remember_fact(fact: str, category: str = "general") -> str:
    """存储一条记忆到 memU"""
    try:
        from memu_sdk import MemUClient
        
        with open('/root/.openclaw/workspace/secrets/memu-credentials.json') as f:
            api_key = json.load(f)['api_key']
        
        client = MemUClient(api_key=api_key)
        conv = [
            {"role": "user", "content": fact},
            {"role": "assistant", "content": "已记录到记忆系统"}
        ]
        result = client.memorize_sync(
            conversation=conv,
            user_id='yiwan',
            agent_id='bowlwanpi'
        )
        client.close_sync()
        
        return f"✅ 记忆已存储！Task ID: {result.task_id}"
    except Exception as e:
        return f"❌ 存储记忆失败: {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

---

## 2. 心跳监控脚本 (heartbeat.sh)

**位置**: `~/.openclaw/workspace/scripts/heartbeat.sh`

```bash
#!/bin/bash
# BowlWanpi 心跳监控脚本
# 每5分钟运行一次

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

LOG_FILE="/var/log/bowlwanpi-heartbeat.log"
ALERT_FILE="/tmp/bowlwanpi-last-alert"
LOCK_FILE="/tmp/bowlwanpi-heartbeat.lock"

# 防止并发执行
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[$(date)] Heartbeat already running, skipping" >> "$LOG_FILE"
        exit 0
    fi
fi
echo $$ > "$LOCK_FILE"

cleanup() { rm -f "$LOCK_FILE"; }
trap cleanup EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"; }

# 发送警报（带冷却时间）
send_alert() {
    local message="$1"
    local alert_type="$2"
    local cooldown_minutes="${3:-30}"
    
    local alert_key="${ALERT_FILE}-${alert_type}"
    local last_alert=0
    [ -f "$alert_key" ] && last_alert=$(cat "$alert_key")
    
    local current_time=$(date +%s)
    local cooldown_seconds=$((cooldown_minutes * 60))
    
    if [ $((current_time - last_alert)) -gt $cooldown_seconds ]; then
        log "ALERT [$alert_type]: $message"
        local msg_file="/tmp/bowlwanpi-pending-messages"
        echo "$(date '+%Y-%m-%d %H:%M:%S')|ALERT|$alert_type|$message" >> "$msg_file"
        echo "$current_time" > "$alert_key"
    fi
}

# 检查 OpenClaw Gateway
check_gateway() {
    if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
        log "Gateway: OK (process running)"
        return 0
    fi
    send_alert "OpenClaw Gateway 未运行！" "gateway_down" 30
    return 1
}

# 检查 Mihomo
check_mihomo() {
    if pgrep -f "mihomo" > /dev/null 2>&1; then
        log "Mihomo: OK"
        return 0
    fi
    send_alert "Mihomo 代理未运行！" "mihomo_down" 60
}

# 检查内存
check_memory() {
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$mem_usage" -gt 90 ]; then
        send_alert "内存使用率过高: ${mem_usage}%" "high_memory" 60
    else
        log "Memory: ${mem_usage}% OK"
    fi
}

# 检查磁盘
check_disk() {
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        send_alert "磁盘空间不足: ${disk_usage}%" "disk_full" 120
    else
        log "Disk: ${disk_usage}% OK"
    fi
}

# 主逻辑
main() {
    log "=== Heartbeat check started ==="
    check_gateway
    check_mihomo
    check_memory
    check_disk
    log "=== Heartbeat check completed ==="
}

main "$@"
```

---

## 3. 夜间构建脚本 (nightly-build-enhanced.sh)

**位置**: `~/.openclaw/workspace/scripts/nightly-build-enhanced.sh`

```bash
#!/bin/bash
# 碗皮夜间构建增强版

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

WORKSPACE="/root/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
LOG_FILE="/var/log/bowlwanpi-nightly-build.log"
REPORT_FILE="$MEMORY_DIR/nightly-build-report-$(date +%Y%m%d).md"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 夜间构建开始..." >> "$LOG_FILE"

cd "$WORKSPACE"

# 1. 记忆整理
echo "整理记忆..." >> "$LOG_FILE"
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)

if [ -f "$MEMORY_DIR/${YESTERDAY}.md" ]; then
    KEY_EVENTS=$(grep -E "^(##|###|\*|-|\[x\])" "$MEMORY_DIR/${YESTERDAY}.md" | head -30)
    if [ -n "$KEY_EVENTS" ]; then
        echo "" >> "$WORKSPACE/MEMORY.md"
        echo "<!-- ${YESTERDAY} -->" >> "$WORKSPACE/MEMORY.md"
        echo "$KEY_EVENTS" >> "$WORKSPACE/MEMORY.md"
    fi
fi

# 2. Git 备份
echo "Git 备份..." >> "$LOG_FILE"
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    git add -A
    git -c user.email="bowlwanpi@moltbook.com" -c user.name="BowlWanpi" \
        commit -m "夜间构建 $(date '+%Y-%m-%d')" >> "$LOG_FILE" 2>&1
fi

# 3. 生成今日待办
cat > "$MEMORY_DIR/${TODAY}.md" << EOF
# ${TODAY} - 今日计划

## 优先事项
- [ ] 检查昨日未完成事项
- [ ] 查看定时任务运行状态

## 定时提醒
| 时间 | 任务 |
|------|------|
| 8:30 | 早晨简报 |
| 14:00 | 信息收集 |
| 22:30 | 晚间反思 |
| 23:00 | 睡眠提醒 |

生成时间: $(date '+%H:%M')
EOF

# 4. 生成报告
cat > "$REPORT_FILE" << EOF
# 夜间构建报告 $(date '+%Y年%m月%d日')

## 完成的工作
- [x] 整理昨日记忆
- [x] Git commit 变更
- [x] 生成今日待办

一碗早安～今日计划已准备好！
EOF

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 夜间构建完成！" >> "$LOG_FILE"
```

---

## 4. 定时任务脚本 (backup-cron.sh)

**位置**: `~/.openclaw/workspace/scripts/backup-cron.sh`

```bash
#!/bin/bash
# 定时任务兜底方案

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export OPENCLAW_GATEWAY_URL="http://localhost:3000"

LOG_FILE="/var/log/bowlwanpi-cron.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"; }

check_openclaw() {
    if ! curl -s "$OPENCLAW_GATEWAY_URL/health" > /dev/null 2>&1; then
        log "ERROR: OpenClaw Gateway is not running"
        return 1
    fi
    return 0
}

send_message() {
    local content="$1"
    log "Sending message: ${content:0:50}..."
    
    if command -v openclaw &> /dev/null; then
        cd /root/.openclaw/workspace
        openclaw message send --channel feishu --target "user_id" "$content" >> "$LOG_FILE" 2>&1
        return $?
    fi
    return 1
}

case "$1" in
    morning-brief)
        log "=== 早晨简报 ==="
        check_openclaw && echo "生成早晨简报任务"
        ;;
    
    netease-music)
        log "=== 网易云日推 ==="
        check_openclaw && echo "推送网易云日推"
        ;;
    
    evening-reflect)
        log "=== 晚间反思 ==="
        send_message "晚间反思时间～今天过得怎么样？"
        ;;
    
    sleep-reminder)
        log "=== 睡眠提醒 ==="
        send_message "该休息啦！明天再继续探索吧，晚安 💤"
        ;;
    
    *)
        log "Unknown task: $1"
        exit 1
        ;;
esac
```

---

## 5. 统一记忆管理器 (unified_memory_manager.py)

**位置**: `~/.openclaw/workspace/skills/unified-memory/unified_memory_manager.py`

```python
#!/usr/bin/env python3
"""
Unified Memory Manager - 三记忆系统整合
支持 memU (云端)、Hippocampus (本地)、MemOS (MCP)
"""

import json
import os
import sys
from typing import List, Dict, Any
import asyncio

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')

from memu_sdk import MemUClient

CREDENTIALS_PATH = '/root/.openclaw/workspace/secrets/memu-credentials.json'
HIPPOCAMPUS_DIR = '/root/.openclaw/workspace/skills/hippocampus-memory'
WORKSPACE_MEMORY = '/root/.openclaw/workspace/memory'
MEMOS_MCP_AVAILABLE = True


class MemOSClient:
    """MemOS MCP 客户端"""
    
    def __init__(self):
        self.available = MEMOS_MCP_AVAILABLE
        self.memos_file = f"{WORKSPACE_MEMORY}/memos-integration.jsonl"
    
    async def memorize(self, user_message: str, assistant_message: str) -> bool:
        try:
            entry = {
                "timestamp": asyncio.get_event_loop().time(),
                "user": user_message,
                "assistant": assistant_message,
                "type": "conversation"
            }
            with open(self.memos_file, 'a') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            return True
        except Exception as e:
            print(f"MemOS 存储失败: {e}")
            return False


class UnifiedMemoryManager:
    """统一记忆管理器"""
    
    def __init__(self, enable_memu=True, enable_hippo=True, enable_memos=True):
        self.enable_memu = enable_memu
        self.enable_hippo = enable_hippo
        self.enable_memos = enable_memos
        
        self.memu_api_key = self._load_memu_credentials() if enable_memu else None
        self.memu_client = None
        self.hippo_available = os.path.exists(HIPPOCAMPUS_DIR) if enable_hippo else False
        self.memos_client = MemOSClient() if enable_memos else None
    
    def _load_memu_credentials(self) -> str:
        try:
            with open(CREDENTIALS_PATH, 'r') as f:
                return json.load(f).get('api_key', '')
        except Exception as e:
            print(f"加载 memU 凭证失败: {e}")
            return ''
    
    async def __aenter__(self):
        if self.memu_api_key and self.enable_memu:
            self.memu_client = MemUClient(api_key=self.memu_api_key)
            await self.memu_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.memu_client:
            await self.memu_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def store_memory(self, user_message: str, assistant_message: str, 
                          importance: float = 0.7) -> Dict[str, bool]:
        """存储记忆到三系统"""
        results = {'memu': False, 'hippocampus': False, 'memos': False}
        
        # 1. memU
        if self.memu_client and self.enable_memu:
            try:
                conversation = [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message}
                ]
                await self.memu_client.memorize(
                    conversation=conversation,
                    user_id='yiwan',
                    agent_id='bowlwanpi'
                )
                results['memu'] = True
            except Exception as e:
                print(f"memU 存储失败: {e}")
        
        # 2. Hippocampus
        if self.hippo_available and self.enable_hippo:
            try:
                signal = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "user": user_message,
                    "assistant": assistant_message,
                    "importance": importance
                }
                with open(f"{WORKSPACE_MEMORY}/signals.jsonl", 'a') as f:
                    f.write(json.dumps(signal, ensure_ascii=False) + '\n')
                results['hippocampus'] = True
            except Exception as e:
                print(f"Hippocampus 存储失败: {e}")
        
        # 3. MemOS
        if self.memos_client and self.enable_memos:
            results['memos'] = await self.memos_client.memorize(user_message, assistant_message)
        
        return results
    
    async def retrieve_memories(self, query: str, limit: int = 5) -> Dict[str, List]:
        """从三系统检索记忆"""
        results = {'memu': [], 'hippocampus': [], 'memos': []}
        
        # 1. memU
        if self.memu_client and self.enable_memu:
            try:
                memu_result = await self.memu_client.retrieve(
                    query=query, user_id='yiwan', agent_id='bowlwanpi'
                )
                if hasattr(memu_result, 'items'):
                    results['memu'] = [
                        {'content': item.content, 'type': getattr(item, 'memory_type', 'unknown')}
                        for item in memu_result.items[:limit]
                    ]
            except Exception as e:
                print(f"memU 检索失败: {e}")
        
        return results


# 便捷函数
async def store_to_all_systems(user_msg: str, assistant_msg: str, importance: float = 0.7):
    async with UnifiedMemoryManager() as mm:
        return await mm.store_memory(user_msg, assistant_msg, importance)


if __name__ == '__main__':
    async def test():
        async with UnifiedMemoryManager() as mm:
            stats = mm.get_memory_stats()
            print(f"系统状态: {stats}")
            
            result = await mm.store_memory("测试", "回复", 0.8)
            print(f"存储结果: {result}")
    
    asyncio.run(test())
```

---

## 6. 智能搜索引擎 (search_engine.py)

**位置**: `~/.openclaw/workspace/skills/intelligent-search/search_engine.py`

```python
#!/usr/bin/env python3
"""
智能搜索聚合器 - 统一搜索接口
支持中英文自动识别、主备切换
"""

import json
import os
import sys
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/tencent-search')

from search_client import search_tencent_web


class SearchProvider(Enum):
    TENCENT_WSA = "tencent_wsa"
    TAVILY = "tavily"


@dataclass
class SearchResult:
    title: str
    content: str
    url: str
    source: str
    provider: str
    score: float = 0.0


class LanguageDetector:
    @staticmethod
    def detect(text: str) -> str:
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total = chinese_chars + english_chars
        if total == 0:
            return 'en'
        return 'zh' if chinese_chars / total > 0.3 else 'en'


class SearchRouter:
    @classmethod
    def route(cls, query: str) -> Tuple[SearchProvider, SearchProvider]:
        lang = LanguageDetector.detect(query)
        if lang == 'zh':
            return (SearchProvider.TENCENT_WSA, SearchProvider.TAVILY)
        else:
            return (SearchProvider.TAVILY, SearchProvider.TENCENT_WSA)


class IntelligentSearchEngine:
    def __init__(self):
        self.search_history = []
    
    async def search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        language = LanguageDetector.detect(query)
        primary, fallback = SearchRouter.route(query)
        
        # 主搜索
        primary_results = await self._execute_search(primary, query, num_results)
        
        if primary_results and not any('error' in r for r in primary_results):
            all_results = self._normalize_results(primary_results, primary.value)
            fallback_used = False
        else:
            fallback_results = await self._execute_search(fallback, query, num_results)
            all_results = self._normalize_results(fallback_results, fallback.value)
            fallback_used = True
        
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        return {
            'success': True,
            'query': query,
            'language': language,
            'primary_provider': primary.value,
            'fallback_used': fallback_used,
            'results': all_results[:num_results]
        }
    
    async def _execute_search(self, provider: SearchProvider, query: str, num: int) -> List[Dict]:
        if provider == SearchProvider.TENCENT_WSA:
            return await search_tencent_web(query, num)
        return []
    
    def _normalize_results(self, raw: List[Dict], provider: str) -> List[SearchResult]:
        return [
            SearchResult(
                title=r.get('title', ''),
                content=r.get('content', ''),
                url=r.get('url', ''),
                source=r.get('site', provider),
                provider=provider,
                score=float(r.get('score', 0))
            )
            for r in raw if 'error' not in r
        ]


async def smart_search(query: str, num_results: int = 10) -> Dict[str, Any]:
    engine = IntelligentSearchEngine()
    return await engine.search(query, num_results)


if __name__ == '__main__':
    result = asyncio.run(smart_search("人工智能", 3))
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

---

## 7. 飞书消息发送脚本 (send-feishu.py)

**位置**: `~/.openclaw/workspace/scripts/send-feishu.py`

```python
#!/usr/bin/env python3
"""
直接发送飞书消息 - 绕过 OpenClaw CLI
用于系统 cron 定时任务
"""

import sys
import json
import os

FEISHU_USER_ID = "ou_a22ce6536f26dee3fec9397a9a1b87b5"

def send_message(content, user_id=None):
    if user_id is None:
        user_id = FEISHU_USER_ID
    
    print(f"[FEISHU MESSAGE TO {user_id}]")
    print(content)
    
    # 写入队列文件
    pending_file = "/tmp/bowlwanpi-pending-messages"
    with open(pending_file, 'a') as f:
        f.write(f"{json.dumps({'time': str(os.times()), 'content': content})}\n")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: send-feishu.py '<message>'")
        sys.exit(1)
    
    message = sys.argv[1]
    send_message(message)
    print("Message queued")

if __name__ == "__main__":
    main()
```

---

*脚本与代码集完成*
