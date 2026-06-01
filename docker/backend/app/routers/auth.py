from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

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
