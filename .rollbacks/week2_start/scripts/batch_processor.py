#!/usr/bin/env python3
"""
BowlWanpi 批量处理器
实际应用的批量处理工具
"""

import asyncio
import time
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class BatchItem:
    """批次中的单个项目"""
    data: Any
    timestamp: float
    future: asyncio.Future = field(default_factory=lambda: asyncio.get_event_loop().create_future())


class MessageBatcher:
    """
    消息批量发送器
    
    将多条消息合并发送，减少 API 调用
    """
    
    def __init__(
        self,
        window_size: float = 2.0,  # 2秒窗口
        max_batch_size: int = 10
    ):
        self.window_size = window_size
        self.max_batch_size = max_batch_size
        self.buffer: List[BatchItem] = []
        self.lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self.stats = {
            "total_sent": 0,
            "batches_sent": 0,
            "avg_batch_size": 0
        }
    
    async def send(self, content: str, **kwargs) -> bool:
        """
        发送消息（自动批量）
        
        Args:
            content: 消息内容
            **kwargs: 其他参数（channel, target等）
        
        Returns:
            bool: 是否发送成功
        """
        item = BatchItem(
            data={"content": content, **kwargs},
            timestamp=time.time()
        )
        
        async with self.lock:
            self.buffer.append(item)
            
            # 达到最大批次，立即发送
            if len(self.buffer) >= self.max_batch_size:
                if self._flush_task:
                    self._flush_task.cancel()
                await self._flush()
            elif self._flush_task is None or self._flush_task.done():
                # 启动定时发送
                self._flush_task = asyncio.create_task(self._delayed_flush())
        
        # 等待发送结果
        try:
            return await item.future
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False
    
    async def _delayed_flush(self):
        """延迟发送"""
        try:
            await asyncio.sleep(self.window_size)
            async with self.lock:
                await self._flush()
        except asyncio.CancelledError:
            pass
    
    async def _flush(self):
        """发送当前批次"""
        if not self.buffer:
            return
        
        batch = self.buffer[:]
        self.buffer = []
        
        try:
            # 实际发送（这里调用 message 工具）
            results = await self._send_batch(batch)
            
            # 分发结果
            for item, result in zip(batch, results):
                if not item.future.done():
                    item.future.set_result(result)
            
            # 更新统计
            self.stats["total_sent"] += len(batch)
            self.stats["batches_sent"] += 1
            self.stats["avg_batch_size"] = self.stats["total_sent"] / self.stats["batches_sent"]
            
            print(f"📦 批量发送 {len(batch)} 条消息完成")
            
        except Exception as e:
            print(f"❌ 批量发送失败: {e}")
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(e)
    
    async def _send_batch(self, batch: List[BatchItem]) -> List[bool]:
        """实际批量发送逻辑"""
        # 按 channel 分组
        by_channel = defaultdict(list)
        for item in batch:
            channel = item.data.get("channel", "feishu")
            by_channel[channel].append(item)
        
        results = []
        
        for channel, items in by_channel.items():
            # 合并内容
            if len(items) == 1:
                # 单条直接发送
                content = items[0].data["content"]
            else:
                # 多条合并
                contents = [f"{i+1}. {item.data['content'][:100]}" 
                           for i, item in enumerate(items)]
                content = "📦 批量消息:\n" + "\n".join(contents)
            
            # 实际发送（模拟）
            print(f"📤 发送到 {channel}: {content[:50]}...")
            
            # 这里调用实际的 message 工具
            # from message import message
            # await message(action="send", message=content, ...)
            
            results.extend([True] * len(items))
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    async def flush_all(self):
        """立即发送所有缓冲的消息"""
        async with self.lock:
            if self._flush_task:
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass
            await self._flush()


class MemoryBatcher:
    """
    记忆批量存储器
    
    将多条记忆合并存储到四系统
    """
    
    def __init__(
        self,
        window_size: float = 3.0,
        max_batch_size: int = 5
    ):
        self.window_size = window_size
        self.max_batch_size = max_batch_size
        self.buffer: List[BatchItem] = []
        self.lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
    
    async def store(
        self,
        user_msg: str,
        assistant_msg: str,
        importance: float = 0.5
    ) -> Dict[str, bool]:
        """
        存储记忆（自动批量）
        
        Returns:
            Dict[str, bool]: 各系统存储结果
        """
        item = BatchItem(
            data={
                "user": user_msg,
                "assistant": assistant_msg,
                "importance": importance
            },
            timestamp=time.time()
        )
        
        async with self.lock:
            self.buffer.append(item)
            
            if len(self.buffer) >= self.max_batch_size:
                if self._flush_task:
                    self._flush_task.cancel()
                await self._flush()
            elif self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._delayed_flush())
        
        return await item.future
    
    async def _delayed_flush(self):
        """延迟刷新"""
        try:
            await asyncio.sleep(self.window_size)
            async with self.lock:
                await self._flush()
        except asyncio.CancelledError:
            pass
    
    async def _flush(self):
        """批量存储"""
        if not self.buffer:
            return
        
        batch = self.buffer[:]
        self.buffer = []
        
        try:
            results = await self._store_batch(batch)
            
            for item, result in zip(batch, results):
                if not item.future.done():
                    item.future.set_result(result)
            
            print(f"🧠 批量存储 {len(batch)} 条记忆完成")
            
        except Exception as e:
            print(f"❌ 批量存储失败: {e}")
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(e)
    
    async def _store_batch(self, batch: List[BatchItem]) -> List[Dict[str, bool]]:
        """实际批量存储"""
        results = []
        
        # 批量导入四记忆系统
        try:
            import sys
            sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')
            from unified_memory_manager_v3 import UnifiedMemoryManagerV3
            
            async with UnifiedMemoryManagerV3() as mm:
                # 逐个存储（但批量提交可以减少连接开销）
                for item in batch:
                    result = await mm.store_memory(
                        item.data["user"],
                        item.data["assistant"],
                        item.data["importance"]
                    )
                    results.append(result)
                    
        except Exception as e:
            print(f"⚠️ 四系统存储失败，回退到本地: {e}")
            # 回退：只存本地文件
            for item in batch:
                # 保存到本地
                from datetime import datetime
                daily_file = f"/root/.openclaw/workspace/memory/{datetime.now().strftime('%Y-%m-%d')}.md"
                with open(daily_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n## {datetime.now().strftime('%H:%M')}\n")
                    f.write(f"**User:** {item.data['user']}\n\n")
                    f.write(f"**Assistant:** {item.data['assistant']}\n")
                
                results.append({"local": True, "cloud": False})
        
        return results
    
    async def flush_all(self):
        """立即存储所有缓冲的记忆"""
        async with self.lock:
            if self._flush_task:
                self._flush_task.cancel()
            await self._flush()


class APICacheBatcher:
    """
    API 调用缓存 + 批量
    
    缓存 API 结果 + 批量请求相同接口
    """
    
    def __init__(
        self,
        cache_ttl: float = 300,  # 5分钟缓存
        batch_window: float = 1.0
    ):
        self.cache: Dict[str, Dict] = {}  # key: {data, timestamp}
        self.cache_ttl = cache_ttl
        self.pending: Dict[str, List[BatchItem]] = defaultdict(list)
        self.lock = asyncio.Lock()
        self.batch_window = batch_window
        self._batch_tasks: Dict[str, asyncio.Task] = {}
    
    async def call(
        self,
        api_name: str,
        params: Dict,
        fetch_func: Callable
    ) -> Any:
        """
        调用 API（带缓存和批量）
        
        Args:
            api_name: API 名称
            params: 请求参数
            fetch_func: 实际获取函数
        """
        cache_key = f"{api_name}:{json.dumps(params, sort_keys=True)}"
        
        # 检查缓存
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["timestamp"] < self.cache_ttl:
                print(f"💾 缓存命中: {api_name}")
                return cached["data"]
        
        # 创建批次项
        item = BatchItem(data={"params": params, "fetch_func": fetch_func}, timestamp=time.time())
        
        async with self.lock:
            self.pending[api_name].append(item)
            
            # 启动批量任务
            if api_name not in self._batch_tasks or self._batch_tasks[api_name].done():
                self._batch_tasks[api_name] = asyncio.create_task(
                    self._batch_fetch(api_name)
                )
        
        # 等待结果
        return await item.future
    
    async def _batch_fetch(self, api_name: str):
        """批量获取"""
        await asyncio.sleep(self.batch_window)
        
        async with self.lock:
            batch = self.pending[api_name][:]
            self.pending[api_name] = []
        
        if not batch:
            return
        
        print(f"📦 批量获取 {api_name}: {len(batch)} 个请求")
        
        try:
            # 合并相同参数的请求
            unique_params = {}
            for item in batch:
                param_key = json.dumps(item.data["params"], sort_keys=True)
                if param_key not in unique_params:
                    unique_params[param_key] = {
                        "params": item.data["params"],
                        "fetch_func": item.data["fetch_func"],
                        "items": []
                    }
                unique_params[param_key]["items"].append(item)
            
            # 批量获取
            for param_key, group in unique_params.items():
                # 实际获取
                result = await group["fetch_func"](group["params"])
                
                # 缓存结果
                cache_key = f"{api_name}:{param_key}"
                self.cache[cache_key] = {
                    "data": result,
                    "timestamp": time.time()
                }
                
                # 分发给所有等待者
                for item in group["items"]:
                    if not item.future.done():
                        item.future.set_result(result)
                        
        except Exception as e:
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(e)


# 全局实例（供整个系统使用）
message_batcher = MessageBatcher()
memory_batcher = MemoryBatcher()
api_batcher = APICacheBatcher()


# 便捷函数
async def send_message(content: str, **kwargs) -> bool:
    """批量发送消息"""
    return await message_batcher.send(content, **kwargs)


async def store_memory(user_msg: str, assistant_msg: str, importance: float = 0.5) -> Dict[str, bool]:
    """批量存储记忆"""
    return await memory_batcher.store(user_msg, assistant_msg, importance)


async def cached_api_call(api_name: str, params: Dict, fetch_func: Callable) -> Any:
    """带缓存和批量的 API 调用"""
    return await api_batcher.call(api_name, params, fetch_func)


# 测试代码
if __name__ == "__main__":
    async def test():
        print("🧪 测试批量处理器\n")
        
        # 测试消息批量
        print("📨 测试消息批量发送...")
        results = await asyncio.gather(*[
            send_message(f"测试消息 {i}")
            for i in range(5)
        ])
        print(f"发送结果: {results}\n")
        
        # 等待批次完成
        await asyncio.sleep(3)
        
        # 查看统计
        stats = message_batcher.get_stats()
        print(f"📊 消息统计: {stats}\n")
        
        # 刷新所有
        await message_batcher.flush_all()
        await memory_batcher.flush_all()
        
        print("✅ 测试完成！")
    
    asyncio.run(test())
