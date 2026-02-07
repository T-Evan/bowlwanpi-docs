#!/usr/bin/env python3
"""
BowlWanpi 记忆增强对话流程
每次对话自动执行: 搜索记忆 -> 回答 -> 记录对话
"""
import sys
import json
sys.path.insert(0, '/root/.openclaw/workspace')

from modules.mcp_client import call_mcp_tool_sync

class MemoryEnhancedConversation:
    """记忆增强对话类"""
    
    def __init__(self):
        self.conversation_first_message = None
        self.messages = []
    
    def start_conversation(self, first_message: str):
        """开始新对话"""
        self.conversation_first_message = first_message
        self.messages = []
    
    def search_relevant_memories(self, query: str, limit: int = 10):
        """
        搜索相关记忆
        
        Args:
            query: 搜索关键词（基于当前话题）
            limit: 返回记忆数量
        """
        try:
            result = call_mcp_tool_sync(
                "memos-api-mcp",
                "search_memory",
                query=query,
                conversation_first_message=self.conversation_first_message or query,
                memory_limit_number=limit
            )
            
            # 解析结果
            if result and result.content:
                content = json.loads(result.content[0].text)
                if content.get('code') == 0:
                    data = content.get('data', {})
                    memories = data.get('memory_detail_list', [])
                    preferences = data.get('preference_detail_list', [])
                    
                    return {
                        'memories': memories,
                        'preferences': preferences,
                        'count': len(memories) + len(preferences)
                    }
            
            return {'memories': [], 'preferences': [], 'count': 0}
            
        except Exception as e:
            print(f"⚠️ 搜索记忆失败: {e}")
            return {'memories': [], 'preferences': [], 'count': 0}
    
    def add_message(self, user_content: str, assistant_content: str):
        """
        记录对话（必须调用！）
        
        Args:
            user_content: 用户说的话
            assistant_content: AI的回复
        """
        try:
            # 确保有 conversation_first_message
            if not self.conversation_first_message:
                self.conversation_first_message = user_content[:50]
            
            # 添加到本地消息列表
            from datetime import datetime
            current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            self.messages.append({
                "role": "user",
                "content": user_content,
                "chat_time": current_time
            })
            self.messages.append({
                "role": "assistant",
                "content": assistant_content,
                "chat_time": current_time
            })
            
            # 调用 MCP 工具记录
            result = call_mcp_tool_sync(
                "memos-api-mcp",
                "add_message",
                conversation_first_message=self.conversation_first_message,
                messages=self.messages[-2:]  # 只发送最近两条
            )
            
            # 检查结果
            if result and result.content:
                content = json.loads(result.content[0].text)
                if content.get('code') == 0:
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ 记录对话失败: {e}")
            return False
    
    def format_memories_for_prompt(self, memories: dict) -> str:
        """
        将记忆格式化为提示词
        
        Args:
            memories: 记忆字典
        """
        if memories['count'] == 0:
            return ""
        
        prompt_parts = ["\n📚 **相关记忆**:\n"]
        
        # 添加偏好
        for pref in memories['preferences'][:3]:
            content = pref.get('content', '')
            if content:
                prompt_parts.append(f"• [偏好] {content}")
        
        # 添加记忆
        for mem in memories['memories'][:5]:
            content = mem.get('content', '')
            mem_type = mem.get('memory_type', '记忆')
            if content:
                prompt_parts.append(f"• [{mem_type}] {content}")
        
        return "\n".join(prompt_parts)


# 全局对话实例
_conversation = MemoryEnhancedConversation()


def search_memories(query: str) -> dict:
    """
    搜索相关记忆（便捷函数）
    
    示例:
        memories = search_memories("用户偏好")
        if memories['count'] > 0:
            print(f"找到 {memories['count']} 条记忆")
    """
    return _conversation.search_relevant_memories(query)


def record_dialogue(user_msg: str, assistant_msg: str) -> bool:
    """
    记录对话（便捷函数）
    
    示例:
        success = record_dialogue("你好", "你好！很高兴见到你")
        if success:
            print("✅ 对话已记录")
    """
    return _conversation.add_message(user_msg, assistant_msg)


def format_memories(memories: dict) -> str:
    """格式化记忆为提示词"""
    return _conversation.format_memories_for_prompt(memories)


if __name__ == "__main__":
    # 测试
    print("🧠 记忆增强对话测试\n")
    
    # 1. 搜索记忆
    print("1️⃣ 搜索记忆...")
    memories = search_memories("一碗")
    print(f"   找到 {memories['count']} 条记忆")
    
    # 2. 格式化记忆
    if memories['count'] > 0:
        print("\n2️⃣ 格式化记忆:")
        prompt = format_memories(memories)
        print(prompt)
    
    # 3. 记录对话
    print("\n3️⃣ 记录对话...")
    success = record_dialogue(
        "测试记忆系统",
        "记忆系统测试成功！我会记住你的偏好和重要信息。"
    )
    print(f"   {'✅' if success else '❌'} 记录{'成功' if success else '失败'}")
    
    print("\n✨ 测试完成！")
