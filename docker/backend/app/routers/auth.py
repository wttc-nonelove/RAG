from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, ChangePasswordRequest, UserInfo
from app.services import user_service
from app.models.user import User

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await user_service.authenticate(db, req)
        return ok(result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await user_service.register(db, req)
        return ok(result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return ok(UserInfo(id=user.id, username=user.username, role=user.role, status=user.status).model_dump())


@router.put("/password")
async def change_password(req: ChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        await user_service.change_password(db, user, req)
        return ok(message="密码修改成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class UpdateUsernameRequest(BaseModel):
    username: str


@router.put("/username")
async def update_username(req: UpdateUsernameRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    # 检查用户名是否已存在
    existing = await db.execute(select(User).where(User.username == req.username, User.id != user.id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user.username = req.username
    await db.commit()
    return ok({"id": user.id, "username": user.username, "role": user.role, "status": user.status}, "用户名修改成功")


@router.get("/stats")
async def get_user_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    from app.models.message import Message
    from app.models.document import Document
    from app.models.conversation import Conversation

    if user.role == "admin":
        # 管理员：显示所有用户的总共问答次数
        qa_count = (await db.execute(
            select(func.count()).select_from(Message).where(Message.role == "user")
        )).scalar()
        # 文档数量（所有文档）
        doc_count = (await db.execute(
            select(func.count()).select_from(Document)
        )).scalar()
    else:
        # 普通用户：只显示当前用户的问答次数
        # 先获取用户的会话ID列表
        conv_ids = (await db.execute(
            select(Conversation.id).where(Conversation.user_id == user.id)
        )).scalars().all()

        if conv_ids:
            # 统计这些会话中的用户消息数量
            qa_count = (await db.execute(
                select(func.count()).select_from(Message).where(
                    Message.conversation_id.in_(conv_ids),
                    Message.role == "user"
                )
            )).scalar()
        else:
            qa_count = 0

        # 文档数量（用户上传的文档，如果documents表有user_id字段）
        # 如果没有user_id字段，则显示所有文档数量
        doc_count = (await db.execute(
            select(func.count()).select_from(Document)
        )).scalar()

    return ok({"qa_count": qa_count, "doc_count": doc_count})
