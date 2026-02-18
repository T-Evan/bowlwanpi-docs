#!/usr/bin/env python3
"""
并行信息收集器 - Parallel Info Collector
使用 OpenClaw subagents 同时收集多个数据源
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace')

# 数据源配置
DATA_SOURCES = {
    'moltbook': {
        'name': 'Moltbook 热门',
        'command': 'python3 skills/Hacker\ News/scripts/moltbook_client.py trending',
        'priority': 1,
        'timeout': 30
    },
    'github_trending': {
        'name': 'GitHub Trending',
        'command': 'python3 scripts/github_trending.py --lang=python,javascript,typescript,go,rust',
        'priority': 1,
        'timeout': 30
    },
    'ai_papers': {
        'name': 'AI 论文更新',
        'command': 'python3 scripts/ai_papers_check.py',
        'priority': 2,
        'timeout': 45
    },
    'product_hunt': {
        'name': 'Product Hunt',
        'command': 'python3 scripts/product_hunt_check.py',
        'priority': 2,
        'timeout': 30
    }
}

WORKSPACE = Path('/root/.openclaw/workspace')
RESULTS_FILE = WORKSPACE / 'memory' / 'parallel-collector-results.json'
LOCK_FILE = Path('/tmp/parallel-collector.lock')


class ParallelCollector:
    """并行信息收集器"""
    
    def __init__(self):
        self.results = {}
        self.errors = {}
        
    async def run_subagent(self, source_id: str, config: dict) -> dict:
        """运行单个子代理收集任务"""
        import subprocess
        
        source_name = config['name']
        command = config['command']
        timeout = config['timeout']
        
        print(f"🚀 启动 [{source_name}] 收集...")
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 使用 asyncio.create_subprocess_exec 并行执行
            proc = await asyncio.create_subprocess_shell(
                f"cd {WORKSPACE} && {command}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            elapsed = asyncio.get_event_loop().time() - start_time
            output = stdout.decode('utf-8', errors='ignore')
            
            if proc.returncode == 0:
                print(f"✅ [{source_name}] 完成 ({elapsed:.1f}s)")
                return {
                    'success': True,
                    'source': source_id,
                    'name': source_name,
                    'output': output,
                    'elapsed': elapsed,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                error = stderr.decode('utf-8', errors='ignore')[:200]
                print(f"⚠️ [{source_name}] 失败: {error}")
                return {
                    'success': False,
                    'source': source_id,
                    'name': source_name,
                    'error': error,
                    'elapsed': elapsed
                }
                
        except asyncio.TimeoutError:
            print(f"⏱️ [{source_name}] 超时 ({timeout}s)")
            return {
                'success': False,
                'source': source_id,
                'name': source_name,
                'error': 'timeout',
                'elapsed': timeout
            }
        except Exception as e:
            print(f"❌ [{source_name}] 异常: {e}")
            return {
                'success': False,
                'source': source_id,
                'name': source_name,
                'error': str(e),
                'elapsed': 0
            }
    
    async def collect_all(self, sources: dict = None) -> dict:
        """并行收集所有数据源"""
        sources = sources or DATA_SOURCES
        
        print(f"\n{'='*50}")
        print(f"🔄 并行信息收集器启动")
        print(f"📊 数据源数量: {len(sources)}")
        print(f"⏰ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}\n")
        
        start_time = asyncio.get_event_loop().time()
        
        # 创建所有任务的并发执行
        tasks = [
            self.run_subagent(source_id, config)
            for source_id, config in sources.items()
        ]
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_elapsed = asyncio.get_event_loop().time() - start_time
        
        # 整理结果
        for result in results:
            if isinstance(result, dict):
                source_id = result['source']
                self.results[source_id] = result
            elif isinstance(result, Exception):
                print(f"❌ 任务异常: {result}")
        
        # 统计
        success_count = sum(1 for r in self.results.values() if r.get('success'))
        
        print(f"\n{'='*50}")
        print(f"✅ 收集完成!")
        print(f"⏱️ 总耗时: {total_elapsed:.1f}秒")
        print(f"📈 成功: {success_count}/{len(sources)}")
        print(f"{'='*50}\n")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_elapsed': total_elapsed,
            'success_count': success_count,
            'total_count': len(sources),
            'results': self.results
        }
    
    def save_results(self, output_file: Path = None):
        """保存结果到文件"""
        output_file = output_file or RESULTS_FILE
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 结果已保存: {output_file}")
    
    def generate_summary(self) -> str:
        """生成汇总报告"""
        lines = ["📊 并行收集结果汇总\n"]
        
        # 按优先级排序
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: DATA_SOURCES.get(x[0], {}).get('priority', 99)
        )
        
        for source_id, result in sorted_results:
            name = result.get('name', source_id)
            success = result.get('success', False)
            elapsed = result.get('elapsed', 0)
            
            if success:
                lines.append(f"✅ {name} ({elapsed:.1f}s)")
                # 显示输出摘要（前100字符）
                output = result.get('output', '')
                if output:
                    preview = output.strip()[:100].replace('\n', ' ')
                    lines.append(f"   └─ {preview}...")
            else:
                lines.append(f"❌ {name} ({elapsed:.1f}s)")
                error = result.get('error', 'Unknown error')
                lines.append(f"   └─ ⚠️ {error[:80]}")
        
        return '\n'.join(lines)


def check_lock() -> bool:
    """检查是否已有实例在运行"""
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            # 检查进程是否还存在
            os.kill(pid, 0)
            print(f"⚠️ 另一个收集器正在运行 (PID: {pid})")
            return False
        except (ProcessLookupError, ValueError):
            # 进程已不存在，删除锁文件
            LOCK_FILE.unlink()
    
    # 创建锁文件
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    return True


def release_lock():
    """释放锁"""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='并行信息收集器')
    parser.add_argument('--sources', '-s', nargs='+', help='指定数据源')
    parser.add_argument('--summary', action='store_true', help='生成汇总报告')
    parser.add_argument('--no-lock', action='store_true', help='跳过锁检查')
    args = parser.parse_args()
    
    # 锁检查
    if not args.no_lock and not check_lock():
        return 1
    
    try:
        # 选择数据源
        sources = DATA_SOURCES
        if args.sources:
            sources = {k: v for k, v in DATA_SOURCES.items() if k in args.sources}
            if not sources:
                print(f"❌ 无效的数据源: {args.sources}")
                print(f"可用: {list(DATA_SOURCES.keys())}")
                return 1
        
        # 运行收集
        collector = ParallelCollector()
        results = asyncio.run(collector.collect_all(sources))
        
        # 保存结果
        collector.save_results()
        
        # 输出汇总
        if args.summary or True:  # 默认输出汇总
            print(collector.generate_summary())
        
        return 0 if results['success_count'] > 0 else 1
        
    finally:
        release_lock()


if __name__ == '__main__':
    exit(main())
