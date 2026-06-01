from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.model_provider import ModelProvider
from app.models.model_config import ModelConfig
from app.models.model_preset import ModelPreset
from typing import Optional, List


async def get_providers(db: AsyncSession) -> List[ModelProvider]:
    result = await db.execute(select(ModelProvider))
    return result.scalars().all()


async def get_provider_by_id(db: AsyncSession, provider_id: int) -> Optional[ModelProvider]:
    result = await db.execute(select(ModelProvider).where(ModelProvider.id == provider_id))
    return result.scalar_one_or_none()


async def create_provider(db: AsyncSession, provider: ModelProvider) -> ModelProvider:
    db.add(provider)
    await db.flush()
    await db.refresh(provider)
    return provider


async def update_provider(db: AsyncSession, provider_id: int, **kwargs) -> None:
    await db.execute(update(ModelProvider).where(ModelProvider.id == provider_id).values(**kwargs))


async def delete_provider(db: AsyncSession, provider_id: int) -> None:
    provider = await get_provider_by_id(db, provider_id)
    if provider:
        await db.delete(provider)


async def get_configs(db: AsyncSession, model_type: str = "") -> List[ModelConfig]:
    query = select(ModelConfig)
    if model_type:
        query = query.where(ModelConfig.model_type == model_type)
    result = await db.execute(query)
    return result.scalars().all()


async def get_config_by_id(db: AsyncSession, config_id: int) -> Optional[ModelConfig]:
    result = await db.execute(select(ModelConfig).where(ModelConfig.id == config_id))
    return result.scalar_one_or_none()


async def get_default_config(db: AsyncSession, model_type: str) -> Optional[ModelConfig]:
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.model_type == model_type, ModelConfig.is_default == True, ModelConfig.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_config_with_provider(db: AsyncSession, config_id: int):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(ModelConfig).where(ModelConfig.id == config_id).options(selectinload(ModelConfig.provider))
    )
    return result.scalar_one_or_none()


async def create_config(db: AsyncSession, config: ModelConfig) -> ModelConfig:
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return config


async def set_default(db: AsyncSession, config_id: int, model_type: str) -> None:
    await db.execute(update(ModelConfig).where(ModelConfig.model_type == model_type).values(is_default=False))
    await db.execute(update(ModelConfig).where(ModelConfig.id == config_id).values(is_default=True))


async def get_presets(db: AsyncSession, user_id: int, role: str) -> List[ModelPreset]:
    query = select(ModelPreset)
    if role != "admin":
        query = query.where((ModelPreset.scope == "global") | (ModelPreset.created_by == user_id))
    result = await db.execute(query)
    return result.scalars().all()


async def create_preset(db: AsyncSession, preset: ModelPreset) -> ModelPreset:
    db.add(preset)
    await db.flush()
    await db.refresh(preset)
    return preset


async def update_preset(db: AsyncSession, preset_id: int, **kwargs) -> None:
    await db.execute(update(ModelPreset).where(ModelPreset.id == preset_id).values(**kwargs))


async def delete_preset(db: AsyncSession, preset_id: int) -> None:
    result = await db.execute(select(ModelPreset).where(ModelPreset.id == preset_id))
    preset = result.scalar_one_or_none()
    if preset:
        await db.delete(preset)
