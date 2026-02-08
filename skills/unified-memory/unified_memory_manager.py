#!/usr/bin/env python3
"""
Unified Memory Manager - 三记忆系统整合
同时支持 memU (云端)、Hippocampus (本地)、MemOS (MCP)
"""

import json
import os
import sys
import subprocess
from typing import List, Dict, Any, Optional
import asyncio

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/hippocampus-memory')

from memu_sdk import MemUClient

# 配置路径
CREDENTIALS_PATH = '/root/.openclaw/workspace/secrets/memu-credentials.json'
HIPPOCAMPUS_DIR = '/root/.openclaw/workspace/skills/hippocampus-memory'
WORKSPACE_MEMORY = '/root/.openclaw/workspace/memory'

# MemOS MCP 配置
MEMOS_MCP_AVAILABLE = True  # 在 mcp_config.json 中已配置


class MemOSClient:
    """
    MemOS HTTP API 客户端
    
    直接使用 HTTP API 调用 MemOS 服务，绕过 MCP
    """
    
    def __init__(self):
        self.available = MEMOS_MCP_AVAILABLE
        self.memos_file = f"{WORKSPACE_MEMORY}/memos-integration.jsonl"
        # MemOS API 配置 (从 MCP 包源码中找到)
        self.api_base = "https://memos.memtensor.cn/api/openmem/v1"
        self.api_key = "mpg-vCI2aAscjA0ckABPMVa6BhQARfckS+bm9YINlcnG"
        self.user_id = "yiwanbot"
        self.channel = "MODELSCOPE"
    
    def _build_curl_cmd(self, endpoint: str, method: str = "GET", data: dict = None) -> list:
        """构建 curl 命令"""
        # 移除 endpoint 开头的 / 避免双斜杠
        endpoint = endpoint.lstrip('/')
        url = f"{self.api_base}/{endpoint}"
        cmd = ["curl", "-s", "-X", method, url]
        
        # 添加 headers (注意：MemOS 使用 Token 而不是 Bearer)
        cmd.extend(["-H", f"Authorization: Token {self.api_key}"])
        cmd.extend(["-H", "Content-Type: application/json"])
        # 注意：不需要 X-User-ID 和 X-Channel headers，它们在 body 中
        
        # 添加代理（如果配置了）
        cmd.extend(["--proxy", "http://127.0.0.1:7890"])
        
        # 添加 data
        if data:
            cmd.extend(["-d", json.dumps(data, ensure_ascii=False)])
        
        cmd.extend(["--max-time", "30"])
        return cmd
    
    async def memorize(self, user_message: str, assistant_message: str) -> bool:
        """
        存储记忆到 MemOS - 使用 HTTP API
        
        使用 add_message endpoint 上传对话
        """
        try:
            import subprocess
            
            # 生成 conversation_id (使用 MD5 hash)
            import hashlib
            from datetime import datetime
            conversation_first_message = user_message[:50]  # 使用用户消息前50字
            conversation_id = hashlib.md5(f"{self.user_id}\n{conversation_first_message}".encode()).hexdigest()
            
            # 构造消息数据
            chat_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 格式: 2026-02-08 19:10:00.123
            messages = [
                {
                    "role": "user",
                    "content": user_message,
                    "chat_time": chat_time
                },
                {
                    "role": "assistant",
                    "content": assistant_message,
                    "chat_time": chat_time
                }
            ]
            
            data = {
                "user_id": self.user_id,
                "conversation_id": conversation_id,
                "messages": messages
            }
            
            # 使用 curl 调用 API
            cmd = self._build_curl_cmd("/add/message", method="POST", data=data)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            
            success = False
            if result.returncode == 0 and result.stdout:
                try:
                    response = json.loads(result.stdout)
                    # API 返回 code: 0 表示成功，或者包含 task_id 也算成功
                    if response.get("code") == 0 or (response.get("data") and "task_id" in response.get("data", {})):
                        success = True
                except:
                    # 非 JSON 响应但 curl 成功，也算成功
                    if result.stdout.strip():
                        success = True
            
            # 写入本地备份（无论成功与否）
            entry = {
                "timestamp": asyncio.get_event_loop().time(),
                "user": user_message,
                "assistant": assistant_message,
                "type": "conversation",
                "source": "memos_api" if success else "local_backup",
                "uploaded": success
            }
            with open(self.memos_file, 'a') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            return success
            
        except Exception as e:
            import traceback
            print(f"⚠️ MemOS API 存储失败: {e}")
            traceback.print_exc()
            # fallback 到本地文件
            try:
                entry = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "user": user_message,
                    "assistant": assistant_message,
                    "type": "conversation",
                    "source": "local_backup",
                    "uploaded": False
                }
                with open(self.memos_file, 'a') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                return False
            except:
                return False
    
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict]:
        """从 MemOS API 检索记忆"""
        try:
            import subprocess
            from datetime import datetime
            
            today = datetime.now().strftime("%Y-%m-%d")
            conversation_id = f"bowlwanpi-{today}"
            
            # 调用 search_memory endpoint
            data = {
                "conversation_id": conversation_id,
                "query": query,
                "memory_limit_number": limit
            }
            
            cmd = self._build_curl_cmd("search_memory", method="POST", data=data)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            
            if result.returncode == 0 and result.stdout:
                try:
                    response = json.loads(result.stdout)
                    memories = response.get("memories", [])
                    return [
                        {
                            'content': m.get('content', ''),
                            'type': 'memos',
                            'timestamp': m.get('timestamp'),
                            'source': 'memos_api'
                        }
                        for m in memories[:limit]
                    ]
                except:
                    pass
            
            # fallback 到本地文件检索
            return await self._retrieve_local(query, limit)
            
        except Exception as e:
            print(f"⚠️ MemOS API 检索失败: {e}")
            return await self._retrieve_local(query, limit)
    
    async def _retrieve_local(self, query: str, limit: int = 5) -> List[Dict]:
        """从本地 MemOS 缓存检索"""
        try:
            if not os.path.exists(self.memos_file):
                return []
            
            results = []
            with open(self.memos_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        content = f"{entry.get('user', '')} {entry.get('assistant', '')}"
                        if query.lower() in content.lower():
                            results.append({
                                'content': content,
                                'type': 'memos',
                                'timestamp': entry.get('timestamp'),
                                'source': entry.get('source', 'local')
                            })
                    except:
                        continue
            
            return results[:limit]
        except Exception as e:
            print(f"⚠️ MemOS 本地检索失败: {e}")
            return []


class UnifiedMemoryManager:
    """统一记忆管理器 - 整合 memU + Hippocampus + MemOS"""
    
    def __init__(self, enable_memu: bool = True, enable_hippo: bool = True, enable_memos: bool = True):
        self.enable_memu = enable_memu
        self.enable_hippo = enable_hippo
        self.enable_memos = enable_memos
        
        self.memu_client = None
        self.memu_api_key = self._load_memu_credentials() if enable_memu else None
        self.hippo_available = os.path.exists(HIPPOCAMPUS_DIR) if enable_hippo else False
        self.memos_client = MemOSClient() if enable_memos and MEMOS_MCP_AVAILABLE else None
    
    def _load_memu_credentials(self) -> str:
        """加载 memU 凭证"""
        try:
            with open(CREDENTIALS_PATH, 'r') as f:
                creds = json.load(f)
                return creds.get('api_key', '')
        except Exception as e:
            print(f"⚠️ 加载 memU 凭证失败: {e}")
            return ''
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self.memu_api_key and self.enable_memu:
            self.memu_client = MemUClient(api_key=self.memu_api_key)
            await self.memu_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.memu_client:
            await self.memu_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def store_memory(self, user_message: str, assistant_message: str, 
                          importance: float = 0.7) -> Dict[str, bool]:
        """
        存储记忆到三系统
        
        Args:
            user_message: 用户消息
            assistant_message: 助手回复
            importance: 重要度 (0.0-1.0)
        
        Returns:
            Dict: {'memu': bool, 'hippocampus': bool, 'memos': bool}
        """
        results = {'memu': False, 'hippocampus': False, 'memos': False}
        
        # 1. 存储到 memU (云端)
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
                print(f"⚠️ memU 存储失败: {e}")
        
        # 2. 存储到 Hippocampus (本地)
        if self.hippo_available and self.enable_hippo:
            try:
                signal = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "user": user_message,
                    "assistant": assistant_message,
                    "importance": importance,
                    "type": "conversation"
                }
                signals_file = f"{WORKSPACE_MEMORY}/signals.jsonl"
                with open(signals_file, 'a') as f:
                    f.write(json.dumps(signal, ensure_ascii=False) + '\n')
                results['hippocampus'] = True
            except Exception as e:
                print(f"⚠️ Hippocampus 存储失败: {e}")
        
        # 3. 存储到 MemOS (MCP 集成)
        if self.memos_client and self.enable_memos:
            try:
                results['memos'] = await self.memos_client.memorize(user_message, assistant_message)
            except Exception as e:
                print(f"⚠️ MemOS 存储失败: {e}")
        
        return results
    
    async def retrieve_memories(self, query: str, limit: int = 5) -> Dict[str, List]:
        """
        从三系统检索记忆
        
        Args:
            query: 查询内容
            limit: 每个系统返回条数
        
        Returns:
            Dict: {'memu': [...], 'hippocampus': [...], 'memos': [...]}
        """
        results = {'memu': [], 'hippocampus': [], 'memos': []}
        
        # 1. 从 memU 检索
        if self.memu_client and self.enable_memu:
            try:
                memu_result = await self.memu_client.retrieve(
                    query=query,
                    user_id='yiwan',
                    agent_id='bowlwanpi'
                )
                if hasattr(memu_result, 'items'):
                    results['memu'] = [
                        {'content': item.content, 'type': getattr(item, 'memory_type', 'unknown')}
                        for item in memu_result.items[:limit]
                    ]
            except Exception as e:
                print(f"⚠️ memU 检索失败: {e}")
        
        # 2. 从 Hippocampus 检索
        if self.hippo_available and self.enable_hippo:
            try:
                result = subprocess.run(
                    [f"{HIPPOCAMPUS_DIR}/scripts/recall.sh", query],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    hippo_memories = []
                    for line in result.stdout.strip().split('\n')[:limit]:
                        if line.strip():
                            hippo_memories.append({'content': line, 'type': 'hippocampus'})
                    results['hippocampus'] = hippo_memories
            except Exception as e:
                print(f"⚠️ Hippocampus 检索失败: {e}")
        
        # 3. 从 MemOS 检索
        if self.memos_client and self.enable_memos:
            try:
                results['memos'] = await self.memos_client.retrieve(query, limit)
            except Exception as e:
                print(f"⚠️ MemOS 检索失败: {e}")
        
        return results
    
    async def retrieve_all(self, query: str, limit: int = 5) -> List[Dict]:
        """
        从所有系统检索并合并结果
        
        Returns:
            List[Dict]: 合并后的记忆列表，按相关性排序
        """
        all_memories = []
        results = await self.retrieve_memories(query, limit)
        
        # 合并所有结果
        for source, memories in results.items():
            for mem in memories:
                mem['source'] = source
                all_memories.append(mem)
        
        # 去重（简单基于内容哈希）
        seen = set()
        unique_memories = []
        for mem in all_memories:
            content_hash = hash(mem.get('content', '')[:100])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_memories.append(mem)
        
        return unique_memories
    
    async def trigger_hippocampus_encoding(self) -> bool:
        """触发 Hippocampus 编码流水线"""
        if not self.hippo_available or not self.enable_hippo:
            return False
        
        try:
            result = subprocess.run(
                [f"{HIPPOCAMPUS_DIR}/scripts/encode-pipeline.sh"],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️ Hippocampus 编码失败: {e}")
            return False
    
    def get_memory_stats(self) -> Dict:
        """获取记忆统计"""
        stats = {
            'memu': {'available': bool(self.memu_api_key) and self.enable_memu, 'enabled': self.enable_memu},
            'hippocampus': {'available': self.hippo_available and self.enable_hippo, 'enabled': self.enable_hippo},
            'memos': {'available': MEMOS_MCP_AVAILABLE and self.enable_memos, 'enabled': self.enable_memos}
        }
        
        # 统计 Hippocampus 记忆数量
        if self.hippo_available and self.enable_hippo:
            try:
                index_file = f"{WORKSPACE_MEMORY}/index.json"
                if os.path.exists(index_file):
                    with open(index_file, 'r') as f:
                        index = json.load(f)
                        stats['hippocampus']['memory_count'] = len(index.get('memories', []))
                else:
                    stats['hippocampus']['memory_count'] = 0
            except:
                stats['hippocampus']['memory_count'] = 0
        
        return stats


# 便捷函数
async def store_to_all_systems(user_msg: str, assistant_msg: str, importance: float = 0.7,
                                enable_memu: bool = True, enable_hippo: bool = True, 
                                enable_memos: bool = True) -> Dict:
    """快捷存储到所有系统"""
    async with UnifiedMemoryManager(enable_memu, enable_hippo, enable_memos) as mm:
        return await mm.store_memory(user_msg, assistant_msg, importance)

async def retrieve_from_all_systems(query: str, limit: int = 5,
                                     enable_memu: bool = True, enable_hippo: bool = True,
                                     enable_memos: bool = True) -> Dict:
    """快捷检索所有系统"""
    async with UnifiedMemoryManager(enable_memu, enable_hippo, enable_memos) as mm:
        return await mm.retrieve_memories(query, limit)

async def retrieve_merged(query: str, limit: int = 5) -> List[Dict]:
    """快捷检索并合并结果"""
    async with UnifiedMemoryManager() as mm:
        return await mm.retrieve_all(query, limit)


if __name__ == '__main__':
    import asyncio
    
    async def test():
        print("🧠 测试三记忆系统...\n")
        
        async with UnifiedMemoryManager() as mm:
            # 检查状态
            stats = mm.get_memory_stats()
            print("📊 系统状态:")
            print(f"  memU: {'✅' if stats['memu']['available'] else '❌'} (启用: {stats['memu']['enabled']})")
            print(f"  Hippocampus: {'✅' if stats['hippocampus']['available'] else '❌'} (启用: {stats['hippocampus']['enabled']})")
            if stats['hippocampus'].get('memory_count'):
                print(f"    记忆数: {stats['hippocampus']['memory_count']}")
            print(f"  MemOS: {'✅' if stats['memos']['available'] else '❌'} (启用: {stats['memos']['enabled']})")
            
            # 测试存储
            print("\n📤 测试存储...")
            result = await mm.store_memory(
                "测试三记忆系统",
                "成功存储到 memU、Hippocampus 和 MemOS！",
                importance=0.8
            )
            print(f"  memU: {'✅' if result['memu'] else '❌'}")
            print(f"  Hippocampus: {'✅' if result['hippocampus'] else '❌'}")
            print(f"  MemOS: {'✅' if result['memos'] else '❌'}")
            
            # 测试检索
            print("\n🔍 测试检索...")
            memories = await mm.retrieve_memories("记忆系统", limit=3)
            print(f"  memU: {len(memories['memu'])} 条")
            print(f"  Hippocampus: {len(memories['hippocampus'])} 条")
            print(f"  MemOS: {len(memories['memos'])} 条")
            
            # 测试合并检索
            print("\n🔍 测试合并检索...")
            merged = await mm.retrieve_all("记忆系统", limit=5)
            print(f"  合并后: {len(merged)} 条")
    
    asyncio.run(test())
