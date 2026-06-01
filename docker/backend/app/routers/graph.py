from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services import kg_service

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


class EntityRequest(BaseModel):
    name: str
    type: str
    description: str = ""
    doc_id: Optional[int] = None


class RelationRequest(BaseModel):
    source: str
    relation: str
    target: str


@router.get("/overview")
async def graph_overview(limit: int = 200, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    data = kg_service.get_overview(limit)
    return ok(data)


@router.get("/entities")
async def list_entities(page: int = 1, size: int = 20, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    data = kg_service.get_overview(1000)
    entities = list({n["name"]: n for n in data["nodes"]}.values())
    total = len(entities)
    start = (page - 1) * size
    return ok({"items": entities[start:start + size], "total": total})


@router.post("/entities")
async def create_entity(req: EntityRequest, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    kg_service.create_entity(req.name, req.type, req.description, req.doc_id)
    return ok(message="实体创建成功")


@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: str, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    kg_service.delete_entity(entity_id)
    return ok(message="实体删除成功")


@router.get("/search")
async def search_graph(q: str = "", user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    if not q:
        return ok({"nodes": [], "edges": []})
    data = kg_service.search_graph(q)
    return ok(data)


@router.post("/relations")
async def create_relation(req: RelationRequest, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    kg_service.create_relation(req.source, req.relation, req.target)
    return ok(message="关系创建成功")
