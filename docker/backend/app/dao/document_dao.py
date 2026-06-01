from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app.models.document import Document
from typing import Optional, List


async def get_by_id(db: AsyncSession, doc_id: int) -> Optional[Document]:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()


async def get_list(db: AsyncSession, page: int = 1, size: int = 20, keyword: str = "", file_type: str = "", status: str = "") -> tuple[List[Document], int]:
    query = select(Document)
    count_q = select(func.count()).select_from(Document)

    if keyword:
        query = query.where(Document.filename.contains(keyword))
        count_q = count_q.where(Document.filename.contains(keyword))
    if file_type:
        query = query.where(Document.file_type == file_type)
        count_q = count_q.where(Document.file_type == file_type)
    if status:
        query = query.where(Document.parse_status == status)
        count_q = count_q.where(Document.parse_status == status)

    total = (await db.execute(count_q)).scalar()
    query = query.order_by(Document.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return result.scalars().all(), total


async def create(db: AsyncSession, doc: Document) -> Document:
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def update_status(db: AsyncSession, doc_id: int, status: str, error_message: str = None) -> None:
    values = {"parse_status": status}
    if error_message is not None:
        values["error_message"] = error_message
    from sqlalchemy import update
    await db.execute(update(Document).where(Document.id == doc_id).values(**values))


async def increment_version(db: AsyncSession, doc_id: int) -> None:
    from sqlalchemy import update
    doc = await get_by_id(db, doc_id)
    if doc:
        await db.execute(update(Document).where(Document.id == doc_id).values(version=doc.version + 1))


async def delete_doc(db: AsyncSession, doc_id: int) -> None:
    doc = await get_by_id(db, doc_id)
    if doc:
        await db.delete(doc)


async def get_all_ids(db: AsyncSession) -> List[int]:
    result = await db.execute(select(Document.id))
    return [row[0] for row in result.all()]
