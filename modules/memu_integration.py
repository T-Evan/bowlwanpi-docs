"""
memU 记忆集成 - OpenClaw/碗皮 适配器
自动记忆和检索相关上下文
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/modules')

from memu_client import get_memory_client
from datetime import datetime
import re

class MemUIntegration:
    """
    memU 与 BowlWanpi 的集成层
    """
    
    def __init__(self):
        self.memory = get_memory_client()
        self.enabled = self.memory.api_key != ""
        
    def process_incoming_message(self, message: str, user_id: str = "一碗") -> str:
        """
        处理用户输入，检索相关记忆，增强上下文
        
        Returns:
            增强后的系统提示（包含相关记忆）
        """
        if not self.enabled:
            return ""
        
        try:
            # 检索相关记忆
            memories = self.memory.retrieve(message, limit=3)
            
            if not memories:
                return ""
            
            # 构建记忆上下文
            memory_context = "## 💭 相关记忆\n\n"
            for i, mem in enumerate(memories, 1):
                content = mem.get("content", "")
                # 截断过长的记忆
                if len(content) > 200:
                    content = content[:200] + "..."
                memory_context += f"{i}. {content}\n"
            
            memory_context += "\n在回复时，可以适当引用这些记忆，让一碗感觉你记得他。"
            
            return memory_context
            
        except Exception as e:
            print(f"[MemU Integration] 检索失败: {e}")
            return ""
    
    def process_outgoing_message(self, user_message: str, assistant_response: str, 
                                  user_id: str = "一碗") -> bool:
        """
        处理助手回复，判断是否需要存储到记忆
        
        Returns:
            是否成功存储
        """
        if not self.enabled:
            return False
        
        try:
            # 判断这是否是重要信息
            combined = f"User: {user_message}\nAssistant: {assistant_response}"
            
            # 存储到记忆
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "type": "conversation",
                "user": user_id,
                "topic": self._extract_topic(user_message)
            }
            
            return self.memory.memorize(combined, metadata)
            
        except Exception as e:
            print(f"[MemU Integration] 存储失败: {e}")
            return False
    
    def _extract_topic(self, message: str) -> str:
        """简单提取话题关键词"""
        # 常见话题关键词
        topics = {
            "技术": ["代码", "编程", "python", "api", "开发"],
            "生活": ["吃饭", "睡觉", "天气", "茶", "咖啡"],
            "工作": ["项目", "任务", "会议", "deadline"],
            "娱乐": ["游戏", "电影", "音乐", "视频"],
            "记忆": ["记住", "记忆", "提醒", "备忘"]
        }
        
        message_lower = message.lower()
        for topic, keywords in topics.items():
            if any(kw in message_lower for kw in keywords):
                return topic
        
        return "general"
    
    def get_memory_summary(self, days: int = 7) -> str:
        """获取近期记忆摘要"""
        if not self.enabled:
            return "记忆系统未启用"
        
        return self.memory.summarize_memories(days)
    
    def is_important_info(self, message: str) -> bool:
        """判断消息是否包含重要信息，需要记忆"""
        # 重要信息模式
        important_patterns = [
            r"我喜欢?",
            r"我讨厌?",
            r"我记得?",
            r"请不要忘记?",
            r"提醒我?",
            r"我的.*是",
            r"我住在?",
            r"我在.*工作",
            r"我的生日",
            r"重要的"
        ]
        
        message_lower = message.lower()
        for pattern in important_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False


# 全局集成实例
_memu_integration = None

def get_memu_integration() -> MemUIntegration:
    """获取 memU 集成单例"""
    global _memu_integration
    if _memu_integration is None:
        _memu_integration = MemUIntegration()
    return _memu_integration


# 便捷函数
def enhance_prompt_with_memory(user_message: str) -> str:
    """增强系统提示，加入相关记忆"""
    integration = get_memu_integration()
    memory_context = integration.process_incoming_message(user_message)
    return memory_context

def store_conversation(user_message: str, assistant_response: str) -> bool:
    """存储对话到记忆"""
    integration = get_memu_integration()
    return integration.process_outgoing_message(user_message, assistant_response)


# 测试
if __name__ == "__main__":
    print("🧠 测试 memU 集成...")
    
    integration = get_memu_integration()
    
    if integration.enabled:
        print("✅ 记忆系统已启用")
        
        # 测试存储
        store_conversation("我喜欢喝绿茶", "好的，我记住了你喜欢绿茶")
        
        # 测试检索
        context = enhance_prompt_with_memory("茶")
        print(f"记忆上下文:\n{context}")
    else:
        print("❌ 记忆系统未启用（API Key 无效）")
