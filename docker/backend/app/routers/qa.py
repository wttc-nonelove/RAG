from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.dao import conversation_dao, message_dao
from app.services import qa_service, model_service

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


class AskRequest(BaseModel):
    conversation_id: Optional[int] = None
    question: str
    model_name: Optional[str] = None


class ConvRequest(BaseModel):
    title: str = "New Conversation"


@router.post("/ask")
async def ask_question(req: AskRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv_id = req.conversation_id
    if not conv_id:
        conv = await conversation_dao.create(db, user.id, req.question[:50])
        await db.commit()
        conv_id = conv.id

    conv = await conversation_dao.get_by_id(db, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")

    # 自动更新对话标题（如果还是默认标题）
    if conv.title == "New Conversation":
        new_title = req.question[:50]
        await conversation_dao.update_title(db, conv_id, new_title)
        await db.commit()

    # Resolve model_name: use provided, or default from DB
    model_name = req.model_name
    if not model_name:
        from app.dao import model_dao
        default_config = await model_dao.get_default_config(db, "chat")
        model_name = default_config.model_name if default_config else "deepseek-chat"

    result = await qa_service.rag_pipeline(db, conv_id, req.question, model_name, user.id)
    result["conversation_id"] = conv_id
    return ok(result)


@router.get("/conversations")
async def list_conversations(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    convs = await conversation_dao.get_by_user(db, user.id)
    return ok([{"id": c.id, "title": c.title, "created_at": str(c.created_at)} for c in convs])


@router.post("/conversations")
async def create_conversation(req: ConvRequest = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    title = req.title if req else "New Conversation"
    conv = await conversation_dao.create(db, user.id, title)
    await db.commit()
    return ok({"id": conv.id, "title": conv.title})


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv = await conversation_dao.get_by_id(db, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    await conversation_dao.delete_conv(db, conv_id)
    await db.commit()
    return ok(message="会话删除成功")


@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv = await conversation_dao.get_by_id(db, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    messages = await message_dao.get_by_conversation(db, conv_id)
    return ok([
        {
            "id": m.id, "role": m.role, "content": m.content,
            "sources": m.sources, "kg_references": m.kg_references,
            "model_name": m.model_name,
            "tokens_used": m.tokens_used, "created_at": str(m.created_at),
        }
        for m in messages
    ])


@router.get("/models")
async def get_models(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    models = await model_service.get_enabled_chat_models(db)
    return ok(models)
