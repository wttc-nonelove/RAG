from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.token_usage import TokenUsage
from typing import List


async def create(db: AsyncSession, model_name: str, model_type: str, tokens_used: int,
                 source_type: str, source_id: int = None, source_name: str = None) -> TokenUsage:
    usage = TokenUsage(
        model_name=model_name,
        model_type=model_type,
        tokens_used=tokens_used,
        source_type=source_type,
        source_id=source_id,
        source_name=source_name,
    )
    db.add(usage)
    await db.flush()
    return usage


async def get_usage_summary(db: AsyncSession) -> dict:
    # 总消耗
    total_result = await db.execute(
        select(func.sum(TokenUsage.tokens_used))
    )
    total_tokens = total_result.scalar() or 0

    # 按类型统计
    chat_result = await db.execute(
        select(func.sum(TokenUsage.tokens_used))
        .where(TokenUsage.model_type == "chat")
    )
    chat_tokens = chat_result.scalar() or 0

    embed_result = await db.execute(
        select(func.sum(TokenUsage.tokens_used))
        .where(TokenUsage.model_type == "embedding")
    )
    embedding_tokens = embed_result.scalar() or 0

    # 按模型统计
    model_result = await db.execute(
        select(
            TokenUsage.model_name,
            TokenUsage.model_type,
            func.sum(TokenUsage.tokens_used).label("total_tokens"),
            func.count().label("count"),
        )
        .group_by(TokenUsage.model_name, TokenUsage.model_type)
    )
    by_model = [
        {
            "model_name": r[0],
            "model_type": r[1],
            "total_tokens": r[2] or 0,
            "count": r[3],
        }
        for r in model_result.all()
    ]

    # 对话次数
    qa_count_result = await db.execute(
        select(func.count()).where(TokenUsage.source_type == "qa")
    )
    qa_count = qa_count_result.scalar() or 0

    return {
        "total_tokens": total_tokens,
        "chat_tokens": chat_tokens,
        "embedding_tokens": embedding_tokens,
        "qa_count": qa_count,
        "by_model": by_model,
    }
