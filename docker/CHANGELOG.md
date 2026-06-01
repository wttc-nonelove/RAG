# RAG 智能知识库问答系统 - 完整更新日志

---

## v2.1.0 - 功能增强与多供应商支持 (2026-05-29)

### 新增功能

#### 1. 多文件批量上传
- 知识库管理页面支持同时选择多个文件上传
- 上传队列实时显示每个文件的状态（待解析 / 上传中 / 已完成 / 失败）
- 上传完成后自动刷新文档列表

#### 2. 知识图谱可视化编辑
- 基于 ECharts 实现力导向图谱可视化，支持拖拽、缩放、平移
- 新增「添加实体」功能：输入名称、选择类型（7种）、填写描述
- 新增「添加关系」功能：从已有节点中选择源实体和目标实体，填写关系标签
- 点击节点弹出操作面板，支持删除实体及其关联关系
- 顶部显示实体类型颜色图例，节点按类型着色
- 支持关键词搜索图谱子图

#### 3. 模型管理全面优化
- **供应商管理**：新增编辑功能，可修改名称、API 地址、API Key
- **对话模型**：新增「添加模型」配置表单，支持选择供应商、设置系统提示词、设为默认模型
- **Embedding 模型**：同上，额外支持设置 Embedding 维度参数
- **Prompt 模板**：从只读改为可编辑，每个模型独立保存
- 所有操作提供 `el-message` 反馈提示

#### 4. 多供应商 LLM/Embedding 支持
- 后端架构重构，LLM 和 Embedding 均支持从数据库动态解析供应商配置
- 对话模型：支持接入任意 OpenAI 兼容 API（DeepSeek、通义千问、OpenAI 等）
- Embedding 模型：优先调用远程 Embedding API，失败时自动回退到本地哈希向量
- QA 接口不传 `model_name` 时自动使用数据库中标记为默认的模型
- 文档解析和向量检索均基于数据库配置的 Embedding 模型

#### 5. 问答历史详情交互
- 点击「详情」按钮打开对话详情弹窗
- 以聊天气泡样式展示完整的用户-助手对话记录
- 支持 Markdown 渲染、引用来源展示
- 历史列表支持分页

#### 6. 新建对话自动跳转
- 点击「新建对话」后自动创建并切换到新会话
- 用户无需二次点击即可直接开始提问

### Bug 修复 (v2.1.0)

- 修复知识图谱页面空白问题（原为占位页面，未接入 ECharts）
- 修复文档解析后台任务复用已关闭的数据库会话导致解析失败
- 修复 KG 实体提取 Prompt 中 JSON 花括号转义错误
- 修复 KG 提取 JSON 被截断时的解析失败（增加尾逗号修复）
- 修复用户创建接口缺少 `db.commit()` 导致数据未持久化
- 修复 QA 首次对话返回缺少 `conversation_id` 导致前端状态异常
- 修复模型连通性测试在 API Key 未配置时的解密异常
- 修复 CORS 仅允许 localhost 导致非本地访问被拦截

### 架构变更 (v2.1.0)

| 文件 | 变更说明 |
|------|----------|
| `backend/app/utils/llm_client.py` | 新增 `chat_with_provider()`、`chat_from_db()`，支持数据库驱动的多供应商调用 |
| `backend/app/utils/embedding.py` | 新增 `encode_with_provider()`、`encode_from_db()`、`encode_batch_from_db()`，支持远程 API + 本地回退 |
| `backend/app/models/model_config.py` | 新增 `provider` relationship，自动关联供应商信息 |
| `backend/app/dao/model_dao.py` | 新增 `get_default_config()`、`get_config_with_provider()` |
| `backend/app/services/qa_service.py` | Embedding 和 LLM 均改用数据库解析的供应商配置 |
| `backend/app/services/document_service.py` | 文档解析 Embedding 改用 `encode_batch_from_db()` |
| `backend/app/routers/qa.py` | 未指定模型时从数据库解析默认模型 |
| `backend/app/routers/models.py` | 新增 `PUT /configs/{id}` 模型配置编辑接口 |
| `backend/app/services/document_service.py` | `parse_document()` 改为独立会话，解决后台任务生命周期问题 |
| `backend/app/utils/kg_extractor.py` | 修复 Prompt 格式化、增加 JSON 修复逻辑 |
| `frontend/src/views/admin/Graph.vue` | 完整重写，ECharts 图谱可视化 + 实体/关系 CRUD |
| `frontend/src/views/admin/Knowledge.vue` | 多文件上传 + 逐文件状态追踪 |
| `frontend/src/views/admin/Model.vue` | 完整重写，供应商/模型/Prompt 全功能管理 |
| `frontend/src/views/admin/History.vue` | 完整重写，分页 + 对话详情弹窗 |
| `frontend/src/stores/qa.js` | `newConversation()` 自动选中新会话，移除硬编码模型名 |

---

## v2.0.1 - Bug 修复与知识图谱可视化 (2026-05-29)

### Bug 修复

#### 模型管理测试失败
- **现象**：点击「测试」显示「测试失败、服务器错误」
- **原因**：`init.sql` 中 API Key 为占位符 `<ENCRYPTED_API_KEY>`，AES-256-CBC 解密时 padding 校验失败
- **修复**：生成正确的加密值写入 `init.sql`，`model_service.py` 增加解密异常的优雅处理

#### 文档解析状态 failed
- **现象**：文件上传成功但状态显示 `failed`
- **原因**：`parse_document(db, doc_id)` 的后台任务复用了请求生命周期的 DB 会话，响应发送后会话已关闭
- **修复**：`parse_document(doc_id)` 改为通过 `async_session()` 创建独立会话

#### 知识图谱页面空白
- **现象**：页面无任何图谱展示
- **原因**：`Graph.vue` 为占位组件，仅有标题无 ECharts 代码
- **修复**：完整重写为 ECharts 力导向图，接入 `/api/v1/graph/overview` 和 `/api/v1/graph/search`

#### 新用户创建不成功
- **现象**：创建用户后列表无新增
- **原因**：`users.py` 路由调用 `create_user` 后缺少 `await db.commit()`
- **修复**：添加 `await db.commit()`

#### KG 实体提取失败
- **现象**：文档上传后 Neo4j 中无实体
- **原因 1**：`EXTRACT_PROMPT` 使用 `.format()` 时，JSON 示例中的 `{}` 被当作占位符导致 `KeyError`
- **原因 2**：长文档 LLM 返回 JSON 被截断，尾部缺少 `}`
- **修复**：`{` → `{{`、`}` → `}}` 转义；减少输入文本至 1500 字符；增加 `max_tokens=2048`；添加尾逗号修复正则

#### QA 首次对话状态异常
- **现象**：首次提问后前端不显示回答
- **原因**：API 返回 `message_id` 而非 `conversation_id`，前端无法关联会话
- **修复**：响应中补充 `conversation_id` 字段

#### CORS 跨域拦截
- **现象**：非 localhost 访问时请求被拦截
- **原因**：`allow_origins` 仅配置 `["http://localhost:5173"]`
- **修复**：改为 `["*"]`

### 新增功能

#### 知识图谱 ECharts 可视化
- ECharts 力导向图布局，74 节点 / 83 边
- 7 种实体类型颜色区分（人物/组织/地点/概念/技术/产品/事件）
- 支持搜索、缩放、拖拽、节点高亮关联

#### 前端 API 全面对接
- Dashboard、Users、Model、Config、MyHistory 等页面从硬编码/空数据改为真实 API 调用

---

## v2.0.0 - 系统初始构建与部署 (2026-05-29)

### 项目概述

基于 RAG 架构的私有知识库智能问答系统，支持文档上传、向量检索、知识图谱、多轮对话。

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + ECharts + Pinia + Vite |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy (async) |
| 数据库 | MySQL 8.0 + ChromaDB + Neo4j 4.4.16 + Redis 7 |
| LLM | DeepSeek API (OpenAI SDK 兼容) |
| 部署 | Docker Compose (6 服务) |

### 核心功能

#### 用户端
- **智能问答**：基于 RAG 检索增强生成，支持多轮对话、历史记录、流式显示
- **模型选择**：下拉切换对话模型（deepseek-chat / deepseek-reasoner 等）
- **会话管理**：新建、切换、删除对话

#### 管理端
- **仪表盘**：系统概览（文档数、用户数、问答数、图谱规模）
- **知识库管理**：文档上传（PDF/DOCX/TXT）、解析状态追踪、预览、删除、重新解析
- **知识图谱**：ECharts 可视化、实体/关系增删查
- **模型管理**：供应商 CRUD、模型配置、Prompt 模板、连通性测试
- **问答历史**：全量问答记录、分页、对话详情查看
- **用户管理**：用户增删改查、角色分配
- **系统配置**：top_k、相似度阈值、温度、历史轮数等参数调整

#### 后端能力
- JWT 认证（HS256，24h 有效期）+ bcrypt 密码加密
- AES-256-CBC 加密存储 API Key
- 后台异步文档解析（FastAPI BackgroundTasks）
- ChromaDB 向量检索 + Neo4j 知识图谱查询
- LLM 实体/关系自动提取

### 部署架构

```
docker-compose.yml
├── rag-frontend    (Vue 3, :5173)
├── rag-backend     (FastAPI, :8000)
├── rag-mysql       (MySQL 8.0, :3307)
├── rag-chromadb    (ChromaDB, :8001)
├── rag-neo4j       (Neo4j 4.4, :7474/:7687)
└── rag-redis       (Redis 7, :6379)
```

### 文件规模

- 后端：Python 源码约 40 文件（routers / services / dao / models / utils）
- 前端：Vue 源码约 25 文件（views / components / api / stores / router）
- 配置：Dockerfile x2、docker-compose.yml、init.sql、.env、requirements.txt
- 总计约 95 文件

---

## 使用说明

### 添加通义千问 Embedding 模型

1. 进入「模型管理」→「模型供应商」→「添加供应商」
2. 填写：名称 `通义千问`，API 地址 `https://dashscope.aliyuncs.com/compatible-mode/v1`，API Key
3. 切换到「Embedding 模型」标签页 →「添加模型」
4. 选择供应商「通义千问」，模型名 `text-embedding-v1`，维度 `1536`，开启「设为默认」
5. 在知识库管理中对已有文档点击「重新解析」以更新向量数据

### 切换对话模型

1. 进入「模型管理」→「对话模型」→「添加模型」
2. 配置新模型后点击「设为默认」
3. QA 页面模型下拉框将自动显示所有已启用的对话模型

### 修改 DeepSeek API Key

1. 进入「模型管理」→「模型供应商」→ DeepSeek 行点击「编辑」
2. 填入新的 API Key，保存
3. 点击「测试」验证连通性
