from sqlalchemy.ext.asyncio import AsyncSession
from app.dao import config_dao


async def get_all(db: AsyncSession) -> dict:
    configs = await config_dao.get_all(db)
    return {c.config_key: c.config_value for c in configs}


async def update_batch(db: AsyncSession, configs: dict) -> None:
    await config_dao.update_batch(db, configs)
    await db.commit()
