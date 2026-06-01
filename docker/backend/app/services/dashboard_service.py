from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.document import Document
from app.models.message import Message
from app.models.user import User
from app.models.conversation import Conversation
from app.dao import chroma_repo, neo4j_repo


async def get_stats(db: AsyncSession) -> dict:
    from datetime import datetime
    today = datetime.now().date()

    total_documents = (await db.execute(select(func.count()).select_from(Document))).scalar()
    total_questions = (await db.execute(select(func.count()).select_from(Message).where(Message.role == "user"))).scalar()
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
    total_chunks = 0
    try:
        total_chunks = chroma_repo.count()
    except Exception:
        pass

    # 解析成功率
    completed_docs = (await db.execute(
        select(func.count()).select_from(Document).where(Document.parse_status == "completed")
    )).scalar()
    parse_success_rate = round(completed_docs / total_documents * 100, 1) if total_documents > 0 else 0

    # 今日问答数
    today_questions = (await db.execute(
        select(func.count()).select_from(Message).where(
            func.date(Message.created_at) == today, Message.role == "user"
        )
    )).scalar()

    # 活跃用户数（近7天有问答的用户）
    from datetime import timedelta
    week_ago = today - timedelta(days=7)
    active_users = (await db.execute(
        select(func.count(func.distinct(Conversation.user_id))).where(
            Conversation.updated_at >= week_ago
        )
    )).scalar()

    # 文档类型分布
    type_result = await db.execute(
        select(Document.file_type, func.count()).group_by(Document.file_type)
    )
    type_counts = {row[0]: row[1] for row in type_result.all()}

    return {
        "total_documents": total_documents,
        "total_questions": total_questions,
        "total_users": total_users,
        "total_chunks": total_chunks,
        "parse_success_rate": parse_success_rate,
        "today_questions": today_questions,
        "active_users": active_users,
        "type_counts": type_counts,
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
