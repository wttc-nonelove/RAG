from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services import user_service

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


@router.get("")
async def list_users(page: int = 1, size: int = 20, keyword: str = "", role: str = "", user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    from app.dao import user_dao
    users, total = await user_dao.get_list(db, page, size, keyword, role)
    from app.schemas.auth import UserInfo
    items = [UserInfo(id=u.id, username=u.username, role=u.role, status=u.status).model_dump() for u in users]
    return ok({"items": items, "total": total, "page": page, "size": size})


@router.post("")
async def create_user(body: dict, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        result = await user_service.create_user(db, body["username"], body["password"], body.get("role", "user"))
        await db.commit()
        return ok(result.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}")
async def update_user(user_id: int, body: dict, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    from app.dao import user_dao
    await user_dao.update_user(db, user_id, **{k: v for k, v in body.items() if k in ("username", "role")})
    return ok(message="用户更新成功")


@router.put("/{user_id}/reset-password")
async def reset_password(user_id: int, body: dict, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await user_service.reset_password(db, user_id, body.get("new_password", "123456"))
    return ok(message="密码重置成功")


@router.put("/{user_id}/status")
async def toggle_status(user_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        new_status = await user_service.toggle_status(db, user_id)
        return ok({"status": new_status})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
