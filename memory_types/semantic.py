"""语义记忆：事实、偏好"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SemanticMemory:
    """
    语义记忆：记录事实、偏好、知识
    
    例如：用户喜欢海边、用户对海鲜过敏、预算5000
    """
    fact: str                   # 事实描述
    category: str = "general"   # 分类（preference/fact/health/general）
    confidence: float = 0.8     # 置信度 (0.0 - 1.0)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "type": "semantic",
            "fact": self.fact,
            "category": self.category,
            "confidence": self.confidence,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SemanticMemory":
        """从字典创建"""
        return cls(
            fact=data.get("fact", ""),
            category=data.get("category", "general"),
            confidence=data.get("confidence", 0.8),
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        return f"[语义记忆] {self.fact} (类别: {self.category}, 置信度: {self.confidence})"
