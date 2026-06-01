from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, documents, qa, graph, users, history, dashboard, config, models

app = FastAPI(
    title="RAG 智能问答系统",
    version="1.0.0",
    description="基于检索增强生成架构的私有知识库智能问答系统",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["文档管理"])
app.include_router(qa.router, prefix="/api/v1/qa", tags=["智能问答"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["知识图谱"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(history.router, prefix="/api/v1/history", tags=["问答历史"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["工作台"])
app.include_router(config.router, prefix="/api/v1/config", tags=["系统配置"])
app.include_router(models.router, prefix="/api/v1/models", tags=["模型管理"])


@app.get("/health")
async def health():
    return {"status": "ok"}
