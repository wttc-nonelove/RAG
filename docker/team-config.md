# RAG 智能问答系统 — 开发团队配置

## 团队架构

```
                    ┌─────────────────┐
                    │   team-lead     │
                    │ (Agents         │
                    │  Orchestrator)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │ Phase1  │         │ Phase2-3│         │ Phase4-5│
   │ 基础框架 │         │ 核心功能 │         │ 管理功能 │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                    │                    │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │ Phase6  │         │  Deploy │         │  Test   │
   │ 联调验收 │         │  部署   │         │  测试   │
   └─────────┘         └─────────┘         └─────────┘
```

## 成员选择与职责

### 1. backend-architect — 后端架构师
- **来源**: `engineering-backend-architect.md`
- **职责**: FastAPI 后端全部开发
  - Phase 1: 项目脚手架、JWT 鉴权、数据库连接池
  - Phase 2: 文档管理模块 (M2)、ChromaDB 集成
  - Phase 3: RAG 核心链路 (M1)、LLM 调用封装
  - Phase 4: 知识图谱模块 (M3)、Neo4j 集成
  - Phase 5: 工作台/历史/配置/模型管理 (M4-M8)
- **并行**: 与 frontend-developer 并行开发

### 2. frontend-developer — 前端开发工程师
- **来源**: `engineering-frontend-developer.md`
- **职责**: Vue 3 + Element Plus 前端全部开发
  - Phase 1: 脚手架、路由守卫、Axios 拦截器、登录页
  - Phase 2: 知识库管理页面 (M2)
  - Phase 3: 智能问答页面 (M1)
  - Phase 4: 知识图谱可视化 (M3)
  - Phase 5: 工作台/历史/配置/模型管理页面 (M4-M8)
- **并行**: 与 backend-architect 并行开发

### 3. ai-engineer — AI/ML 工程师
- **来源**: `engineering-ai-engineer.md`
- **职责**: AI 核心能力开发
  - Phase 3: RAG Pipeline 实现（Embedding + ChromaDB 检索 + LLM 生成）
  - Phase 3: 多轮对话上下文管理、检索兜底逻辑
  - Phase 4: KG 信息抽取（LLM IE + spaCy NER）
  - Phase 5: Embedding 模型切换、向量重建任务
- **并行**: 与 backend-architect 协作，负责 AI 核心模块

### 4. database-optimizer — 数据库专家
- **来源**: `engineering-database-optimizer.md`
- **职责**: 多数据库架构设计与优化
  - Phase 1: MySQL 8 张表 DDL 设计、索引优化、预置数据
  - Phase 1: ChromaDB Collection 设计
  - Phase 1: Neo4j 约束与索引设计
  - Phase 5: 查询优化、慢查询分析
- **并行**: Phase 1 与 devops-automator 并行

### 5. devops-automator — DevOps 工程师
- **来源**: `engineering-devops-automator.md`
- **职责**: Docker 环境与部署流水线
  - Phase 1: docker-compose.yml（6 个服务容器）
  - Phase 1: Dockerfile（backend + frontend）
  - Phase 1: MySQL init.sql、环境变量配置
  - Phase 6: 全链路集成测试环境
- **并行**: 与所有开发角色并行，部署就绪即可验证

### 6. test-writer — 测试工程师
- **来源**: `test-writer.md`
- **职责**: 全链路测试
  - Phase 3+: 后端 API 单元测试
  - Phase 5+: 前端组件测试
  - Phase 6: 端到端集成测试、边界测试、性能验证
- **并行**: 跟随开发进度编写测试，Phase 6 集中执行

### 7. code-reviewer — 代码审查员
- **来源**: `code-reviewer.md`
- **职责**: 代码质量保障
  - 每个 Phase 完成后进行代码审查
  - 检查安全漏洞、边界条件、命名规范
  - 确保符合详细设计说明书的规范
- **并行**: 随开发进度持续审查

---

## 分阶段交付计划

### Phase 1: 基础框架搭建
| 任务 | 负责人 | 并行关系 |
|------|--------|----------|
| Docker 环境搭建 (docker-compose, Dockerfile) | devops-automator | 并行 |
| MySQL DDL + 预置数据 | database-optimizer | 并行 |
| 后端 FastAPI 脚手架 + JWT 鉴权 | backend-architect | 并行 |
| 前端 Vue 3 脚手架 + 路由守卫 | frontend-developer | 并行 |
| 代码审查 | code-reviewer | Phase 1 完成后 |

### Phase 2: 知识库管理
| 任务 | 负责人 | 并行关系 |
|------|--------|----------|
| 文档管理后端 (M2) | backend-architect | 并行 |
| 知识库管理前端 (M2) | frontend-developer | 并行 |
| ChromaDB 集成 + Embedding 封装 | ai-engineer | 并行 |
| 代码审查 | code-reviewer | Phase 2 完成后 |

### Phase 3: 智能问答核心
| 任务 | 负责人 | 并行关系 |
|------|--------|----------|
| RAG 问答后端 (M1) | backend-architect | 并行 |
| 智能问答前端 (M1) | frontend-developer | 并行 |
| RAG Pipeline + LLM 调用 | ai-engineer | 并行 |
| API 单元测试 | test-writer | 跟随 |
| 代码审查 | code-reviewer | Phase 3 完成后 |

### Phase 4: 知识图谱
| 任务 | 负责人 | 并行关系 |
|------|--------|----------|
| KG 后端管理 (M3) | backend-architect | 并行 |
| 图谱可视化前端 (M3) | frontend-developer | 并行 |
| KG 抽取引擎 (LLM IE + spaCy) | ai-engineer | 并行 |
| 代码审查 | code-reviewer | Phase 4 完成后 |

### Phase 5: 管理功能完善
| 任务 | 负责人 | 并行关系 |
|------|--------|----------|
| 用户管理/工作台/历史/配置后端 (M4-M8) | backend-architect | 并行 |
| 对应前端页面 (M4-M8) | frontend-developer | 并行 |
| Embedding 切换 + 向量重建 | ai-engineer | 并行 |
| 查询优化 | database-optimizer | 并行 |
| 代码审查 | code-reviewer | Phase 5 完成后 |

### Phase 6: 联调验收
| 任务 | 负责人 | 并行关系 |
|------|--------|----------|
| 全链路集成测试 | test-writer | 并行 |
| Docker 环境验证 | devops-automator | 并行 |
| 性能验证 | database-optimizer | 并行 |
| 最终代码审查 | code-reviewer | 收尾 |

---

## 协作原则

1. **分阶段交付**: 每个 Phase 完成后进行代码审查和集成验证
2. **模块化协作**: backend-architect 和 frontend-developer 按模块并行开发
3. **全链路验证**: test-writer 跟随开发进度，Phase 6 集中端到端测试
4. **开发-部署并行**: devops-automator 提前搭建 Docker 环境，开发完成后直接部署验证
