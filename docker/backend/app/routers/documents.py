from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.dao import document_dao
from app.services import document_service

router = APIRouter()


def ok(data=None, message="ok"):
    return {"code": 200, "data": data, "message": message}


@router.get("/stats")
async def get_document_stats(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await document_service.get_document_stats(db)
    return ok(result)


@router.get("")
async def list_documents(
    page: int = 1, size: int = 20, keyword: str = "", file_type: str = "", status: str = "",
    user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    docs, total = await document_dao.get_list(db, page, size, keyword, file_type, status)
    items = [
        {
            "id": d.id, "filename": d.filename, "file_type": d.file_type,
            "file_size": d.file_size, "tag": d.tag, "parse_status": d.parse_status,
            "version": d.version, "created_at": str(d.created_at),
        }
        for d in docs
    ]
    return ok({"items": items, "total": total, "page": page, "size": size})


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), tag: Optional[str] = Form(None),
    user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    doc = await document_service.upload_and_parse(db, content, file.filename, tag, user.id)
    background_tasks.add_task(document_service.parse_document, doc.id)
    return ok({"id": doc.id, "filename": doc.filename, "file_type": doc.file_type, "file_size": doc.file_size, "parse_status": doc.parse_status, "version": doc.version})


@router.get("/{doc_id}")
async def get_document(doc_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    doc = await document_dao.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return ok({
        "id": doc.id, "filename": doc.filename, "file_type": doc.file_type,
        "file_size": doc.file_size, "tag": doc.tag, "parse_status": doc.parse_status,
        "version": doc.version, "error_message": doc.error_message,
        "created_at": str(doc.created_at), "updated_at": str(doc.updated_at) if doc.updated_at else None,
    })


@router.get("/{doc_id}/preview")
async def preview_document(doc_id: int, page: int = 1, page_size: int = 50, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        result = await document_service.get_preview(db, doc_id, page, page_size)
        return ok(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{doc_id}/update")
async def update_document(
    doc_id: int, file: UploadFile = File(...),
    user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    doc = await document_dao.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    from app.dao import file_store
    file_store.delete_file(doc.file_path)
    content = await file.read()
    filepath = file_store.save_file(content, file.filename)
    from sqlalchemy import update
    from app.models.document import Document
    await db.execute(update(Document).where(Document.id == doc_id).values(
        filename=file.filename, file_path=filepath, file_size=len(content),
        parse_status="pending", version=doc.version + 1,
    ))
    await db.commit()
    return ok(message="文档更新成功")


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await document_service.delete_document(db, doc_id)
    return ok(message="文档删除成功")


@router.post("/{doc_id}/reparse")
async def reparse_document(doc_id: int, background_tasks: BackgroundTasks, user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    doc = await document_dao.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    background_tasks.add_task(document_service.parse_document, doc_id)
    return ok(message="重新解析已触发")
