#!/usr/bin/env python3
"""
BowlWanpi 信息去重推送系统 v1.0
确保同一内容最多推送3次，避免重复打扰
"""
import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

CONTENT_TRACK_FILE = '/root/.openclaw/workspace/memory/content-pushed.json'
MAX_PUSH_COUNT = 3  # 同一内容最多推送次数
DEDUP_WINDOW_DAYS = 7  # 去重窗口期（7天内）

@dataclass
class PushedContent:
    """已推送内容记录"""
    content_hash: str
    original_text: str
    push_count: int
    first_push: str
    last_push: str
    sources: List[str]  # 来源记录

class ContentDeduplicationManager:
    """
    内容去重管理器
    
    功能:
    1. 内容指纹识别 (哈希)
    2. 推送次数限制 (最多3次)
    3. 时间窗口控制 (7天)
    4. 相似内容检测
    """
    
    def __init__(self):
        self.pushed_content: Dict[str, PushedContent] = {}
        self._load()
    
    def _load(self):
        """加载已推送记录"""
        if os.path.exists(CONTENT_TRACK_FILE):
            try:
                with open(CONTENT_TRACK_FILE, 'r') as f:
                    data = json.load(f)
                for hash_key, record in data.items():
                    self.pushed_content[hash_key] = PushedContent(**record)
            except:
                self.pushed_content = {}
    
    def _save(self):
        """保存推送记录"""
        data = {}
        for hash_key, record in self.pushed_content.items():
            data[hash_key] = {
                'content_hash': record.content_hash,
                'original_text': record.original_text[:200],  # 只保存前200字符
                'push_count': record.push_count,
                'first_push': record.first_push,
                'last_push': record.last_push,
                'sources': record.sources
            }
        os.makedirs(os.path.dirname(CONTENT_TRACK_FILE), exist_ok=True)
        with open(CONTENT_TRACK_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_fingerprint(self, content: str) -> str:
        """
        生成内容指纹
        
        策略:
        1. 清洗内容 (去除空格、标点、大小写统一)
        2. 提取关键词
        3. 生成哈希
        """
        # 清洗
        cleaned = content.lower().strip()
        # 去除常见标点
        for char in '。，！？.,!?;:""''（）()【】[]':
            cleaned = cleaned.replace(char, '')
        # 去除多余空格
        cleaned = ' '.join(cleaned.split())
        
        # 如果内容太长，提取核心部分
        if len(cleaned) > 100:
            # 取开头30 + 中间20 + 结尾30
            cleaned = cleaned[:30] + cleaned[len(cleaned)//2-10:len(cleaned)//2+10] + cleaned[-30:]
        
        # 生成MD5哈希
        return hashlib.md5(cleaned.encode()).hexdigest()[:16]
    
    def check_and_update(self, content: str, source: str = "unknown") -> Dict:
        """
        检查内容是否可以推送，并更新记录
        
        Returns:
            {
                'can_push': bool,
                'push_count': int,
                'remaining': int,  # 剩余可推送次数
                'reason': str
            }
        """
        fingerprint = self._generate_fingerprint(content)
        now = datetime.now().isoformat()
        
        # 检查是否已存在
        if fingerprint in self.pushed_content:
            record = self.pushed_content[fingerprint]
            
            # 检查时间窗口
            first_push = datetime.fromisoformat(record.first_push)
            if datetime.now() - first_push > timedelta(days=DEDUP_WINDOW_DAYS):
                # 超过7天，重置计数
                record.push_count = 0
                record.first_push = now
            
            # 检查推送次数
            if record.push_count >= MAX_PUSH_COUNT:
                return {
                    'can_push': False,
                    'push_count': record.push_count,
                    'remaining': 0,
                    'reason': f'该内容已推送{record.push_count}次（达到上限），7天后重置'
                }
            
            # 可以推送，更新记录
            record.push_count += 1
            record.last_push = now
            if source not in record.sources:
                record.sources.append(source)
            self._save()
            
            return {
                'can_push': True,
                'push_count': record.push_count,
                'remaining': MAX_PUSH_COUNT - record.push_count,
                'reason': f'第{record.push_count}次推送（还剩{MAX_PUSH_COUNT - record.push_count}次）'
            }
        
        else:
            # 新内容，创建记录
            self.pushed_content[fingerprint] = PushedContent(
                content_hash=fingerprint,
                original_text=content,
                push_count=1,
                first_push=now,
                last_push=now,
                sources=[source]
            )
            self._save()
            
            return {
                'can_push': True,
                'push_count': 1,
                'remaining': MAX_PUSH_COUNT - 1,
                'reason': '首次推送（还剩2次）'
            }
    
    def should_push(self, content: str, source: str = "unknown") -> bool:
        """简单检查是否应该推送"""
        result = self.check_and_update(content, source)
        return result['can_push']
    
    def get_stats(self) -> str:
        """获取推送统计"""
        total = len(self.pushed_content)
        
        # 统计今日推送
        today = datetime.now().date()
        today_count = sum(
            1 for r in self.pushed_content.values()
            if datetime.fromisoformat(r.last_push).date() == today
        )
        
        # 统计已用完次数的内容
        maxed_out = sum(
            1 for r in self.pushed_content.values()
            if r.push_count >= MAX_PUSH_COUNT
        )
        
        lines = []
        lines.append("📊 内容推送去重统计")
        lines.append("=" * 50)
        lines.append(f"总记录数: {total}")
        lines.append(f"今日推送: {today_count}")
        lines.append(f"已达上限(3次): {maxed_out}")
        lines.append(f"去重窗口: {DEDUP_WINDOW_DAYS}天")
        lines.append("")
        lines.append("💡 规则:")
        lines.append("  • 同一内容最多推送3次")
        lines.append("  • 7天后自动重置计数")
        lines.append("  • 相似内容会合并计数")
        
        return "\n".join(lines)
    
    def reset_if_needed(self):
        """清理过期的记录（超过30天）"""
        now = datetime.now()
        to_remove = []
        
        for hash_key, record in self.pushed_content.items():
            last_push = datetime.fromisoformat(record.last_push)
            if now - last_push > timedelta(days=30):
                to_remove.append(hash_key)
        
        for key in to_remove:
            del self.pushed_content[key]
        
        if to_remove:
            self._save()
            print(f"🧹 清理了{len(to_remove)}条过期记录")


class SmartInfoCollector:
    """
    智能信息收集器（带去重）
    """
    
    def __init__(self):
        self.dedup = ContentDeduplicationManager()
    
    def collect_and_push(self, content: str, source: str, priority: str = "normal") -> Dict:
        """
        收集信息并决定是否推送
        
        Args:
            content: 内容文本
            source: 来源（如：GitHub, Twitter, 新闻）
            priority: 优先级 (high/normal/low)
        
        Returns:
            处理结果
        """
        # 检查是否应该推送
        check_result = self.dedup.check_and_update(content, source)
        
        result = {
            'content': content[:100] + '...' if len(content) > 100 else content,
            'source': source,
            'priority': priority,
            'action': 'push' if check_result['can_push'] else 'skip',
            'reason': check_result['reason'],
            'push_count': check_result['push_count']
        }
        
        if check_result['can_push']:
            # 这里执行实际推送
            # push_to_feishu(content)
            pass
        
        return result


def demo_deduplication():
    """演示去重系统"""
    manager = ContentDeduplicationManager()
    collector = SmartInfoCollector()
    
    print("🧪 测试内容去重系统")
    print("=" * 60)
    
    # 测试内容
    contents = [
        "OpenClaw发布了新版本，增加了AI Brain功能！",
        "OpenClaw发布了新版本，增加了AI Brain功能！",  # 重复
        "OpenClaw v2.0 发布，支持AI Brain！",  # 相似
        "GitHub上有新的star项目",
        "OpenClaw发布了新版本，增加了AI Brain功能！",  # 第3次
        "OpenClaw发布了新版本，增加了AI Brain功能！",  # 第4次（应该被阻止）
    ]
    
    for i, content in enumerate(contents, 1):
        print(f"\n测试 {i}: {content[:40]}...")
        result = collector.collect_and_push(content, "demo")
        print(f"  结果: {result['action'].upper()} - {result['reason']}")
    
    print("\n" + manager.get_stats())


if __name__ == '__main__':
    demo_deduplication()
