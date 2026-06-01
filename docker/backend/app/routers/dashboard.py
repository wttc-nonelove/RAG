from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services import dashboard_service

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


@router.get("/stats")
async def get_stats(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await dashboard_service.get_stats(db)
    return ok(result)


@router.get("/trends")
async def get_trends(days: int = 7, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await dashboard_service.get_trends(db, days)
    return ok(result)


@router.get("/storage")
async def get_storage(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await dashboard_service.get_storage()
    return ok(result)


@router.get("/system-status")
async def get_system_status(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await dashboard_service.get_system_status()
    return ok(result)
