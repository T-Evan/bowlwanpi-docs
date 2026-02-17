#!/usr/bin/env python3
"""
Unified Memory Manager v3.0 - 四记忆系统整合
支持 memU (云端)、Hippocampus (本地)、MemOS (MCP)、QMDR (本地向量搜索)
"""

import json
import os
import sys
import subprocess
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/hippocampus-memory')

try:
    from memu_sdk import MemUClient
except ImportError:
    MemUClient = None
    print("⚠️ memU SDK not available")

# 配置路径
CREDENTIALS_PATH = '/root/.openclaw/workspace/secrets/memu-credentials.json'
HIPPOCAMPUS_DIR = '/root/.openclaw/workspace/skills/hippocampus-memory'
WORKSPACE_MEMORY = '/root/.openclaw/workspace/memory'
QMD_COLLECTION = 'memory'

# MemOS MCP 配置
MEMOS_MCP_AVAILABLE = True

# QMDR 配置
QMD_AVAILABLE = os.path.exists(os.path.expanduser('~/.bun/bin/qmd'))


class QMDRClient:
    """
    QMDR 本地向量搜索客户端
    提供快速的本地语义检索能力
    """
    
    def __init__(self, collection: str = QMD_COLLECTION):
        self.collection = collection
        self.available = QMD_AVAILABLE
        self.qmd_path = os.path.expanduser('~/.bun/bin/qmd')
        self.memory_dir = WORKSPACE_MEMORY
        
    def _run_qmd(self, args: List[str], timeout: int = 10) -> Tuple[bool, str]:
        """运行 qmd 命令"""
        if not self.available:
            return False, "QMDR not available"
        
        env = os.environ.copy()
        env['PATH'] = f"{os.path.expanduser('~/.bun/bin')}:{env.get('PATH', '')}"
        env['QMD_ALLOW_SQLITE_EXTENSIONS'] = '1'
        
        try:
            result = subprocess.run(
                [self.qmd_path] + args,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def index_document(self, filepath: str, metadata: Dict[str, Any] = None) -> bool:
        """索引文档到 QMDR - 使用 update 命令增量更新"""
        if not os.path.exists(filepath):
            return False
        
        # QMD 使用 collection-based 索引，我们调用 update 来增量更新
        # 这会重新扫描所有 collections 并索引新文件
        success, output = self._run_qmd(['update'], timeout=60)
        
        # update 可能部分失败但前面 collections 成功，只要有 Indexed 输出就算成功
        if 'Indexed:' in output or 'Indexing:' in output:
            return True
        
        return success
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """使用 QMDR 搜索"""
        success, output = self._run_qmd([
            'search', query,
            '--collection', self.collection,
            '--limit', str(limit)
        ])
        
        if not success:
            return []
        
        # 解析输出
        results = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.startswith('qmd://'):
                # 解析 qmd://memory/file.md:line #hash
                parts = line.split()
                if len(parts) >= 2:
                    uri = parts[0]
                    score = 0.0
                    
                    # 尝试提取分数
                    for part in parts:
                        if 'Score:' in part:
                            try:
                                score = float(part.replace('Score:', '').replace('%', ''))
                            except:
                                pass
                    
                    results.append({
                        'uri': uri,
                        'score': score,
                        'source': 'qmdr'
                    })
        
        return results
    
    def get_document(self, filename: str) -> Optional[str]:
        """获取完整文档内容"""
        filepath = os.path.join(self.memory_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                pass
        return None
    
    def reindex_all(self) -> Dict[str, Any]:
        """重新索引所有记忆文档"""
        if not self.available:
            return {'success': False, 'error': 'QMDR not available'}
        
        indexed = 0
        failed = 0
        
        # 扫描 memory 目录下的所有 md 文件
        for root, dirs, files in os.walk(self.memory_dir):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    if self.index_document(filepath):
                        indexed += 1
                    else:
                        failed += 1
        
        return {
            'success': True,
            'indexed': indexed,
            'failed': failed
        }


class MemOSClient:
    """MemOS HTTP API 客户端"""
    
    def __init__(self):
        self.available = MEMOS_MCP_AVAILABLE
        self.memos_file = f"{WORKSPACE_MEMORY}/memos-integration.jsonl"
        self.api_base = "https://memos.memtensor.cn/api/openmem/v1"
        self.api_key = "mpg-vCI2aAscjA0ckABPMVa6BhQARfckS+bm9YINlcnG"
        self.user_id = "yiwanbot"
        self.channel = "MODELSCOPE"
    
    def _build_curl_cmd(self, endpoint: str, method: str = "GET", data: dict = None) -> list:
        endpoint = endpoint.lstrip('/')
        url = f"{self.api_base}/{endpoint}"
        cmd = ["curl", "-s", "-X", method, url]
        cmd.extend(["-H", f"Authorization: Token {self.api_key}"])
        cmd.extend(["-H", "Content-Type: application/json"])
        
        # 检查代理
        try:
            proxy_check = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
                 '--max-time', '2', '--proxy', 'http://127.0.0.1:7890', 'https://www.google.com'],
                capture_output=True, text=True, timeout=3
            )
            if proxy_check.stdout.strip() == '200':
                cmd.extend(["--proxy", "http://127.0.0.1:7890"])
        except:
            pass
        
        if data:
            cmd.extend(["-d", json.dumps(data, ensure_ascii=False)])
        
        cmd.extend(["--max-time", "10"])
        return cmd
    
    async def memorize(self, user_message: str, assistant_message: str) -> bool:
        """存储记忆到 MemOS"""
        data = {
            "content": f"User: {user_message}\nAssistant: {assistant_message}",
            "channel": self.channel,
            "user_id": self.user_id,
            "type": "conversation"
        }
        
        cmd = self._build_curl_cmd("/memorize", "POST", data)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                response = json.loads(result.stdout)
                return response.get('success', False)
        except:
            pass
        
        return False
    
    async def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """从 MemOS 检索记忆"""
        data = {
            "query": query,
            "user_id": self.user_id,
            "channel": self.channel,
            "limit": limit
        }
        
        cmd = self._build_curl_cmd("/retrieve", "POST", data)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                response = json.loads(result.stdout)
                memories = response.get('memories', [])
                return [{'content': m.get('content', ''), 'source': 'memos'} for m in memories]
        except:
            pass
        
        return []


class UnifiedMemoryManagerV3:
    """
    四记忆系统统一管理器 (v3.0)
    集成：memU + Hippocampus + MemOS + QMDR
    """
    
    def __init__(
        self,
        enable_memu: bool = True,
        enable_hippo: bool = True,
        enable_memos: bool = True,
        enable_qmdr: bool = True,
        user_id: str = 'yiwan',
        agent_id: str = 'bowlwanpi'
    ):
        self.user_id = user_id
        self.agent_id = agent_id
        
        # 初始化各系统
        self.memu_client = None
        self.hippo_dir = HIPPOCAMPUS_DIR
        self.memos_client = MemOSClient() if enable_memos else None
        self.qmdr_client = QMDRClient() if enable_qmdr else None
        
        # 启用状态
        self.enabled = {
            'memu': enable_memu and MemUClient is not None,
            'hippo': enable_hippo,
            'memos': enable_memos and self.memos_client and self.memos_client.available,
            'qmdr': enable_qmdr and self.qmdr_client and self.qmdr_client.available
        }
        
        # 初始化 memU
        if self.enabled['memu']:
            try:
                if os.path.exists(CREDENTIALS_PATH):
                    with open(CREDENTIALS_PATH, 'r') as f:
                        creds = json.load(f)
                        self.memu_api_key = creds.get('api_key')
                else:
                    self.memu_api_key = None
                    self.enabled['memu'] = False
            except:
                self.enabled['memu'] = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self.enabled['memu'] and self.memu_api_key:
            self.memu_client = MemUClient(api_key=self.memu_api_key)
            await self.memu_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.memu_client:
            await self.memu_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def store_memory(
        self,
        user_message: str,
        assistant_message: str,
        importance: float = 0.5,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, bool]:
        """
        存储记忆到所有启用的系统
        
        Returns:
            {'memu': True/False, 'hippo': True/False, 'memos': True/False, 'qmdr': True/False}
        """
        results = {'memu': False, 'hippo': False, 'memos': False, 'qmdr': False}
        
        # 1. memU (云端)
        if self.enabled['memu'] and self.memu_client:
            try:
                await self.memu_client.memorize(
                    conversation=[
                        {'role': 'user', 'content': user_message},
                        {'role': 'assistant', 'content': assistant_message}
                    ],
                    user_id=self.user_id,
                    agent_id=self.agent_id
                )
                results['memu'] = True
            except Exception as e:
                print(f"memU store error: {e}")
        
        # 2. Hippocampus (本地文件)
        if self.enabled['hippo']:
            try:
                hippo_script = f"{self.hippo_dir}/scripts/add_memory.py"
                if os.path.exists(hippo_script):
                    subprocess.run([
                        'python3', hippo_script,
                        user_message,
                        assistant_message,
                        str(importance)
                    ], capture_output=True, timeout=5)
                    results['hippo'] = True
            except Exception as e:
                print(f"Hippo store error: {e}")
        
        # 3. MemOS (MCP)
        if self.enabled['memos'] and self.memos_client:
            try:
                results['memos'] = await self.memos_client.memorize(
                    user_message, assistant_message
                )
            except Exception as e:
                print(f"MemOS store error: {e}")
        
        # 4. QMDR (本地向量)
        # 实时索引：保存到文件后立即索引
        if self.enabled['qmdr'] and self.qmdr_client:
            try:
                # 保存到本地记忆文件
                daily_file = f"{WORKSPACE_MEMORY}/{datetime.now().strftime('%Y-%m-%d')}.md"
                with open(daily_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n## {datetime.now().strftime('%H:%M')}\n")
                    f.write(f"**User:** {user_message}\n\n")
                    f.write(f"**Assistant:** {assistant_message}\n")
                
                # 实时索引该文件
                index_success = self.qmdr_client.index_document(daily_file)
                if index_success:
                    results['qmdr'] = True
                else:
                    print(f"QMDR index warning: failed to index {daily_file}")
                    # 文件已保存，标记为部分成功
                    results['qmdr'] = True
            except Exception as e:
                print(f"QMDR store error: {e}")
        
        return results
    
    async def retrieve_memories(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        从所有启用的系统检索记忆
        
        Returns:
            {'memu': [...], 'hippo': [...], 'memos': [...], 'qmdr': [...]}
        """
        results = {'memu': [], 'hippo': [], 'memos': [], 'qmdr': []}
        
        # 1. memU (云端)
        if self.enabled['memu'] and self.memu_client:
            try:
                memu_results = await self.memu_client.retrieve(
                    query=query,
                    user_id=self.user_id,
                    agent_id=self.agent_id
                )
                results['memu'] = [
                    {'content': r.get('content', ''), 'source': 'memu', 'type': r.get('type', 'unknown')}
                    for r in memu_results
                ]
            except Exception as e:
                print(f"memU retrieve error: {e}")
        
        # 2. Hippocampus (本地)
        if self.enabled['hippo']:
            try:
                hippo_script = f"{self.hippo_dir}/scripts/query.py"
                if os.path.exists(hippo_script):
                    result = subprocess.run(
                        ['python3', hippo_script, query, str(limit)],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        for line in result.stdout.strip().split('\n'):
                            if line:
                                results['hippo'].append({
                                    'content': line,
                                    'source': 'hippocampus'
                                })
            except Exception as e:
                print(f"Hippo retrieve error: {e}")
        
        # 3. MemOS (MCP)
        if self.enabled['memos'] and self.memos_client:
            try:
                results['memos'] = await self.memos_client.retrieve(query, limit)
            except Exception as e:
                print(f"MemOS retrieve error: {e}")
        
        # 4. QMDR (本地向量搜索)
        if self.enabled['qmdr'] and self.qmdr_client:
            try:
                qmdr_results = self.qmdr_client.search(query, limit)
                for r in qmdr_results:
                    # 获取完整文档内容
                    filename = r['uri'].split('/')[-1].split(':')[0]
                    content = self.qmdr_client.get_document(filename)
                    if content:
                        results['qmdr'].append({
                            'content': content[:500] + '...' if len(content) > 500 else content,
                            'source': 'qmdr',
                            'score': r.get('score', 0),
                            'file': filename
                        })
            except Exception as e:
                print(f"QMDR retrieve error: {e}")
        
        return results
    
    async def retrieve_merged(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        合并检索结果（自动去重和排序）
        
        策略：
        1. 优先使用 QMDR 本地搜索结果（最快）
        2. 合并 memU 云端结果（语义理解最好）
        3. 补充 Hippocampus 重要记忆
        4. 最后加 MemOS 快速结果
        """
        all_results = await self.retrieve_memories(query, limit=limit)
        
        merged = []
        seen_contents = set()
        
        # 按优先级合并
        priority_order = ['qmdr', 'memu', 'hippo', 'memos']
        
        for source in priority_order:
            for item in all_results.get(source, []):
                content = item.get('content', '')
                # 简单去重：检查前50个字符
                content_hash = hashlib.md5(content[:50].encode()).hexdigest()
                
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    merged.append(item)
                    
                    if len(merged) >= limit:
                        break
            
            if len(merged) >= limit:
                break
        
        return merged
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计"""
        return {
            'enabled': self.enabled,
            'systems': {
                'memu': '✅' if self.enabled['memu'] else '❌',
                'hippo': '✅' if self.enabled['hippo'] else '❌',
                'memos': '✅' if self.enabled['memos'] else '❌',
                'qmdr': '✅' if self.enabled['qmdr'] else '❌'
            }
        }
    
    async def reindex_qmdr(self) -> Dict[str, Any]:
        """重新索引 QMDR"""
        if self.enabled['qmdr'] and self.qmdr_client:
            return self.qmdr_client.reindex_all()
        return {'success': False, 'error': 'QMDR not enabled'}


# 便捷函数
async def store_to_all_systems(
    user_msg: str,
    assistant_msg: str,
    importance: float = 0.5,
    **kwargs
) -> Dict[str, bool]:
    """便捷函数：存储到所有系统"""
    async with UnifiedMemoryManagerV3(**kwargs) as mm:
        return await mm.store_memory(user_msg, assistant_msg, importance)


async def retrieve_from_all_systems(
    query: str,
    limit: int = 5,
    **kwargs
) -> Dict[str, List[Dict[str, Any]]]:
    """便捷函数：从所有系统检索"""
    async with UnifiedMemoryManagerV3(**kwargs) as mm:
        return await mm.retrieve_memories(query, limit)


async def retrieve_merged(
    query: str,
    limit: int = 10,
    **kwargs
) -> List[Dict[str, Any]]:
    """便捷函数：合并检索"""
    async with UnifiedMemoryManagerV3(**kwargs) as mm:
        return await mm.retrieve_merged(query, limit)


# 测试代码
if __name__ == '__main__':
    async def test():
        print("🧠 四记忆系统测试\n")
        
        async with UnifiedMemoryManagerV3() as mm:
            stats = mm.get_memory_stats()
            print("系统状态:")
            for system, status in stats['systems'].items():
                print(f"  {system}: {status}")
            
            print("\n" + "="*50)
            
            # 测试搜索
            query = "定时任务"
            print(f"\n🔍 搜索: '{query}'\n")
            
            results = await mm.retrieve_memories(query, limit=3)
            
            for source, items in results.items():
                if items:
                    print(f"\n📦 {source.upper()} ({len(items)} 条):")
                    for i, item in enumerate(items[:2], 1):
                        content = item.get('content', '')[:100]
                        print(f"  {i}. {content}...")
            
            # 合并检索
            print("\n" + "="*50)
            print(f"\n🔄 合并检索 (去重后):\n")
            
            merged = await mm.retrieve_merged(query, limit=5)
            for i, item in enumerate(merged, 1):
                source = item.get('source', 'unknown')
                content = item.get('content', '')[:80]
                print(f"  {i}. [{source}] {content}...")
    
    asyncio.run(test())
