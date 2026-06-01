from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services import model_service
from app.dao import model_dao

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


class ProviderRequest(BaseModel):
    provider_name: str
    api_base_url: str
    api_key: str


class ConfigRequest(BaseModel):
    provider_id: int
    model_name: str
    model_type: str
    system_prompt: Optional[str] = None
    embedding_dimension: Optional[int] = None


class PresetRequest(BaseModel):
    name: str
    model_config_id: int
    scope: str = "personal"
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 2048


@router.get("/providers")
async def list_providers(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    providers = await model_dao.get_providers(db)
    return ok([{
        "id": p.id, "provider_name": p.provider_name, "api_base_url": p.api_base_url,
        "is_active": p.is_active, "created_at": str(p.created_at),
    } for p in providers])


@router.post("/providers")
async def create_provider(req: ProviderRequest, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        provider = await model_service.create_provider(db, req.provider_name, req.api_base_url, req.api_key)
        await db.commit()
        return ok({"id": provider.id})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: int, body: dict, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    from app.utils.encryption import encrypt
    values = {}
    if "provider_name" in body:
        values["provider_name"] = body["provider_name"]
    if "api_base_url" in body:
        values["api_base_url"] = body["api_base_url"]
    if "api_key" in body:
        values["api_key_encrypted"] = encrypt(body["api_key"])
    if "is_active" in body:
        values["is_active"] = body["is_active"]
    if values:
        await model_dao.update_provider(db, provider_id, **values)
        await db.commit()
    return ok(message="供应商更新成功")


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await model_dao.delete_provider(db, provider_id)
    await db.commit()
    return ok(message="供应商删除成功")


@router.post("/providers/{provider_id}/test")
async def test_provider(provider_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await model_service.test_connectivity(db, provider_id)
    return ok(result)


@router.get("/configs")
async def list_configs(type: str = "", user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    configs = await model_dao.get_configs(db, type)
    return ok([{
        "id": c.id, "provider_id": c.provider_id, "model_name": c.model_name,
        "model_type": c.model_type, "system_prompt": c.system_prompt,
        "embedding_dimension": c.embedding_dimension, "is_default": c.is_default,
        "is_active": c.is_active,
    } for c in configs])


@router.post("/configs")
async def create_config(req: ConfigRequest, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    config = await model_service.create_config(db, req.model_dump())
    await db.commit()
    return ok({"id": config.id})


@router.put("/configs/{config_id}/set-default")
async def set_default(config_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        await model_service.set_default_model(db, config_id)
        return ok(message="默认模型设置成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/configs/{config_id}")
async def update_config(config_id: int, req: ConfigRequest, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    config = await model_dao.get_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    data = req.model_dump()
    for key, value in data.items():
        if value is not None:
            setattr(config, key, value)
    await db.commit()
    return ok(message="模型配置更新成功")


@router.put("/prompts/{model_id}")
async def save_prompt(model_id: int, body: dict, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await model_service.save_prompt_template(db, model_id, body.get("system_prompt", ""))
    return ok(message="Prompt 模板保存成功")


@router.post("/rebuild-vectors")
async def rebuild_vectors(body: dict, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return ok({"task_id": "rebuild-001", "status": "running", "total_documents": 0})


@router.get("/rebuild-status")
async def rebuild_status(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return ok({"status": "idle"})


@router.get("/usage")
async def get_model_usage(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    from app.models.message import Message
    from app.models.document import Document
    # 按模型统计对话 token 用量
    result = await db.execute(
        select(
            Message.model_name,
            func.sum(Message.tokens_used).label("total_tokens"),
            func.count().label("message_count"),
        )
        .where(Message.role == "bot", Message.model_name.isnot(None))
        .group_by(Message.model_name)
    )
    rows = result.all()
    # 对话 token 总计
    chat_tokens = sum(r[1] or 0 for r in rows)
    chat_messages = sum(r[2] or 0 for r in rows)

    # Embedding token 统计
    embed_result = await db.execute(
        select(func.sum(Document.embedding_tokens))
    )
    embedding_tokens = embed_result.scalar() or 0

    total_tokens = chat_tokens + embedding_tokens
    return ok({
        "total_tokens": total_tokens,
        "chat_tokens": chat_tokens,
        "embedding_tokens": embedding_tokens,
        "total_messages": chat_messages,
        "by_model": [
            {"model_name": r[0], "total_tokens": r[1] or 0, "message_count": r[2], "type": "chat"}
            for r in rows
        ],
    })


@router.get("/presets")
async def list_presets(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    presets = await model_dao.get_presets(db, user.id, user.role)
    return ok([{
        "id": p.id, "name": p.name, "model_config_id": p.model_config_id,
        "scope": p.scope, "description": p.description,
        "temperature": float(p.temperature), "top_p": float(p.top_p),
        "max_tokens": p.max_tokens, "created_by": p.created_by,
    } for p in presets])


@router.post("/presets")
async def create_preset(req: PresetRequest, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    preset = await model_service.create_preset(db, req.model_dump(), user.id)
    await db.commit()
    return ok({"id": preset.id})


@router.put("/presets/{preset_id}")
async def update_preset(preset_id: int, body: dict, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await model_dao.update_preset(db, preset_id, **body)
    await db.commit()
    return ok(message="预设更新成功")


@router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await model_dao.delete_preset(db, preset_id)
    await db.commit()
    return ok(message="预设删除成功")
