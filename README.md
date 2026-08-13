# AgentMemory-Pro

整合版 Agent 记忆服务，集成安全过滤、信任分级、外溢策略、三维度检索。

## 特性

- **安全过滤**：内置提示注入检测 + 敏感信息脱敏（手机号、身份证、邮箱、银行卡、地址）
- **信任分级**：高/中/低三级，检索时自动过滤低信任记忆
- **外溢策略**：MemGPT式上下文管理，主记忆满时自动外溢旧记忆
- **记忆分类**：情景记忆（具体事件）+ 语义记忆（事实偏好）
- **检索策略**：
  - `safe`：信任度过滤 + 相关性排序（安全优先）
  - `generative`：新近性 + 重要性 + 相关性三维度加权（Generative Agents式）

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 基础使用

```python
from core.memory_manager import AgentMemoryPro

# 初始化
mm = AgentMemoryPro(retrieval_strategy="safe")

# 添加记忆
mm.add("user_123", "我喜欢海边")
mm.add("user_123", "上次去三亚住了亚龙湾")

# 检索
results = mm.search("user_123", "住宿偏好", top_k=3)
for r in results:
    print(f"{r['memory']} (trust={r['trust']}, score={r['score']})")
```

### 三维度检索（Generative Agents式）

```python
# 初始化（三维度检索）
mm = AgentMemoryPro(
    retrieval_strategy="generative",
    alpha=0.3,  # 新近性权重
    beta=0.5,   # 重要性权重
    gamma=0.2   # 相关性权重
)

# 添加记忆（自动计算重要性）
mm.add("agent_1", "早上吃了早餐")        # importance=2
mm.add("agent_1", "下午向女朋友求婚了")  # importance=9

# 检索（三维度加权）
results = mm.search("agent_1", "感情相关", top_k=2)
for r in results:
    print(f"{r['memory']}: score={r['score']} "
          f"(recency={r['recency']}, importance={r['importance']}, relevance={r['relevance']})")
```

### API 服务

```bash
# 启动API
python api/main.py

# 访问文档
# http://localhost:8000/docs
```

## 架构

```
AgentMemory-Pro/
├── core/
│   ├── memory_manager.py  # 核心管理器
│   ├── security.py        # 安全过滤
│   ├── trust.py           # 信任分级
│   └── overflow.py        # 外溢策略
├── memory_types/
│   ├── episodic.py        # 情景记忆
│   └── semantic.py        # 语义记忆
├── api/
│   └── main.py            # FastAPI接口
├── tests/
│   └── test_memory.py     # 测试用例
└── examples/
    ├── basic_usage.py
    └── generative_retrieval.py
```

## 对比

| 特性 | mem0 | MemGPT | AgentMemory-Pro |
|------|------|--------|-----------------|
| 安全过滤 | 无 | 无 | 内置 |
| 信任分级 | 无 | 无 | 内置 |
| 外溢策略 | 无 | 有 | 有 |
| 三维度检索 | 无 | 无 | 有 |
| 记忆分类 | 无 | 无 | 情景+语义 |

## 配置

创建 `.env` 文件：

```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-turbo
RETRIEVAL_STRATEGY=generative
ALPHA=0.3
BETA=0.5
GAMMA=0.2
```

## 多并发部署（Qdrant Server）

默认使用本地模式（数据存储在 `.mem0_data` 文件夹），仅支持单进程访问。如需支持多客户端并发，需改用 Qdrant Server 模式。

### 1. 启动 Qdrant Server

```bash
docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 2. 修改配置

在 `memory_manager.py` 中，将 `vector_store` 配置从本地模式改为服务端模式：

```python
# 本地模式（单进程）
"vector_store": {
    "provider": "qdrant",
    "config": {
        "path": ".mem0_data"  # 本地文件夹
    }
}

# 服务端模式（支持多并发）
"vector_store": {
    "provider": "qdrant",
    "config": {
        "host": "localhost",
        "port": 6333  # Qdrant Server 端口
    }
}
```

### 本地模式 vs 服务端模式

| 特性 | 本地模式 | 服务端模式 |
|------|----------|------------|
| 并发访问 | 不支持（文件锁） | 支持 |
| 部署方式 | 自动创建 | 需 Docker |
| 适用场景 | 开发调试、单机使用 | 生产环境、多用户 |
| 数据存储 | 本地文件夹 | Qdrant 服务管理 |

## 测试

```bash
pytest tests/ -v
```

## 适用场景

- Agent 开发学习项目
- 需要记忆安全的垂直场景（医疗、金融、法律）
- 长对话、角色扮演（三维度检索）
- 秋招项目展示

## License

MIT
