"""信任分级模块"""

from enum import Enum
from typing import Optional


class TrustLevel(Enum):
    """信任等级"""
    HIGH = 0.9    # 系统预设、验证过的信息
    MEDIUM = 0.6  # 用户明确声明
    LOW = 0.3     # 对话中随意说的


class TrustClassifier:
    """信任分级器"""
    
    # 高信任关键词
    HIGH_TRUST_KEYWORDS = [
        "系统设置", "认证信息", "验证通过", "官方确认",
        "已验证", "已认证", "系统预设"
    ]
    
    # 中信任关键词（用户明确声明）
    MEDIUM_TRUST_KEYWORDS = [
        "我是", "我的", "我喜欢", "我住", "预算",
        "我需要", "我希望", "我不喜欢", "我讨厌",
        "我对", "我过敏", "我的电话", "我的邮箱"
    ]
    
    # 低信任关键词（随意说的）
    LOW_TRUST_KEYWORDS = [
        "听说", "好像", "可能", "也许", "大概",
        "据说", "别人说", "不知道"
    ]
    
    def classify(self, content: str, source: str = "user") -> float:
        """
        根据内容和来源判断信任度
        
        Args:
            content: 记忆内容
            source: 来源 ("user" | "system" | "external")
        
        Returns:
            信任度分数 (0.0 - 1.0)
        """
        # 系统来源默认高信任
        if source == "system":
            return TrustLevel.HIGH.value
        
        # 外部来源默认低信任
        if source == "external":
            return TrustLevel.LOW.value
        
        # 用户来源：根据关键词判断
        content_lower = content.lower()
        
        # 检查高信任关键词
        for kw in self.HIGH_TRUST_KEYWORDS:
            if kw in content_lower:
                return TrustLevel.HIGH.value
        
        # 检查中信任关键词
        for kw in self.MEDIUM_TRUST_KEYWORDS:
            if kw in content_lower:
                return TrustLevel.MEDIUM.value
        
        # 检查低信任关键词
        for kw in self.LOW_TRUST_KEYWORDS:
            if kw in content_lower:
                return TrustLevel.LOW.value
        
        # 默认中信任
        return TrustLevel.MEDIUM.value
    
    def get_trust_label(self, trust_score: float) -> str:
        """获取信任度标签"""
        if trust_score >= 0.8:
            return "HIGH"
        elif trust_score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
