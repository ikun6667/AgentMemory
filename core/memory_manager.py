"""核心记忆管理器：整合安全过滤、信任分级、外溢策略、三维度检索"""

import math
from datetime import datetime
from typing import List, Dict, Optional

import os

from mem0 import Memory
from openai import OpenAI

from .security import SecurityFilter
from .trust import TrustClassifier, TrustLevel
from .overflow import OverflowManager
from memory_types.episodic import EpisodicMemory
from memory_types.semantic import SemanticMemory


class AgentMemoryPro:
    """
    整合版记忆管理器
    
    特性：
    - 安全过滤：注入检测 + 敏感信息脱敏
    - 信任分级：高/中/低三级，检索时自动过滤
    - 外溢策略：MemGPT式上下文管理
    - 记忆分类：情景记忆 + 语义记忆
    - 检索策略：安全优先 或 三维度（Generative Agents式）
    """
    
    def __init__(
        self,
        max_context_tokens: int = 4000,
        retrieval_strategy: str = "safe",
        alpha: float = 0.3,
        beta: float = 0.5,
        gamma: float = 0.2,
        openai_api_key: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo"
    ):
        """
        初始化记忆管理器
        
        Args:
            max_context_tokens: 主记忆最大token数
            retrieval_strategy: 检索策略 ("safe" | "generative")
            alpha: 新近性权重（三维度检索）
            beta: 重要性权重（三维度检索）
            gamma: 相关性权重（三维度检索）
            openai_api_key: OpenAI API密钥（用于重要性打分）
            openai_base_url: OpenAI API自定义地址（中转/代理/千问等）
            model_name: LLM模型名称（如 gpt-3.5-turbo, qwen-turbo）
        """
        # 配置mem0：用千问text-embedding-v2（1536维，匹配mem0默认值）
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mem0_data_path = os.path.join(project_root, ".mem0_data")
        os.makedirs(mem0_data_path, exist_ok=True)
        
        mem0_config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "mem0",
                    "path": mem0_data_path,
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-v2",
                    "api_key": openai_api_key or "",
                    "openai_base_url": openai_base_url or ""
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": model_name,
                    "api_key": openai_api_key or "",
                    "openai_base_url": openai_base_url or ""
                }
            }
        }
        self.storage = Memory.from_config(mem0_config)
        llm_kwargs = {}
        if openai_api_key:
            llm_kwargs["api_key"] = openai_api_key
        if openai_base_url:
            llm_kwargs["base_url"] = openai_base_url
        self.llm = OpenAI(**llm_kwargs)
        self.model_name = model_name
        
        # 基础模块
        self.security = SecurityFilter()
        self.trust = TrustClassifier()
        self.overflow = OverflowManager(max_context_tokens)

        
        # 检索策略
        self.retrieval_strategy = retrieval_strategy
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        
        # 主记忆/外记忆
        self.recent_memories: List[Dict] = []
        self.archived_memories: List[Dict] = []
    
    def add(
        self,
        user_id: str,
        content: str,
        memory_type: str = "auto",
        source: str = "user",
        rate_importance: bool = True
    ) -> Dict:
        """
        添加记忆
        
        Args:
            user_id: 用户ID
            content: 记忆内容
            memory_type: "episodic" | "semantic" | "auto"
            source: "user" | "system" | "external"
            rate_importance: 是否让LLM打分重要性
        
        Returns:
            {"success": bool, "trust": float, "type": str, "importance": int, "error": str}
        """
        # 1. 安全过滤
        is_safe, processed_content, error_msg = self.security.process(content)
        if not is_safe:
            return {"success": False, "error": error_msg}
        
        # 2. 信任分级
        trust_level = self.trust.classify(processed_content, source)
        
        # 3. 推断记忆类型
        if memory_type == "auto":
            memory_type = self._infer_type(processed_content)
        
        # 4. 计算重要性
        importance = None
        if rate_importance or self.retrieval_strategy == "generative":
            importance = self._rate_importance(processed_content)
        
        # 5. 构建metadata
        metadata = {
            "type": memory_type,
            "trust": trust_level,
            "timestamp": datetime.now().isoformat(),
            "importance": importance,
            "source": source
        }
        
        # 6. 存入mem0
        self.storage.add(processed_content, user_id=user_id, metadata=metadata)
        
        # 7. 加入主记忆
        memory_dict = {"content": processed_content, **metadata}
        self.recent_memories.append(memory_dict)
        self.overflow.add_tokens(processed_content)
        
        # 8. 检查外溢
        if self.overflow.should_overflow(processed_content):
            self._overflow_old_memories(user_id)
        
        return {
            "success": True,
            "trust": trust_level,
            "type": memory_type,
            "importance": importance
        }
    
    def search(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
        min_trust: float = 0.5,
        memory_type: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> List[Dict]:
        """
        检索记忆
        
        Args:
            user_id: 用户ID
            query: 查询内容
            top_k: 返回条数
            min_trust: 最低信任度（safe策略）
            memory_type: 过滤记忆类型
            strategy: "safe" | "generative" | None(使用默认)
        
        Returns:
            记忆列表，每条包含 memory, score, trust, type, timestamp 等
        """
        # 1. 安全过滤查询
        is_safe, processed_query, _ = self.security.process(query)
        if not is_safe:
            return []
        
        # 2. 从mem0粗筛候选（v2.0.18+返回{'results': [...]}格式）
        search_result = self.storage.search(processed_query, filters={"user_id": user_id}, limit=50)
        candidates = search_result.get("results", []) if isinstance(search_result, dict) else search_result
        
        # 3. 选择检索策略
        use_strategy = strategy or self.retrieval_strategy
        
        if use_strategy == "generative":
            results = self._retrieve_generative(candidates, top_k)
        else:
            results = self._retrieve_safe(candidates, min_trust, memory_type, top_k)
        
        return results
    
    def _retrieve_safe(
        self,
        candidates: List[Dict],
        min_trust: float,
        memory_type: Optional[str],
        top_k: int
    ) -> List[Dict]:
        """安全优先检索：信任度过滤 + 相关性排序"""
        filtered = []
        for r in candidates:
            metadata = r.get("metadata", {})
            
            # 信任度过滤
            if metadata.get("trust", 0.5) < min_trust:
                continue
            
            # 类型过滤
            if memory_type and metadata.get("type") != memory_type:
                continue
            
            filtered.append({
                "memory": r["memory"],
                "score": r.get("score", 0.5),
                "trust": metadata.get("trust"),
                "type": metadata.get("type"),
                "timestamp": metadata.get("timestamp"),
                "importance": metadata.get("importance")
            })
        
        # 按相关性排序
        filtered.sort(key=lambda x: x["score"], reverse=True)
        return filtered[:top_k]
    
    def _retrieve_generative(
        self,
        candidates: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """三维度检索：新近性 + 重要性 + 相关性"""
        scored = []
        
        for mem in candidates:
            metadata = mem.get("metadata", {})
            
            # 计算三维度
            recency = self._calc_recency(metadata.get("timestamp"))
            importance = (metadata.get("importance") or 5) / 10.0
            relevance = mem.get("score", 0.5)
            
            # 加权总分
            total_score = (
                self.alpha * recency +
                self.beta * importance +
                self.gamma * relevance
            )
            
            scored.append({
                "memory": mem["memory"],
                "score": round(total_score, 3),
                "recency": round(recency, 3),
                "importance": round(importance, 3),
                "relevance": round(relevance, 3),
                "trust": metadata.get("trust"),
                "type": metadata.get("type"),
                "timestamp": metadata.get("timestamp")
            })
        
        # 按总分排序
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
    
    def _rate_importance(self, content: str) -> int:
        """LLM打分重要性（1-10）"""
        prompt = f"""给这段记忆的重要性打分（1-10）：
1 = 完全无关紧要（如"我吃了早餐"）
10 = 极其重要（如"我求婚了"、"我失业了"）

记忆：{content}

只返回数字："""
        
        try:
            response = self.llm.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            score = int(response.choices[0].message.content.strip())
            return max(1, min(10, score))
        except Exception as e:
            print(f"Importance rating failed: {e}")
            return 5
    
    def _calc_recency(self, timestamp_str: Optional[str]) -> float:
        """计算新近性分数（指数衰减）"""
        if not timestamp_str:
            return 0.5
        try:
            mem_time = datetime.fromisoformat(timestamp_str)
            hours_ago = (datetime.now() - mem_time).total_seconds() / 3600
            decay_factor = 0.01
            return math.exp(-decay_factor * hours_ago)
        except:
            return 0.5
    
    def _infer_type(self, content: str) -> str:
        """推断记忆类型"""
        time_keywords = ["上次", "昨天", "今天", "刚才", "去", "住了", "去了", "做了"]
        for kw in time_keywords:
            if kw in content:
                return "episodic"
        return "semantic"
    
    def _overflow_old_memories(self, user_id: str):
        """外溢旧记忆"""
        victims = self.overflow.select_victims(self.recent_memories, keep_count=5)
        for v in victims:
            if v in self.recent_memories:
                self.recent_memories.remove(v)
                self.archived_memories.append(v)
                self.overflow.remove_tokens(v.get("content", ""))
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "recent_count": len(self.recent_memories),
            "archived_count": len(self.archived_memories),
            "current_tokens": self.overflow.current_tokens,
            "max_tokens": self.overflow.max_tokens,
            "strategy": self.retrieval_strategy
        }
