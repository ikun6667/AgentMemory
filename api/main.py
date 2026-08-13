"""FastAPI 接口"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

from core.memory_manager import AgentMemoryPro

load_dotenv()

app = FastAPI(
    title="AgentMemory-Pro",
    description="整合版 Agent 记忆服务：安全过滤 + 信任分级 + 三维度检索",
    version="0.1.0"
)

# 初始化记忆管理器
memory_manager = AgentMemoryPro(
    retrieval_strategy=os.getenv("RETRIEVAL_STRATEGY", "generative"),
    alpha=float(os.getenv("ALPHA", 0.3)),
    beta=float(os.getenv("BETA", 0.5)),
    gamma=float(os.getenv("GAMMA", 0.2)),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_base_url=os.getenv("OPENAI_BASE_URL"),
    model_name=os.getenv("MODEL_NAME", "gpt-3.5-turbo")
)


class AddMemoryRequest(BaseModel):
    """添加记忆请求"""
    user_id: str
    content: str
    memory_type: str = "auto"
    source: str = "user"


class SearchMemoryRequest(BaseModel):
    """检索记忆请求"""
    user_id: str
    query: str
    top_k: int = 5
    min_trust: float = 0.5
    memory_type: Optional[str] = None
    strategy: Optional[str] = None


class MemoryResponse(BaseModel):
    """记忆响应"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None


class SearchResponse(BaseModel):
    """检索响应"""
    memories: List[Dict]
    count: int


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "AgentMemory-Pro API",
        "version": "0.1.0",
        "docs": "/docs",
        "features": [
            "安全过滤（注入检测 + 脱敏）",
            "信任分级（高/中/低）",
            "外溢策略（MemGPT式）",
            "记忆分类（情景 + 语义）",
            "检索策略（safe / generative）"
        ]
    }


@app.post("/memory/add", response_model=MemoryResponse)
def add_memory(req: AddMemoryRequest):
    """添加记忆"""
    result = memory_manager.add(
        user_id=req.user_id,
        content=req.content,
        memory_type=req.memory_type,
        source=req.source
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return MemoryResponse(success=True, data=result)


@app.post("/memory/search", response_model=SearchResponse)
def search_memory(req: SearchMemoryRequest):
    """检索记忆"""
    results = memory_manager.search(
        user_id=req.user_id,
        query=req.query,
        top_k=req.top_k,
        min_trust=req.min_trust,
        memory_type=req.memory_type,
        strategy=req.strategy
    )
    
    return SearchResponse(memories=results, count=len(results))


@app.get("/memory/stats")
def get_stats():
    """获取统计信息"""
    return memory_manager.get_stats()


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
