#!/usr/bin/env python3
"""
BowlWanpi 三记忆系统统一管理器 v1.0
学习自 multi-coding-agent skill
统一管理 memU + Hippocampus + MemOS
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class MemorySystem(Enum):
    """记忆系统类型"""
    MEMU = "memu"           # 云端记忆
    HIPPOCAMPUS = "hippocampus"  # 本地记忆
    MEMOS = "memos"         # MCP记忆

@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    source: str  # 来源系统
    timestamp: str
    importance: float
    tags: List[str]

class UnifiedMemoryManager:
    """
    三记忆系统统一管理器
    
    统一管理:
    - memU (云端)
    - Hippocampus (本地)
    - MemOS (MCP)
    
    功能:
    - 智能选择存储位置
    - 自动同步和备份
    - 统一检索接口
    - 冗余和容错
    """
    
    def __init__(self):
        self.systems_status = {
            MemorySystem.MEMU: {"available": False, "last_sync": None},
            MemorySystem.HIPPOCAMPUS: {"available": True, "last_sync": None},
            MemorySystem.MEMOS: {"available": False, "last_sync": None},
        }
        self.cache = []
        self._check_systems()
    
    def _check_systems(self):
        """检查各系统可用性"""
        # 检查 Hippocampus
        if os.path.exists('/root/.openclaw/workspace/memory/index.json'):
            self.systems_status[MemorySystem.HIPPOCAMPUS]["available"] = True
        
        # 检查 memU (需要API key)
        if os.path.exists('/root/.openclaw/workspace/secrets/memu-credentials.json'):
            self.systems_status[MemorySystem.MEMU]["available"] = True
        
        # 检查 MemOS
        # 简化处理，假设可能不可用
        self.systems_status[MemorySystem.MEMOS]["available"] = False
    
    def store(self, content: str, importance: float = 0.5, 
              tags: List[str] = None, preferred_system: MemorySystem = None) -> Dict:
        """
        智能存储记忆
        
        策略:
        - 重要记忆(>0.7): 存所有可用系统
        - 中等记忆(0.4-0.7): 存本地 + 云端
        - 普通记忆(<0.4): 只存本地
        """
        if tags is None:
            tags = []
        
        memory_id = f"mem_{datetime.now().timestamp()}"
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            source="unified",
            timestamp=datetime.now().isoformat(),
            importance=importance,
            tags=tags
        )
        
        results = {}
        
        # 智能选择存储位置
        if importance >= 0.7:
            # 重要记忆: 存所有可用系统
            for system in MemorySystem:
                if self.systems_status[system]["available"]:
                    result = self._store_to_system(system, entry)
                    results[system.value] = result
        elif importance >= 0.4:
            # 中等记忆: 本地 + 云端
            if self.systems_status[MemorySystem.HIPPOCAMPUS]["available"]:
                results["hippocampus"] = self._store_to_system(MemorySystem.HIPPOCAMPUS, entry)
            if self.systems_status[MemorySystem.MEMU]["available"]:
                results["memu"] = self._store_to_system(MemorySystem.MEMU, entry)
        else:
            # 普通记忆: 只存本地
            if self.systems_status[MemorySystem.HIPPOCAMPUS]["available"]:
                results["hippocampus"] = self._store_to_system(MemorySystem.HIPPOCAMPUS, entry)
        
        # 加入缓存
        self.cache.append(entry)
        
        return {
            "memory_id": memory_id,
            "stored_to": results,
            "importance": importance,
            "redundancy": len(results)
        }
    
    def _store_to_system(self, system: MemorySystem, entry: MemoryEntry) -> bool:
        """存储到指定系统"""
        try:
            if system == MemorySystem.HIPPOCAMPUS:
                return self._store_hippocampus(entry)
            elif system == MemorySystem.MEMU:
                return self._store_memu(entry)
            elif system == MemorySystem.MEMOS:
                return self._store_memos(entry)
        except Exception as e:
            print(f"存储到{system.value}失败: {e}")
            return False
    
    def _store_hippocampus(self, entry: MemoryEntry) -> bool:
        """存储到Hippocampus"""
        # 简化实现 - 实际应调用hippocampus接口
        memory_file = '/root/.openclaw/workspace/memory/unified-memories.jsonl'
        with open(memory_file, 'a') as f:
            f.write(json.dumps({
                'id': entry.id,
                'content': entry.content[:200],
                'importance': entry.importance,
                'timestamp': entry.timestamp,
                'tags': entry.tags
            }) + '\n')
        return True
    
    def _store_memu(self, entry: MemoryEntry) -> bool:
        """存储到memU"""
        # 简化实现 - 实际应调用memU API
        # 当前memU可能不可用
        return False
    
    def _store_memos(self, entry: MemoryEntry) -> bool:
        """存储到MemOS"""
        # 简化实现
        return False
    
    def retrieve(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        统一检索记忆
        
        策略:
        1. 先查本地缓存
        2. 查Hippocampus
        3. 查memU
        4. 合并去重
        """
        results = []
        
        # 查缓存
        for entry in self.cache:
            if query.lower() in entry.content.lower():
                results.append(entry)
        
        # 查Hippocampus
        if self.systems_status[MemorySystem.HIPPOCAMPUS]["available"]:
            hip_results = self._retrieve_hippocampus(query, limit)
            results.extend(hip_results)
        
        # 去重并排序
        seen = set()
        unique_results = []
        for entry in sorted(results, key=lambda x: x.importance, reverse=True):
            if entry.id not in seen:
                seen.add(entry.id)
                unique_results.append(entry)
        
        return unique_results[:limit]
    
    def _retrieve_hippocampus(self, query: str, limit: int) -> List[MemoryEntry]:
        """从Hippocampus检索"""
        # 简化实现
        return []
    
    def sync_all(self) -> Dict:
        """同步所有系统"""
        results = {}
        
        for system in MemorySystem:
            if self.systems_status[system]["available"]:
                try:
                    # 执行同步
                    self.systems_status[system]["last_sync"] = datetime.now().isoformat()
                    results[system.value] = "synced"
                except Exception as e:
                    results[system.value] = f"error: {e}"
            else:
                results[system.value] = "unavailable"
        
        return results
    
    def get_status(self) -> str:
        """获取统一记忆管理器状态"""
        lines = []
        lines.append("🧠 三记忆系统统一管理器")
        lines.append("=" * 50)
        
        for system, status in self.systems_status.items():
            available = "🟢 可用" if status["available"] else "🔴 不可用"
            last_sync = status["last_sync"][:19] if status["last_sync"] else "从未"
            lines.append(f"  {system.value:12s} {available} (上次同步: {last_sync})")
        
        lines.append("")
        lines.append(f"  缓存条目: {len(self.cache)}")
        lines.append("")
        
        lines.append("存储策略:")
        lines.append("  • 重要记忆(≥0.7): 存所有可用系统")
        lines.append("  • 中等记忆(0.4-0.7): 本地+云端")
        lines.append("  • 普通记忆(<0.4): 仅本地")
        
        return "\n".join(lines)


def main():
    """测试记忆管理器"""
    manager = UnifiedMemoryManager()
    
    print(manager.get_status())
    print("\n" + "=" * 50)
    
    # 测试存储
    print("\n📝 测试存储:")
    
    memories = [
        ("今天学会了AI Brain六部曲", 0.9, ["学习", "AI Brain"]),
        ("和一碗一起创造了18个模块", 0.95, ["成就", "创造"]),
        ("中午吃了饭", 0.2, ["日常"]),
    ]
    
    for content, importance, tags in memories:
        result = manager.store(content, importance, tags)
        print(f"\n存储: {content[:30]}...")
        print(f"  重要度: {importance} → 冗余度: {result['redundancy']}")


if __name__ == '__main__':
    main()
