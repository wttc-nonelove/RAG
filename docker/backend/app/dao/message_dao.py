from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.message import Message
from typing import Optional, List


async def create(db: AsyncSession, conversation_id: int, role: str, content: str,
                 sources: list = None, model_name: str = None, tokens_used: int = None) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources,
        model_name=model_name,
        tokens_used=tokens_used,
    )
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return msg


async def get_by_conversation(db: AsyncSession, conversation_id: int) -> List[Message]:
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    return result.scalars().all()


async def get_recent_history(db: AsyncSession, conversation_id: int, rounds: int = 5) -> List[Message]:
    limit = rounds * 2
    result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(desc(Message.created_at)).limit(limit)
    )
    messages = result.scalars().all()
    return list(reversed(messages))


async def get_by_id(db: AsyncSession, message_id: int) -> Optional[Message]:
    result = await db.execute(select(Message).where(Message.id == message_id))
    return result.scalar_one_or_none()
