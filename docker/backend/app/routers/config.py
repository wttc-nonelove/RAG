from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services import config_service, dashboard_service

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


@router.get("")
async def get_config(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await config_service.get_all(db)
    return ok(result)


@router.put("")
async def update_config(body: dict, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await config_service.update_batch(db, body)
    return ok(message="配置更新成功")


@router.get("/system-info")
async def get_system_info(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    status = await dashboard_service.get_system_status()
    return ok({"version": "1.0.0", "python": "3.11", "services": status})
