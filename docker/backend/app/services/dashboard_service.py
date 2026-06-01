from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.document import Document
from app.models.message import Message
from app.models.user import User
from app.models.conversation import Conversation
from app.dao import chroma_repo, neo4j_repo


async def get_stats(db: AsyncSession) -> dict:
    total_documents = (await db.execute(select(func.count()).select_from(Document))).scalar()
    total_questions = (await db.execute(select(func.count()).select_from(Message).where(Message.role == "user"))).scalar()
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
    total_chunks = 0
    try:
        total_chunks = chroma_repo.count()
    except Exception:
        pass
    return {
        "total_documents": total_documents,
        "total_questions": total_questions,
        "total_users": total_users,
        "total_chunks": total_chunks,
    }


async def get_trends(db: AsyncSession, days: int = 7) -> list:
    from datetime import datetime, timedelta
    today = datetime.now().date()
    trends = []
    for i in range(days - 1, -1, -1):
        date = today - timedelta(days=i)
        count = (await db.execute(
            select(func.count()).select_from(Message).where(
                func.date(Message.created_at) == date, Message.role == "user"
            )
        )).scalar()
        trends.append({"date": str(date), "count": count})
    return trends


async def get_storage() -> dict:
    import os
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "files")
    doc_size = 0
    if os.path.exists(base):
        for f in os.listdir(base):
            doc_size += os.path.getsize(os.path.join(base, f))
    return {
        "total_mb": round(doc_size / 1024 / 1024, 2),
        "documents_mb": round(doc_size / 1024 / 1024, 2),
        "vectors_mb": 0,
    }


async def get_system_status() -> dict:
    from app.dao import chroma_repo, neo4j_repo
    mysql_ok = True
    redis_ok = True
    neo4j_ok = False
    chroma_ok = False
    try:
        neo4j_ok = neo4j_repo.health()
    except Exception:
        pass
    try:
        chroma_ok = chroma_repo.health()
    except Exception:
        pass
    return {
        "mysql": "ok" if mysql_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "neo4j": "ok" if neo4j_ok else "error",
        "chromadb": "ok" if chroma_ok else "error",
    }
