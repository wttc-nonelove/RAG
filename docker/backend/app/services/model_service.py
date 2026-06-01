from sqlalchemy.ext.asyncio import AsyncSession
from app.dao import model_dao
from app.models.model_provider import ModelProvider
from app.models.model_config import ModelConfig
from app.models.model_preset import ModelPreset
from app.utils.encryption import encrypt, decrypt
import httpx


async def test_connectivity(db: AsyncSession, provider_id: int) -> dict:
    provider = await model_dao.get_provider_by_id(db, provider_id)
    if not provider:
        raise ValueError("供应商不存在")
    try:
        api_key = decrypt(provider.api_key_encrypted)
    except Exception:
        return {
            "provider_name": provider.provider_name,
            "api_base_url": provider.api_base_url,
            "status": "error",
            "latency_ms": 0,
            "error": "API Key 未配置或格式错误，请先更新 API Key",
        }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{provider.api_base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            return {
                "provider_name": provider.provider_name,
                "api_base_url": provider.api_base_url,
                "status": "ok" if resp.status_code == 200 else "error",
                "latency_ms": int(resp.elapsed.total_seconds() * 1000),
            }
    except Exception as e:
        return {
            "provider_name": provider.provider_name,
            "api_base_url": provider.api_base_url,
            "status": "error",
            "latency_ms": 0,
            "error": str(e),
        }


async def set_default_model(db: AsyncSession, config_id: int) -> None:
    config = await model_dao.get_config_by_id(db, config_id)
    if not config:
        raise ValueError("模型配置不存在")
    await model_dao.set_default(db, config_id, config.model_type)
    await db.commit()


async def save_prompt_template(db: AsyncSession, model_id: int, system_prompt: str) -> None:
    from sqlalchemy import update
    await db.execute(update(ModelConfig).where(ModelConfig.id == model_id).values(system_prompt=system_prompt))
    await db.commit()


async def create_provider(db: AsyncSession, name: str, api_base_url: str, api_key: str) -> ModelProvider:
    provider = ModelProvider(
        provider_name=name,
        api_base_url=api_base_url,
        api_key_encrypted=encrypt(api_key),
    )
    return await model_dao.create_provider(db, provider)


async def create_config(db: AsyncSession, data: dict) -> ModelConfig:
    config = ModelConfig(**data)
    return await model_dao.create_config(db, config)


async def create_preset(db: AsyncSession, data: dict, user_id: int) -> ModelPreset:
    preset = ModelPreset(**data, created_by=user_id)
    return await model_dao.create_preset(db, preset)


async def get_enabled_chat_models(db: AsyncSession) -> list:
    configs = await model_dao.get_configs(db, "chat")
    return [
        {"id": c.id, "model_name": c.model_name, "is_default": c.is_default}
        for c in configs if c.is_active
    ]
