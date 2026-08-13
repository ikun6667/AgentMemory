"""情景记忆：具体事件"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class EpisodicMemory:
    """
    情景记忆：记录具体事件
    
    例如：上次去三亚旅行、昨天和朋友吃饭
    """
    event: str                          # 事件描述
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())  # 发生时间
    location: Optional[str] = None      # 地点
    participants: List[str] = field(default_factory=list)  # 参与人
    emotion: Optional[str] = None       # 情绪
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "type": "episodic",
            "event": self.event,
            "timestamp": self.timestamp,
            "location": self.location,
            "participants": self.participants,
            "emotion": self.emotion,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EpisodicMemory":
        """从字典创建"""
        return cls(
            event=data.get("event", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            location=data.get("location"),
            participants=data.get("participants", []),
            emotion=data.get("emotion"),
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        parts = [f"[情景记忆] {self.event}"]
        if self.location:
            parts.append(f"地点: {self.location}")
        if self.timestamp:
            parts.append(f"时间: {self.timestamp}")
        if self.emotion:
            parts.append(f"情绪: {self.emotion}")
        return " | ".join(parts)
