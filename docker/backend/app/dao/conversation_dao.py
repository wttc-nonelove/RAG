from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.conversation import Conversation
from typing import Optional, List


async def create(db: AsyncSession, user_id: int, title: str = "New Conversation") -> Conversation:
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    return conv


async def get_by_user(db: AsyncSession, user_id: int) -> List[Conversation]:
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


async def get_by_id(db: AsyncSession, conv_id: int) -> Optional[Conversation]:
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    return result.scalar_one_or_none()


async def delete_conv(db: AsyncSession, conv_id: int) -> None:
    conv = await get_by_id(db, conv_id)
    if conv:
        await db.delete(conv)


async def update_title(db: AsyncSession, conv_id: int, title: str) -> None:
    conv = await get_by_id(db, conv_id)
    if conv:
        conv.title = title
        await db.flush()
