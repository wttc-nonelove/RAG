# 基于 RAG 架构的智能问答系统数据库说明书

文档版本：最终版  
项目名称：基于 RAG 架构的智能问答系统  
文档名称：RAG-数据库说明书-课设  
生成日期：2026-06-03  
依据文件：`docker/mysql/init.sql`、`docker/backend/app/models`、`docker/backend/app/dao`

## 1. 编写目的

本文档用于说明课程设计最终版本的数据库设计结果，包括关系型数据库表结构、字段约束、索引、预置数据、辅助存储方案、数据流转关系和部署验证方式。文档面向系统开发、测试、部署和答辩说明，作为后续维护数据库结构和理解数据访问逻辑的依据。

系统采用“关系型数据库 + 向量数据库 + 图数据库 + 缓存”的组合存储方案：

| 存储组件 | 版本/服务 | 主要职责 |
| --- | --- | --- |
| MySQL | MySQL 8.0 / `rag-mysql` | 用户、文档元数据、会话、消息、系统配置、模型配置、Token 使用量等结构化数据 |
| ChromaDB | `rag-chromadb` | 文档分块向量、分块原文、向量检索元数据 |
| Neo4j | Neo4j 4.4.16 / `rag-neo4j` | 知识实体、实体关系、图谱可视化和图谱增强检索 |
| Redis | Redis 7 / `rag-redis` | 缓存、异步任务和运行状态扩展预留 |
| 文件卷 | Docker volume `file_store` | 上传原始文件持久化 |

## 2. 数据库环境

### 2.1 Docker 服务配置

| 服务名 | 容器名 | 容器端口 | 宿主机端口 | 说明 |
| --- | --- | ---: | ---: | --- |
| MySQL | `rag-mysql` | 3306 | 3307 | 关系型数据库，启动时执行 `mysql/init.sql` |
| Redis | `rag-redis` | 6379 | 6379 | 缓存与异步任务支撑 |
| Neo4j HTTP | `rag-neo4j` | 7474 | 7474 | 图数据库控制台 |
| Neo4j Bolt | `rag-neo4j` | 7687 | 7687 | 后端图数据库连接 |
| ChromaDB | `rag-chromadb` | 8000 | 8001 | 向量数据库 HTTP 服务 |
| FastAPI | `rag-backend` | 8000 | 8000 | 后端 API 服务 |

### 2.2 MySQL 连接参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| 数据库名 | `rag_db` | 业务数据库 |
| 用户名 | `rag_user` | 后端应用访问用户 |
| 密码 | `rag_pass_2026` | 可通过 `.env` 覆盖 |
| 字符集 | `utf8mb4` | 支持中文、符号和多语言文本 |
| 排序规则 | `utf8mb4_unicode_ci` | 通用 Unicode 排序规则 |

后端 SQLAlchemy 异步连接 URL：

```text
mysql+aiomysql://rag_user:rag_pass_2026@rag-mysql:3306/rag_db?charset=utf8mb4
```

## 3. 总体数据架构

### 3.1 数据分层

| 层级 | 数据内容 | 存储位置 | 访问模块 |
| --- | --- | --- | --- |
| 账号与权限层 | 用户、角色、状态、密码哈希 | MySQL `users` | 认证、用户管理、路由守卫 |
| 知识库元数据层 | 文件名、类型、路径、解析状态、标签、版本 | MySQL `documents` | 文档管理、问答溯源、工作台 |
| 问答会话层 | 会话、用户消息、模型回答、引用来源 | MySQL `conversations`、`messages` | 智能问答、历史记录 |
| 系统运行配置层 | RAG 参数、分块参数、模型参数 | MySQL `system_config` | 问答、文档解析、系统配置 |
| 模型管理层 | 供应商、模型、提示词、预设 | MySQL `model_providers`、`model_configs`、`model_presets` | 模型管理、问答 |
| 统计审计层 | Chat/Embedding Token 消耗 | MySQL `token_usage` | 工作台、模型使用统计 |
| 向量检索层 | 文档分块、向量、分块元数据 | ChromaDB `kb_chunks` | 文档解析、RAG 检索 |
| 图谱增强层 | 实体、关系、文档来源 | Neo4j `Entity` 节点和关系 | 图谱管理、RAG 增强 |
| 文件存储层 | 上传的原始 PDF/DOCX/TXT/MD/Excel/CSV 文件 | Docker volume `file_store` | 文档管理、预览、重解析 |

### 3.2 MySQL 表清单

| 序号 | 表名 | 中文名称 | 主要用途 |
| ---: | --- | --- | --- |
| 1 | `users` | 用户表 | 登录认证、角色权限、账号状态 |
| 2 | `documents` | 文档元数据表 | 管理上传文件、解析状态和向量化消耗 |
| 3 | `conversations` | 会话表 | 记录用户问答会话 |
| 4 | `messages` | 消息表 | 记录用户提问、模型回答、引用来源 |
| 5 | `system_config` | 系统配置表 | 保存 RAG、LLM、分块、图谱等运行参数 |
| 6 | `model_providers` | 模型供应商表 | 保存 OpenAI 兼容供应商地址和加密 API Key |
| 7 | `model_configs` | 模型配置表 | 保存 Chat/Embedding 模型、默认模型和提示词 |
| 8 | `model_presets` | 模型预设表 | 保存可复用的提示词和生成参数组合 |
| 9 | `token_usage` | Token 使用记录表 | 独立记录问答和文档向量化 Token 消耗 |

## 4. 概念结构设计

### 4.1 实体关系

```mermaid
erDiagram
    users ||--o{ documents : uploads
    users ||--o{ conversations : owns
    users ||--o{ model_presets : creates
    conversations ||--o{ messages : contains
    model_providers ||--o{ model_configs : provides
    model_configs ||--o{ model_presets : binds

    users {
        int id PK
        varchar username UK
        varchar password_hash
        enum role
        enum status
        datetime created_at
    }

    documents {
        int id PK
        varchar filename
        enum file_type
        bigint file_size
        varchar file_path
        varchar tag
        enum parse_status
        int version
        int uploaded_by FK
        text error_message
        int embedding_tokens
        datetime created_at
        datetime updated_at
    }

    conversations {
        int id PK
        int user_id FK
        varchar title
        datetime created_at
        datetime updated_at
    }

    messages {
        int id PK
        int conversation_id FK
        enum role
        text content
        json sources
        json kg_references
        varchar model_name
        int tokens_used
        datetime created_at
    }

    model_providers {
        int id PK
        varchar provider_name UK
        varchar api_base_url
        text api_key_encrypted
        boolean is_active
        datetime created_at
    }

    model_configs {
        int id PK
        int provider_id FK
        varchar model_name
        enum model_type
        text system_prompt
        int embedding_dimension
        boolean is_default
        boolean is_active
        datetime created_at
    }

    model_presets {
        int id PK
        varchar name
        int model_config_id FK
        enum scope
        varchar description
        text system_prompt
        decimal temperature
        decimal top_p
        int max_tokens
        int created_by FK
        datetime created_at
    }
```

### 4.2 级联与保留策略

| 主表 | 从表/存储 | 关系 | 删除策略 |
| --- | --- | --- | --- |
| `users` | `documents` | 一个用户可上传多个文档 | 用户删除后 `uploaded_by` 置空，保留文档 |
| `users` | `conversations` | 一个用户拥有多个会话 | 用户删除后级联删除会话 |
| `conversations` | `messages` | 一个会话包含多条消息 | 会话删除后级联删除消息 |
| `model_providers` | `model_configs` | 一个供应商提供多个模型 | 供应商删除后级联删除模型配置 |
| `model_configs` | `model_presets` | 一个模型可绑定多个预设 | 模型配置删除后级联删除预设 |
| `documents` | ChromaDB 分块 | 通过 `doc_id` 关联 | 文档删除时删除对应向量分块 |
| `documents` | Neo4j 实体 | 通过 `doc_id` 关联 | 文档删除时删除对应图谱实体和关系 |
| `documents` / `conversations` | `token_usage` | 通过 `source_type`、`source_id` 逻辑关联 | 独立保留，不随源数据级联删除 |

## 5. 物理表设计

### 5.1 `users` 用户表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 用户编号 |
| `username` | `VARCHAR(50)` | UNIQUE, NOT NULL |  | 登录名 |
| `password_hash` | `VARCHAR(255)` | NOT NULL |  | bcrypt 密码哈希 |
| `role` | `ENUM('admin','user')` | NOT NULL | `user` | 用户角色 |
| `status` | `ENUM('active','disabled')` | NOT NULL | `active` | 账号状态 |
| `created_at` | `DATETIME` | NOT NULL | `CURRENT_TIMESTAMP` | 创建时间 |

设计说明：

- `admin` 可访问工作台、知识库、图谱、用户管理、系统配置、模型管理等管理页面。
- `user` 可访问智能问答、个人历史、个人中心。
- 禁用用户不能正常登录或继续使用受保护接口。

### 5.2 `documents` 文档元数据表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 文档编号 |
| `filename` | `VARCHAR(255)` | NOT NULL |  | 原始文件名 |
| `file_type` | `ENUM('PDF','DOCX','TXT','MD','XLSX','XLS','CSV')` | NOT NULL |  | 文件类型 |
| `file_size` | `BIGINT` | NOT NULL |  | 文件大小，单位字节 |
| `file_path` | `VARCHAR(500)` | NOT NULL |  | 文件卷内路径 |
| `tag` | `VARCHAR(100)` |  | NULL | 分类标签 |
| `parse_status` | `ENUM('pending','parsing','completed','failed')` | NOT NULL | `pending` | 解析状态 |
| `version` | `INT` | NOT NULL | `1` | 文档版本号 |
| `uploaded_by` | `INT` | FK | NULL | 上传人，引用 `users.id` |
| `error_message` | `TEXT` |  | NULL | 解析失败原因 |
| `embedding_tokens` | `INT` |  | `0` | 向量化消耗 Token |
| `created_at` | `DATETIME` | NOT NULL | `CURRENT_TIMESTAMP` | 上传时间 |
| `updated_at` | `DATETIME` | ON UPDATE | NULL | 更新时间 |

索引：

| 索引名 | 字段 | 用途 |
| --- | --- | --- |
| `idx_documents_parse_status` | `parse_status` | 按解析状态筛选文档 |
| `idx_documents_tag` | `tag` | 按分类标签筛选 |
| `idx_documents_uploaded_by` | `uploaded_by` | 查询指定用户上传文档 |

### 5.3 `conversations` 会话表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 会话编号 |
| `user_id` | `INT` | FK, NOT NULL |  | 所属用户 |
| `title` | `VARCHAR(200)` | NOT NULL | `New Conversation` | 会话标题 |
| `created_at` | `DATETIME` | NOT NULL | `CURRENT_TIMESTAMP` | 创建时间 |
| `updated_at` | `DATETIME` | ON UPDATE | NULL | 更新时间 |

索引：

| 索引名 | 字段 | 用途 |
| --- | --- | --- |
| `idx_conversations_user_id` | `user_id` | 查询用户会话列表 |

### 5.4 `messages` 消息记录表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 消息编号 |
| `conversation_id` | `INT` | FK, NOT NULL |  | 所属会话 |
| `role` | `ENUM('user','bot')` | NOT NULL |  | 消息角色 |
| `content` | `TEXT` | NOT NULL |  | 消息正文 |
| `sources` | `JSON` |  | NULL | RAG 引用来源列表 |
| `kg_references` | `JSON` |  | NULL | 知识图谱引用实体和关系 |
| `model_name` | `VARCHAR(100)` |  | NULL | 回答使用的模型名 |
| `tokens_used` | `INT` |  | NULL | 本次回答消耗 Token |
| `created_at` | `DATETIME` | NOT NULL | `CURRENT_TIMESTAMP` | 创建时间 |

`sources` JSON 示例：

```json
[
  {
    "doc_name": "课程设计说明.pdf",
    "chunk_index": 3,
    "excerpt": "系统采用 RAG 架构...",
    "similarity": 0.8421
  }
]
```

`kg_references` JSON 示例：

```json
{
  "entities": [{"id": "RAG", "name": "RAG", "type": "概念"}],
  "edges": [{"source": "RAG", "target": "向量检索", "rel": "包含"}]
}
```

索引：

| 索引名 | 字段 | 用途 |
| --- | --- | --- |
| `idx_messages_conversation_id` | `conversation_id` | 查询会话消息和历史上下文 |

### 5.5 `system_config` 系统配置表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 配置编号 |
| `config_key` | `VARCHAR(100)` | UNIQUE, NOT NULL |  | 配置键 |
| `config_value` | `TEXT` | NOT NULL |  | 配置值 |
| `description` | `VARCHAR(255)` |  | NULL | 配置说明 |
| `updated_at` | `DATETIME` | ON UPDATE | NULL | 更新时间 |

最终版预置配置：

| 配置键 | 默认值 | 用途 |
| --- | --- | --- |
| `temperature` | `0.7` | LLM 温度参数 |
| `top_p` | `0.9` | LLM Top-P 参数 |
| `max_tokens` | `2048` | LLM 最大输出 Token |
| `top_k` | `5` | 向量检索返回数量 |
| `similarity_threshold` | `0.6` | RAG 相似度阈值 |
| `chunk_size` | `512` | 文本分块大小 |
| `chunk_overlap` | `128` | 文本分块重叠长度 |
| `kg_enabled` | `true` | 是否启用知识图谱增强 |
| `history_rounds` | `5` | 问答携带历史轮数 |

说明：文档解析服务中还支持读取 `kg_chunk_size`、`kg_overlap`、`kg_min_chars` 等知识图谱抽取参数；如果数据库未配置，则后端使用代码默认值。

### 5.6 `model_providers` 模型供应商表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 供应商编号 |
| `provider_name` | `VARCHAR(50)` | UNIQUE, NOT NULL |  | 供应商名称 |
| `api_base_url` | `VARCHAR(255)` | NOT NULL |  | OpenAI 兼容接口地址 |
| `api_key_encrypted` | `TEXT` | NOT NULL |  | 加密后的 API Key |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | 是否启用 |
| `created_at` | `DATETIME` | NOT NULL | `CURRENT_TIMESTAMP` | 创建时间 |

设计说明：

- API Key 不明文入库，由 `app/utils/encryption.py` 加密后保存。
- 供应商可通过管理端新增、编辑、删除、连通性测试。

### 5.7 `model_configs` 模型配置表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 模型配置编号 |
| `provider_id` | `INT` | FK, NOT NULL |  | 所属供应商 |
| `model_name` | `VARCHAR(100)` | NOT NULL |  | 模型名称 |
| `model_type` | `ENUM('chat','embedding')` | NOT NULL |  | 模型类型 |
| `system_prompt` | `TEXT` |  | NULL | 系统提示词模板 |
| `embedding_dimension` | `INT` |  | NULL | 向量维度 |
| `is_default` | `BOOLEAN` | NOT NULL | FALSE | 是否默认模型 |
| `is_active` | `BOOLEAN` | NOT NULL | TRUE | 是否启用 |
| `created_at` | `DATETIME` | NOT NULL | `CURRENT_TIMESTAMP` | 创建时间 |

约束：

| 约束名 | 字段 | 说明 |
| --- | --- | --- |
| `uk_provider_model` | `provider_id`, `model_name` | 同一供应商下模型名唯一 |

### 5.8 `model_presets` 模型预设表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 预设编号 |
| `name` | `VARCHAR(100)` | NOT NULL |  | 预设名称 |
| `model_config_id` | `INT` | FK, NOT NULL |  | 绑定模型 |
| `scope` | `ENUM('global','personal')` | NOT NULL | `personal` | 作用范围 |
| `description` | `VARCHAR(255)` |  | NULL | 预设说明 |
| `system_prompt` | `TEXT` |  | NULL | 预设提示词 |
| `temperature` | `DECIMAL(3,2)` |  | `0.70` | 温度参数 |
| `top_p` | `DECIMAL(3,2)` |  | `0.90` | Top-P 参数 |
| `max_tokens` | `INT` |  | `2048` | 最大输出 Token |
| `created_by` | `INT` | FK | NULL | 创建人 |
| `created_at` | `DATETIME` | NOT NULL | `CURRENT_TIMESTAMP` | 创建时间 |

### 5.9 `token_usage` Token 使用记录表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `id` | `INT` | PK, AUTO_INCREMENT |  | 记录编号 |
| `model_name` | `VARCHAR(100)` | NOT NULL |  | 模型名称 |
| `model_type` | `ENUM('chat','embedding')` | NOT NULL |  | 消耗类型 |
| `tokens_used` | `INT` | NOT NULL | `0` | 消耗 Token 数 |
| `source_type` | `ENUM('qa','document')` | NOT NULL |  | 来源类型 |
| `source_id` | `INT` |  | NULL | 来源编号，会话 ID 或文档 ID |
| `source_name` | `VARCHAR(255)` |  | NULL | 来源名称，问题摘要或文件名 |
| `created_at` | `DATETIME` | NOT NULL | `CURRENT_TIMESTAMP` | 记录时间 |

索引：

| 索引名 | 字段 | 用途 |
| --- | --- | --- |
| `idx_token_usage_model` | `model_name`, `model_type` | 按模型统计消耗 |
| `idx_token_usage_source` | `source_type`, `source_id` | 按问答或文档追踪来源 |

设计说明：

- 问答完成后，`qa_service.rag_pipeline` 写入 `source_type='qa'` 的 Chat Token 记录。
- 文档解析向量化后，`document_service.parse_document` 写入 `source_type='document'` 的 Embedding Token 记录。
- 该表独立保存统计数据，不设置外键级联，避免源会话或文档删除后统计口径丢失。

## 6. 辅助存储设计

### 6.1 ChromaDB Collection：`kb_chunks`

| 项 | 说明 |
| --- | --- |
| Collection 名称 | `kb_chunks` |
| 主键 ID | `doc{doc_id}_chunk{chunk_index}` |
| 文档内容 | 清洗后的文本分块 |
| Embedding | 默认 Embedding 模型生成的向量 |
| Metadata | `doc_id`、`filename`、`chunk_index` |

写入流程：

1. 管理员上传文档，MySQL 写入 `documents` 记录，状态为 `pending`。
2. 后台解析任务读取原文件，抽取文本并清洗。
3. `chunk_text` 按默认 512 字符、128 字符重叠分块。
4. Embedding 模型生成向量。
5. ChromaDB 批量写入分块、向量和元数据。
6. MySQL 更新 `documents.parse_status='completed'`，并记录 `embedding_tokens`。

检索流程：

1. 用户提问后，后端生成问题向量。
2. ChromaDB 按向量相似度返回 Top-K 分块。
3. 后端按 `similarity_threshold` 过滤低相似度分块。
4. 命中的分块作为 LLM 上下文，并写入 `messages.sources`。

### 6.2 Neo4j 图 Schema

节点：`Entity`

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| `name` | String | 实体名，作为主要匹配标识 |
| `type` | String | 实体类型，默认“概念” |
| `description` | String | 实体描述 |
| `doc_id` | Integer | 来源文档 ID |

关系：

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| 关系类型 | Dynamic | 由 LLM 抽取出的关系名称 |
| `source` | Entity | 起点实体 |
| `target` | Entity | 终点实体 |

图谱用途：

- 管理端图谱总览、实体搜索、类型筛选、邻居查询。
- 支持手动新增实体、关系、编辑实体、删除实体和关系。
- RAG 问答中根据问题词匹配图谱子图，将相关关系作为补充上下文。
- 删除文档时按 `doc_id` 清理对应图谱数据。

### 6.3 Redis 数据设计

当前最终实现中 Redis 已作为基础服务接入 Docker Compose，主要承担缓存和异步扩展支撑。后续可按以下命名规范扩展：

| Key 模式 | 数据类型 | 用途 | 建议 TTL |
| --- | --- | --- | --- |
| `rag:session:{user_id}` | String/Hash | 用户会话缓存 | 与 JWT 过期时间一致 |
| `rag:task:parse:{doc_id}` | Hash | 文档解析任务状态 | 24 小时 |
| `rag:task:rebuild:{task_id}` | Hash | 向量重建任务状态 | 24 小时 |
| `rag:rate:{user_id}:{minute}` | String | 接口限流计数 | 60 秒 |

### 6.4 文件存储

上传文件保存到后端容器的 `/app/data/files`，通过 Docker volume `file_store` 持久化。MySQL `documents.file_path` 保存真实路径，文档预览、重解析和删除操作均通过该路径访问文件。

支持文件类型：

| 类型 | 扩展名 | 解析方式 |
| --- | --- | --- |
| PDF | `.pdf` | `pdfplumber` 抽取页面文本 |
| DOCX | `.docx` | `python-docx` 抽取段落文本 |
| TXT | `.txt` | UTF-8 文本读取 |
| MD | `.md` | UTF-8 文本读取 |
| XLSX/XLS | `.xlsx` / `.xls` | `openpyxl` 按工作表逐行读取 |
| CSV | `.csv` | `csv` 模块逐行读取 |

## 7. 标准编码

| 编码项 | 取值 | 说明 |
| --- | --- | --- |
| 用户角色 | `admin` | 管理员 |
| 用户角色 | `user` | 普通用户 |
| 用户状态 | `active` | 正常 |
| 用户状态 | `disabled` | 禁用 |
| 文档状态 | `pending` | 已上传，等待解析 |
| 文档状态 | `parsing` | 正在解析 |
| 文档状态 | `completed` | 解析完成，可参与问答 |
| 文档状态 | `failed` | 解析失败 |
| 消息角色 | `user` | 用户提问 |
| 消息角色 | `bot` | 模型回答 |
| 模型类型 | `chat` | 对话生成模型 |
| 模型类型 | `embedding` | 向量模型 |
| 预设范围 | `global` | 全局预设 |
| 预设范围 | `personal` | 个人预设 |
| Token 来源 | `qa` | 问答流程 |
| Token 来源 | `document` | 文档向量化流程 |

## 8. 预置数据

### 8.1 默认管理员

| 用户名 | 默认密码 | 角色 | 说明 |
| --- | --- | --- | --- |
| `admin` | `admin123` | `admin` | 初始化系统管理账号 |

密码在数据库中保存为 bcrypt 哈希，不保存明文。

### 8.2 默认模型供应商和模型

| 类型 | 名称 | 默认 | 说明 |
| --- | --- | --- | --- |
| 供应商 | `DeepSeek` | 是 | OpenAI 兼容接口地址 `https://api.deepseek.com/v1` |
| Chat 模型 | `deepseek-chat` | 是 | 普通问答模型 |
| Chat 模型 | `deepseek-reasoner` | 否 | 推理问答模型 |
| Embedding 模型 | `deepseek-embedding` | 是 | 文档和问题向量化模型，默认维度 1536 |

## 9. 数据访问层对应关系

| 数据对象 | SQLAlchemy 模型 | DAO 文件 | 主要服务 |
| --- | --- | --- | --- |
| 用户 | `models/user.py` | `dao/user_dao.py` | `services/user_service.py` |
| 文档 | `models/document.py` | `dao/document_dao.py`、`dao/file_store.py` | `services/document_service.py` |
| 会话 | `models/conversation.py` | `dao/conversation_dao.py` | `services/qa_service.py` |
| 消息 | `models/message.py` | `dao/message_dao.py` | `services/qa_service.py`、`services/history_service.py` |
| 系统配置 | `models/system_config.py` | `dao/config_dao.py` | `services/config_service.py` |
| 模型供应商 | `models/model_provider.py` | `dao/model_dao.py` | `services/model_service.py` |
| 模型配置 | `models/model_config.py` | `dao/model_dao.py` | `services/model_service.py`、`services/qa_service.py` |
| 模型预设 | `models/model_preset.py` | `dao/model_dao.py` | `services/model_service.py` |
| Token 统计 | `models/token_usage.py` | `dao/token_usage_dao.py` | `services/qa_service.py`、`services/document_service.py` |
| 向量库 | ChromaDB Collection | `dao/chroma_repo.py` | `services/document_service.py`、`services/qa_service.py` |
| 图数据库 | Neo4j `Entity` | `dao/neo4j_repo.py` | `services/kg_service.py`、`services/document_service.py` |

## 10. 完整 DDL

```sql
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

USE rag_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','user') NOT NULL DEFAULT 'user',
    status ENUM('active','disabled') NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type ENUM('PDF','DOCX','TXT','MD','XLSX','XLS','CSV') NOT NULL,
    file_size BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    tag VARCHAR(100),
    parse_status ENUM('pending','parsing','completed','failed') NOT NULL DEFAULT 'pending',
    version INT NOT NULL DEFAULT 1,
    uploaded_by INT,
    error_message TEXT,
    embedding_tokens INT DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_documents_parse_status ON documents(parse_status);
CREATE INDEX idx_documents_tag ON documents(tag);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);

CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL DEFAULT 'New Conversation',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_conversations_user_id ON conversations(user_id);

CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    role ENUM('user','bot') NOT NULL,
    content TEXT NOT NULL,
    sources JSON,
    kg_references JSON,
    model_name VARCHAR(100),
    tokens_used INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

CREATE TABLE IF NOT EXISTS system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description VARCHAR(255),
    updated_at DATETIME DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS model_providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider_name VARCHAR(50) UNIQUE NOT NULL,
    api_base_url VARCHAR(255) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS model_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider_id INT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_type ENUM('chat','embedding') NOT NULL,
    system_prompt TEXT,
    embedding_dimension INT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES model_providers(id) ON DELETE CASCADE,
    UNIQUE KEY uk_provider_model (provider_id, model_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS model_presets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model_config_id INT NOT NULL,
    scope ENUM('global','personal') NOT NULL DEFAULT 'personal',
    description VARCHAR(255),
    system_prompt TEXT,
    temperature DECIMAL(3,2) DEFAULT 0.70,
    top_p DECIMAL(3,2) DEFAULT 0.90,
    max_tokens INT DEFAULT 2048,
    created_by INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_config_id) REFERENCES model_configs(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS token_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type ENUM('chat','embedding') NOT NULL,
    tokens_used INT NOT NULL DEFAULT 0,
    source_type ENUM('qa','document') NOT NULL,
    source_id INT,
    source_name VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_token_usage_model ON token_usage(model_name, model_type);
CREATE INDEX idx_token_usage_source ON token_usage(source_type, source_id);
```

## 11. 初始化与验证

### 11.1 初始化方式

MySQL 容器首次启动时自动执行：

```bash
docker compose up -d rag-mysql
```

初始化脚本路径：

```text
docker/mysql/init.sql
```

### 11.2 结构验证 SQL

```sql
SHOW TABLES;
SHOW CREATE TABLE users;
SHOW CREATE TABLE documents;
SHOW CREATE TABLE token_usage;
SELECT config_key, config_value FROM system_config;
SELECT provider_name, api_base_url FROM model_providers;
SELECT model_name, model_type, is_default FROM model_configs;
```

### 11.3 统计验证 SQL

```sql
SELECT parse_status, COUNT(*) AS total
FROM documents
GROUP BY parse_status;

SELECT model_name, model_type, SUM(tokens_used) AS total_tokens
FROM token_usage
GROUP BY model_name, model_type;

SELECT c.user_id, COUNT(m.id) AS message_count
FROM conversations c
LEFT JOIN messages m ON m.conversation_id = c.id
GROUP BY c.user_id;
```

## 12. 备份与恢复

### 12.1 MySQL

```bash
docker exec rag-mysql mysqldump -u root -p rag_db > rag_db_backup.sql
docker exec -i rag-mysql mysql -u root -p rag_db < rag_db_backup.sql
```

### 12.2 ChromaDB

```bash
docker cp rag-chromadb:/chroma/chroma ./chroma_backup
```

### 12.3 Neo4j

```bash
docker cp rag-neo4j:/data ./neo4j_backup
```

### 12.4 上传文件

```bash
docker cp rag-backend:/app/data/files ./file_store_backup
```

## 13. 安全设计

| 安全点 | 设计 |
| --- | --- |
| 密码保存 | 使用 bcrypt 哈希，不保存明文密码 |
| API Key 保存 | 使用 AES 加密后写入 `model_providers.api_key_encrypted` |
| 数据库访问 | 后端使用独立数据库用户 `rag_user` |
| 角色权限 | 后端接口通过 `require_admin` 和 `get_current_user` 控制 |
| SQL 注入防护 | 使用 SQLAlchemy 参数化查询 |
| 文件路径 | 文件路径由后端保存逻辑生成，不直接信任用户输入路径 |
| 统计留存 | `token_usage` 不级联删除，保证成本统计口径稳定 |

## 14. 最终说明

本数据库说明书对应课程设计最终实现，核心数据库对象以 `docker/mysql/init.sql` 为准，代码访问路径以 `docker/backend/app/models` 和 `docker/backend/app/dao` 为准。与早期设计相比，最终版重点补充了 `token_usage` 表、Excel/CSV 文档类型、向量库和图数据库实际落地方式，以及模型使用统计的数据设计。
