from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List


class SystemConfig:
    pass


async def get_all(db: AsyncSession) -> List:
    from app.models.system_config import SystemConfig as SC
    result = await db.execute(select(SC))
    return result.scalars().all()


async def get_by_key(db: AsyncSession, key: str) -> Optional[str]:
    from app.models.system_config import SystemConfig as SC
    result = await db.execute(select(SC).where(SC.config_key == key))
    row = result.scalar_one_or_none()
    return row.config_value if row else None


async def update_batch(db: AsyncSession, configs: dict) -> None:
    from app.models.system_config import SystemConfig as SC
    for key, value in configs.items():
        result = await db.execute(select(SC).where(SC.config_key == key))
        existing = result.scalar_one_or_none()
        if existing:
            await db.execute(update(SC).where(SC.config_key == key).values(config_value=str(value)))
        else:
            new_config = SC(config_key=key, config_value=str(value))
            db.add(new_config)
    await db.flush()
