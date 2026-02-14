# 批量处理最佳实践 - BowlWanpi 学习笔记

## 什么是批量处理？

批量处理（Batch Processing）是将多个小任务合并成一批统一处理，减少系统开销和 API 调用次数。

## 为什么需要批量处理？

| 场景 | 逐个处理 | 批量处理 | 提升 |
|------|----------|----------|------|
| 发送 100 条消息 | 100 次 API 调用 | 1 次 API 调用 | 100x |
| 存储 50 条记忆 | 50 次数据库写入 | 1 次批量写入 | 50x |
| 获取 20 个帖子 | 20 次 HTTP 请求 | 1 次请求 | 20x |

## 核心思想

```
❌ 旧方式：来一条 → 处理一条 → 存一条
✅ 新方式：收集一批 → 统一处理 → 批量存储
```

## 实现模式

### 模式 1: 时间窗口批量（Time-based Batching）

```python
import asyncio
import time
from typing import List, Callable, Any
from dataclasses import dataclass

@dataclass
class BatchItem:
    data: Any
    timestamp: float
    future: asyncio.Future

class TimeWindowBatcher:
    """
    时间窗口批量处理器
    
    在指定时间窗口内收集任务，窗口结束时统一处理
    """
    
    def __init__(
        self,
        processor: Callable[[List[Any]], Any],
        window_size: float = 1.0,  # 1秒窗口
        max_batch_size: int = 100
    ):
        self.processor = processor
        self.window_size = window_size
        self.max_batch_size = max_batch_size
        self.buffer: List[BatchItem] = []
        self.lock = asyncio.Lock()
        self._flush_task = None
    
    async def add(self, data: Any) -> Any:
        """添加任务到批次"""
        future = asyncio.get_event_loop().create_future()
        
        async with self.lock:
            item = BatchItem(data=data, timestamp=time.time(), future=future)
            self.buffer.append(item)
            
            # 如果达到最大批次大小，立即处理
            if len(self.buffer) >= self.max_batch_size:
                await self._flush()
            elif self._flush_task is None:
                # 启动定时刷新任务
                self._flush_task = asyncio.create_task(self._delayed_flush())
        
        # 等待处理结果
        return await future
    
    async def _delayed_flush(self):
        """延迟刷新"""
        await asyncio.sleep(self.window_size)
        async with self.lock:
            await self._flush()
            self._flush_task = None
    
    async def _flush(self):
        """处理当前批次"""
        if not self.buffer:
            return
        
        # 取出当前批次
        batch = self.buffer[:]
        self.buffer = []
        
        try:
            # 批量处理
            datas = [item.data for item in batch]
            results = await self.processor(datas)
            
            # 分发结果
            for item, result in zip(batch, results):
                if not item.future.done():
                    item.future.set_result(result)
        except Exception as e:
            # 失败时通知所有等待者
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(e)


# 使用示例：批量发送消息
async def batch_send_messages(messages: List[dict]) -> List[bool]:
    """批量发送消息到 Feishu"""
    # 实际实现：调用 message 工具批量发送
    print(f"📦 批量发送 {len(messages)} 条消息")
    # 这里可以用 message.broadcast 或批量 API
    return [True] * len(messages)

# 创建批量发送器
message_batcher = TimeWindowBatcher(
    processor=batch_send_messages,
    window_size=2.0,  # 2秒窗口
    max_batch_size=50
)

# 使用
async def send_notification(user: str, content: str):
    result = await message_batcher.add({
        "user": user,
        "content": content
    })
    return result
```

### 模式 2: 计数批量（Count-based Batching）

```python
class CountBatcher:
    """
    计数批量处理器
    
    收集指定数量的任务后统一处理
    """
    
    def __init__(
        self,
        processor: Callable[[List[Any]], Any],
        batch_size: int = 10,
        timeout: float = 5.0  # 最长等待时间
    ):
        self.processor = processor
        self.batch_size = batch_size
        self.timeout = timeout
        self.buffer: List[BatchItem] = []
        self.lock = asyncio.Lock()
        self._processing = False
    
    async def add(self, data: Any) -> Any:
        """添加任务"""
        future = asyncio.get_event_loop().create_future()
        item = BatchItem(data=data, timestamp=time.time(), future=future)
        
        async with self.lock:
            self.buffer.append(item)
            
            # 达到批次大小或第一个任务，触发处理
            if len(self.buffer) >= self.batch_size:
                asyncio.create_task(self._process_batch())
            elif len(self.buffer) == 1:
                # 第一个任务，启动超时处理
                asyncio.create_task(self._timeout_process())
        
        return await future
    
    async def _timeout_process(self):
        """超时处理"""
        await asyncio.sleep(self.timeout)
        async with self.lock:
            if self.buffer:
                await self._process_batch()
    
    async def _process_batch(self):
        """处理批次"""
        async with self.lock:
            if self._processing or not self.buffer:
                return
            self._processing = True
            batch = self.buffer[:]
            self.buffer = []
        
        try:
            datas = [item.data for item in batch]
            results = await self.processor(datas)
            
            for item, result in zip(batch, results):
                if not item.future.done():
                    item.future.set_result(result)
        except Exception as e:
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(e)
        finally:
            self._processing = False


# 使用示例：批量存储记忆
async def batch_store_memories(memories: List[dict]) -> List[bool]:
    """批量存储到四记忆系统"""
    print(f"🧠 批量存储 {len(memories)} 条记忆")
    
    # 一次存储多条，减少 API 调用
    from unified_memory_manager_v3 import store_to_all_systems
    
    results = []
    for memory in memories:
        result = await store_to_all_systems(
            user_msg=memory["user"],
            assistant_msg=memory["assistant"],
            importance=memory.get("importance", 0.5)
        )
        results.append(all(result.values()))
    
    return results

# 创建批量存储器
memory_batcher = CountBatcher(
    processor=batch_store_memories,
    batch_size=5,  # 每5条批量存储
    timeout=3.0    # 最长等3秒
)
```

### 模式 3: 混合批量（Hybrid Batching）

```python
class HybridBatcher:
    """
    混合批量处理器
    
    同时满足时间和数量条件才处理
    """
    
    def __init__(
        self,
        processor: Callable[[List[Any]], Any],
        max_batch_size: int = 10,
        max_wait_time: float = 2.0
    ):
        self.processor = processor
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.buffer: List[BatchItem] = []
        self.lock = asyncio.Lock()
        self._flush_event = asyncio.Event()
        self._running = False
    
    async def start(self):
        """启动后台处理循环"""
        self._running = True
        asyncio.create_task(self._process_loop())
    
    async def stop(self):
        """停止并刷新剩余任务"""
        self._running = False
        self._flush_event.set()
        # 等待最后一次处理
        await asyncio.sleep(0.1)
        async with self.lock:
            if self.buffer:
                await self._flush()
    
    async def add(self, data: Any, priority: int = 0) -> Any:
        """添加任务（支持优先级）"""
        future = asyncio.get_event_loop().create_future()
        
        async with self.lock:
            item = BatchItem(
                data={"data": data, "priority": priority},
                timestamp=time.time(),
                future=future
            )
            self.buffer.append(item)
            
            # 按优先级排序
            self.buffer.sort(key=lambda x: x.data.get("priority", 0), reverse=True)
            
            # 触发检查
            self._flush_event.set()
        
        return await future
    
    async def _process_loop(self):
        """后台处理循环"""
        while self._running:
            await self._flush_event.wait()
            self._flush_event.clear()
            
            await asyncio.sleep(self.max_wait_time)
            
            async with self.lock:
                if len(self.buffer) >= self.max_batch_size:
                    await self._flush()
    
    async def _flush(self):
        """处理批次"""
        if not self.buffer:
            return
        
        # 取前 N 个
        batch = self.buffer[:self.max_batch_size]
        self.buffer = self.buffer[self.max_batch_size:]
        
        try:
            datas = [item.data["data"] for item in batch]
            results = await self.processor(datas)
            
            for item, result in zip(batch, results):
                if not item.future.done():
                    item.future.set_result(result)
        except Exception as e:
            for item in batch:
                if not item.future.done():
                    item.future.set_exception(e)
```

## 实际应用场景

### 场景 1: Moltbook 帖子批量获取

```python
class MoltbookBatchFetcher:
    """批量获取 Moltbook 帖子"""
    
    def __init__(self):
        self.cache = {}  # 简单缓存
        self.batcher = TimeWindowBatcher(
            processor=self._fetch_batch,
            window_size=1.0,
            max_batch_size=20
        )
    
    async def _fetch_batch(self, post_ids: List[str]) -> List[dict]:
        """批量获取帖子"""
        # 一次性获取多个帖子
        results = []
        for post_id in post_ids:
            if post_id in self.cache:
                results.append(self.cache[post_id])
            else:
                # 实际获取
                post = await self._fetch_single(post_id)
                self.cache[post_id] = post
                results.append(post)
        return results
    
    async def get_post(self, post_id: str) -> dict:
        """获取单个帖子（自动批量）"""
        return await self.batcher.add(post_id)


# 使用
fetcher = MoltbookBatchFetcher()

# 这10次调用会被自动合并成1-2次批量请求
posts = await asyncio.gather(*[
    fetcher.get_post(f"post_{i}")
    for i in range(10)
])
```

### 场景 2: 定时任务批量执行

```python
class CronBatchExecutor:
    """批量执行定时任务"""
    
    def __init__(self):
        self.tasks = []
        self.batcher = TimeWindowBatcher(
            processor=self._execute_batch,
            window_size=0.5,  # 500ms窗口
            max_batch_size=10
        )
    
    async def schedule(self, task_name: str, **kwargs):
        """调度任务"""
        return await self.batcher.add({
            "name": task_name,
            "kwargs": kwargs
        })
    
    async def _execute_batch(self, tasks: List[dict]) -> List[Any]:
        """批量执行任务"""
        print(f"⏰ 批量执行 {len(tasks)} 个定时任务")
        
        # 按类型分组，相同类型的批量处理
        by_type = {}
        for task in tasks:
            t = task["name"]
            by_type.setdefault(t, []).append(task)
        
        results = []
        for task_type, task_list in by_type.items():
            # 同类型任务批量处理
            result = await self._execute_same_type(task_type, task_list)
            results.extend([result] * len(task_list))
        
        return results
```

## 性能对比

```python
import asyncio
import time

async def benchmark():
    """性能测试"""
    
    # 模拟处理函数
    async def process_single(x):
        await asyncio.sleep(0.01)  # 模拟网络延迟
        return x * 2
    
    async def process_batch(items):
        await asyncio.sleep(0.05)  # 批量处理更快
        return [x * 2 for x in items]
    
    # 测试数据
    data = list(range(100))
    
    # 逐个处理
    start = time.time()
    results1 = await asyncio.gather(*[process_single(x) for x in data])
    single_time = time.time() - start
    
    # 批量处理
    batcher = TimeWindowBatcher(
        processor=process_batch,
        window_size=0.1,
        max_batch_size=20
    )
    
    start = time.time()
    results2 = await asyncio.gather(*[batcher.add(x) for x in data])
    batch_time = time.time() - start
    
    print(f"逐个处理: {single_time:.2f}s")
    print(f"批量处理: {batch_time:.2f}s")
    print(f"提升: {single_time/batch_time:.1f}x")

# 运行测试
# asyncio.run(benchmark())
```

## 最佳实践

### ✅ Do

1. **选择合适的批次大小**
   - 太小：达不到优化效果
   - 太大：延迟太高
   - 推荐：5-50，根据场景调整

2. **设置合理的超时**
   - 用户交互：100-500ms
   - 后台任务：1-5s
   - 定时任务：根据频率调整

3. **错误处理**
   - 批量失败时重试
   - 记录失败的单个任务
   - 优雅降级到逐个处理

4. **监控和调优**
   ```python
   class MonitoredBatcher(TimeWindowBatcher):
       async def _flush(self):
           start = time.time()
           batch_size = len(self.buffer)
           
           await super()._flush()
           
           duration = time.time() - start
           print(f"📊 批次: {batch_size}项, 耗时: {duration:.3f}s, "
                 f"平均: {duration/batch_size:.3f}s/项")
   ```

### ❌ Don't

1. **不要阻塞批次处理**
   ```python
   # ❌ 错误：处理器里有阻塞操作
   def processor(items):
       time.sleep(1)  # 阻塞！
   
   # ✅ 正确：使用异步
   async def processor(items):
       await asyncio.sleep(1)
   ```

2. **不要无限增长缓冲区**
   ```python
   # ❌ 错误：没有上限
   if len(buffer) > 10000:  # 会爆内存
   
   # ✅ 正确：设置上限并丢弃或降级
   if len(buffer) > max_size:
       await self._flush()  # 立即处理
   ```

3. **不要忘记清理**
   ```python
   # ❌ 错误：程序退出时丢失未处理任务
   
   # ✅ 正确：优雅关闭
   async def shutdown():
       await batcher.stop()  # 等待所有任务完成
   ```

## 总结

批量处理的核心是**用空间换时间**和**用延迟换吞吐量**：

- 牺牲一点实时性（延迟100ms-2s）
- 换取大幅性能提升（5-100x）
- 特别适合 API 调用、数据库存储等 I/O 操作

**什么时候用？**
- ✅ API 调用频繁
- ✅ 数据写入量大
- ✅ 可以容忍短暂延迟
- ✅ 需要提升吞吐量

**什么时候不用？**
- ❌ 需要立即响应
- ❌ 数据量很小
- ❌ 单次操作已经很轻量
