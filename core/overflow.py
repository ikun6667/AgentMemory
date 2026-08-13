"""外溢策略模块：管理上下文窗口"""

from typing import List, Dict


class OverflowManager:
    """外溢管理器：当主记忆满时，外溢旧记忆到外记忆"""
    
    def __init__(self, max_context_tokens: int = 4000):
        """
        Args:
            max_context_tokens: 主记忆最大token数
        """
        self.max_tokens = max_context_tokens
        self.current_tokens = 0
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算token数（简化版）
        
        中文约1.5-2 token/字，英文约0.75 token/词
        """
        # 简单估算：中文1字≈1.5token，英文1词≈1.3token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        return int(chinese_chars * 1.5 + other_chars * 0.5)
    
    def should_overflow(self, new_content: str) -> bool:
        """判断是否需要外溢"""
        new_tokens = self.estimate_tokens(new_content)
        return (self.current_tokens + new_tokens) > (self.max_tokens * 0.8)
    
    def select_victims(self, memories: List[Dict], keep_count: int = 5) -> List[Dict]:
        """
        选择要外溢的记忆
        
        策略：保留最近keep_count条，其余外溢
        
        Args:
            memories: 记忆列表
            keep_count: 保留条数
        
        Returns:
            要外溢的记忆列表
        """
        if len(memories) <= keep_count:
            return []
        
        # 按时间排序，旧的先外溢
        sorted_memories = sorted(
            memories,
            key=lambda x: x.get("timestamp", ""),
            reverse=True  # 新的在前
        )
        
        # 保留前keep_count条，其余外溢
        victims = sorted_memories[keep_count:]
        return victims
    
    def add_tokens(self, content: str):
        """增加当前token计数"""
        self.current_tokens += self.estimate_tokens(content)
    
    def remove_tokens(self, content: str):
        """减少当前token计数"""
        self.current_tokens -= self.estimate_tokens(content)
        self.current_tokens = max(0, self.current_tokens)
    
    def reset(self):
        """重置token计数"""
        self.current_tokens = 0
