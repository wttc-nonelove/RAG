from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services import history_service
from app.dao import message_dao

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


@router.get("/admin")
async def admin_history(page: int = 1, size: int = 20, keyword: str = "", user_id: int = None, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await history_service.get_admin_history(db, page, size, keyword, user_id)
    return ok(result)


@router.get("/my")
async def my_history(page: int = 1, size: int = 20, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await history_service.get_my_history(db, user.id, page, size)
    return ok(result)


@router.get("/stats")
async def history_stats(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await history_service.get_stats(db)
    return ok(result)


@router.get("/{message_id}")
async def get_message(message_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    msg = await message_dao.get_by_id(db, message_id)
    if not msg:
        return ok(None)
    return ok({"id": msg.id, "role": msg.role, "content": msg.content, "sources": msg.sources, "model_name": msg.model_name, "created_at": str(msg.created_at)})
