from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.user import User


async def get_admin_history(db: AsyncSession, page: int = 1, size: int = 20, keyword: str = "", user_id: int = None) -> dict:
    query = select(Message, Conversation, User).join(
        Conversation, Message.conversation_id == Conversation.id
    ).join(User, Conversation.user_id == User.id).where(Message.role == "user")

    count_q = select(func.count()).select_from(Message).join(
        Conversation, Message.conversation_id == Conversation.id
    ).join(User, Conversation.user_id == User.id).where(Message.role == "user")

    if keyword:
        query = query.where(Message.content.contains(keyword))
        count_q = count_q.where(Message.content.contains(keyword))
    if user_id:
        query = query.where(Conversation.user_id == user_id)
        count_q = count_q.where(Conversation.user_id == user_id)

    total = (await db.execute(count_q)).scalar()
    query = query.order_by(Message.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for msg, conv, user in rows:
        items.append({
            "id": msg.id,
            "question": msg.content[:200],
            "username": user.username,
            "conversation_id": conv.id,
            "created_at": str(msg.created_at),
        })
    return {"items": items, "total": total}


async def get_my_history(db: AsyncSession, user_id: int, page: int = 1, size: int = 20) -> dict:
    query = select(Message).join(
        Conversation, Message.conversation_id == Conversation.id
    ).where(Conversation.user_id == user_id, Message.role == "user")

    count_q = select(func.count()).select_from(Message).join(
        Conversation, Message.conversation_id == Conversation.id
    ).where(Conversation.user_id == user_id, Message.role == "user")

    total = (await db.execute(count_q)).scalar()
    query = query.order_by(Message.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    messages = result.scalars().all()

    items = [{"id": m.id, "question": m.content[:200], "created_at": str(m.created_at)} for m in messages]
    return {"items": items, "total": total}


async def get_stats(db: AsyncSession) -> dict:
    total_messages = (await db.execute(select(func.count()).select_from(Message).where(Message.role == "user"))).scalar()
    total_conversations = (await db.execute(select(func.count()).select_from(Conversation))).scalar()
    return {"total_messages": total_messages, "total_conversations": total_conversations}
