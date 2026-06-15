# RAG 智能知识库问答系统

基于检索增强生成（RAG）架构的私有知识库智能问答系统。支持企业用户上传内部文档，自动进行文档解析、向量化、知识图谱构建，并向终端用户提供基于私有知识的精准问答服务。

## 功能特性

### 核心功能

- **智能问答**：基于 RAG 架构，结合向量检索与知识图谱，返回有出处的精准回答
- **知识库管理**：支持 PDF、DOCX、TXT 格式文档上传、自动解析与向量化
- **知识图谱**：LLM 自动提取实体关系，ECharts 力导向图可视化展示
- **多轮对话**：支持上下文关联的连续追问

### 管理功能

- **用户管理**：角色权限控制（管理员/普通用户）
- **模型管理**：多供应商支持，灵活切换 LLM 和 Embedding 模型
- **系统配置**：可调节检索参数、分块策略、LLM 参数等
- **工作台**：系统概览、趋势统计、服务状态监控

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Element Plus + Pinia + ECharts + Vite |
| **后端** | FastAPI + SQLAlchemy + Pydantic + httpx |
| **数据库** | MySQL 8.0 + ChromaDB + Neo4j 4.4 + Redis 7 |
| **部署** | Docker + Docker Compose |
| **LLM** | DeepSeek API（支持 OpenAI 兼容接口） |

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                           │
│         Views → Components → Stores → API                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                            │
│      Routers → Services → DAO → Models                      │
└─────────────────────────────────────────────────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
    ┌───────┐    ┌──────────┐    ┌────────┐    ┌────────┐
    │ MySQL │    │ ChromaDB │    │ Neo4j  │    │ Redis  │
    │ 关系  │    │  向量库  │    │ 图数据库│    │  缓存  │
    └───────┘    └──────────┘    └────────┘    └────────┘
```

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- 至少 4GB 可用内存
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）

### 部署步骤

1. **克隆项目**

```bash
git clone https://github.com/your-username/RAG2.0.git
cd RAG2.0/docker
```

2. **配置环境变量**

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必需参数：

```env
# DeepSeek API（必需）
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 加密密钥（必需，32位十六进制）
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef

# JWT 密钥（建议修改）
JWT_SECRET_KEY=your_jwt_secret_key
```

3. **启动服务**

```bash
docker-compose up -d
```

4. **访问系统**

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:15173 |
| 后端 API | http://localhost:18080 |
| API 文档 | http://localhost:18080/docs |
| Neo4j 控制台 | http://localhost:17474 |

5. **默认登录**

- 管理员：`admin` / `admin123`

## 项目结构

```
RAG2.0/
├── docker/
│   ├── docker-compose.yml       # 服务编排
│   ├── .env.example             # 环境变量模板
│   ├── mysql/
│   │   └── init.sql             # 数据库初始化
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py          # 应用入口
│   │       ├── config.py        # 配置管理
│   │       ├── database.py      # 数据库连接
│   │       ├── models/          # 数据模型
│   │       ├── schemas/         # 数据模式
│   │       ├── routers/         # API 路由
│   │       ├── services/        # 业务逻辑
│   │       └── dao/             # 数据访问
│   └── frontend/
│       ├── Dockerfile
│       ├── package.json
│       └── src/
│           ├── views/           # 页面视图
│           ├── components/      # 公共组件
│           ├── stores/          # 状态管理
│           ├── api/             # 接口封装
│           └── router/          # 路由配置
├── 需求说明书.md
├── 概要设计说明书.md
├── 详细设计说明书.md
├── 数据库设计说明书.md
└── 开发计划.md
```

## 服务端口

| 服务 | 容器端口 | 宿主机端口 | 用途 |
|------|----------|------------|------|
| rag-frontend | 5173 | 15173 | 前端 Web 界面 |
| rag-backend | 8000 | 18080 | 后端 API 服务 |
| rag-mysql | 3306 | 13307 | MySQL 数据库 |
| rag-redis | 6379 | 16379 | Redis 缓存 |
| rag-neo4j | 7474/7687 | 17474/17687 | Neo4j 图数据库 |
| rag-chromadb | 8000 | 18001 | ChromaDB 向量库 |

## 使用指南

### 知识库管理

1. 以管理员身份登录系统
2. 进入「知识库」页面，上传 PDF/DOCX/TXT 文档
3. 系统自动完成解析、分块、向量化和知识图谱构建
4. 文档状态变为「已完成」后即可用于问答

### 智能问答

1. 进入「问答」页面，选择或新建对话
2. 输入问题，系统自动检索相关知识并生成回答
3. 回答中会标注引用来源，支持点击查看原文

### 模型配置

1. 进入「模型管理」页面
2. 添加新的模型供应商（需支持 OpenAI 兼容接口）
3. 配置对话模型或 Embedding 模型
4. 设置默认使用的模型

## 环境变量说明

| 变量名 | 必需 | 说明 | 默认值 |
|--------|------|------|--------|
| DEEPSEEK_API_KEY | 是 | DeepSeek API 密钥 | - |
| DEEPSEEK_BASE_URL | 否 | API 基础地址 | https://api.deepseek.com/v1 |
| ENCRYPTION_KEY | 是 | AES-256 加密密钥（32位十六进制） | - |
| JWT_SECRET_KEY | 是 | JWT 签名密钥 | - |
| MYSQL_ROOT_PASSWORD | 否 | MySQL root 密码 | rag_root_2026 |
| MYSQL_DATABASE | 否 | 数据库名 | rag_db |
| MYSQL_USER | 否 | 数据库用户 | rag_user |
| MYSQL_PASSWORD | 否 | 数据库密码 | rag_pass_2026 |
| REDIS_PASSWORD | 否 | Redis 密码 | rag_redis_2026 |
| NEO4J_AUTH | 否 | Neo4j 认证 | neo4j/rag_neo4j_2026 |

## 系统配置（运行时）

通过管理界面可调节的参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| temperature | LLM 温度参数 | 0.7 |
| top_p | LLM Top-P 参数 | 0.9 |
| max_tokens | 最大 Token 数 | 2048 |
| top_k | 向量检索返回数 | 5 |
| similarity_threshold | 相似度阈值 | 0.6 |
| chunk_size | 文本分块大小 | 512 |
| chunk_overlap | 分块重叠长度 | 128 |
| kg_enabled | 是否启用知识图谱 | true |
| history_rounds | 多轮对话历史轮数 | 5 |

## 常见问题

### Q: 如何更换其他 LLM 供应商？

进入「模型管理」→「模型供应商」添加新供应商，然后在「对话模型」中添加新模型并设为默认。系统支持所有 OpenAI 兼容接口。

### Q: 如何备份数据？

```bash
# 备份 MySQL
docker exec rag-mysql mysqldump -u root -p rag_db > backup.sql

# 备份 ChromaDB（向量数据）
docker cp rag-chromadb:/chroma/chroma ./chroma-backup

# 备份 Neo4j（知识图谱）
docker cp rag-neo4j:/data ./neo4j-backup
```

### Q: 文档解析失败怎么办？

检查文档格式是否正确，查看文档详情中的错误信息。常见原因：
- PDF 为扫描件（无文字层）
- 文档加密或损坏
- 文件过大导致超时

## 开发说明

### 本地开发环境

```bash
# 后端
cd docker/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd docker/frontend
npm install
npm run dev
```

### API 文档

启动后端服务后访问：
- Swagger UI：http://localhost:18080/docs
- ReDoc：http://localhost:18080/redoc

## 许可证

本项目为课程设计作品，仅供学习参考。

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue 3](https://vuejs.org/)
- [Element Plus](https://element-plus.org/)
- [ChromaDB](https://www.trychroma.com/)
- [Neo4j](https://neo4j.com/)
- [DeepSeek](https://deepseek.com/)
