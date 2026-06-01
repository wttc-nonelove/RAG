import os
import pdfplumber
from docx import Document as DocxDocument
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao import document_dao, file_store, chroma_repo
from app.models.document import Document
from app.utils.text_processor import clean_text, chunk_text
from app.utils.embedding import embedding_client
from app.utils.kg_extractor import extract as kg_extract
from app.dao import neo4j_repo


ALLOWED_TYPES = {"PDF": ".pdf", "DOCX": ".docx", "TXT": ".txt"}


def _detect_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    for ft, e in ALLOWED_TYPES.items():
        if e == ext:
            return ft
    raise ValueError(f"不支持的文件类型: {ext}")


async def upload_and_parse(db: AsyncSession, file_content: bytes, filename: str, tag: str, user_id: int) -> Document:
    file_type = _detect_type(filename)
    filepath = file_store.save_file(file_content, filename)
    doc = Document(
        filename=filename,
        file_type=file_type,
        file_size=len(file_content),
        file_path=filepath,
        tag=tag,
        parse_status="pending",
        uploaded_by=user_id,
    )
    doc = await document_dao.create(db, doc)
    await db.commit()
    return doc


async def parse_document(doc_id: int) -> None:
    from app.database import async_session
    async with async_session() as db:
        doc = await document_dao.get_by_id(db, doc_id)
        if not doc:
            return

        await document_dao.update_status(db, doc_id, "parsing")
        await db.commit()

        try:
            text = _extract_text(doc.file_path, doc.file_type)
            text = clean_text(text)
            chunks = chunk_text(text)

            embeddings = await embedding_client.encode_batch_from_db(db, chunks)
            ids = [f"doc{doc_id}_chunk{i}" for i in range(len(chunks))]
            metadatas = [{"doc_id": doc_id, "filename": doc.filename, "chunk_index": i} for i in range(len(chunks))]
            chroma_repo.add_batch(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

            try:
                kg_data = await kg_extract(text[:3000], doc_id, doc.filename)
                for entity in kg_data.get("entities", []):
                    neo4j_repo.create_entity(entity["name"], entity.get("type", "概念"), entity.get("description", ""), doc_id)
                for rel in kg_data.get("relations", []):
                    neo4j_repo.create_relation(rel["source"], rel["relation"], rel["target"])
            except Exception as e:
                import loguru
                loguru.logger.error(f"KG storage failed: {e}")

            await document_dao.update_status(db, doc_id, "completed")
        except Exception as e:
            await document_dao.update_status(db, doc_id, "failed", str(e))

        await db.commit()


def _extract_text(filepath: str, file_type: str) -> str:
    if file_type == "PDF":
        with pdfplumber.open(filepath) as pdf:
            return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    elif file_type == "DOCX":
        doc = DocxDocument(filepath)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    elif file_type == "TXT":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError(f"不支持的文件类型: {file_type}")


async def get_preview(db: AsyncSession, doc_id: int, page: int = 1, page_size: int = 50) -> dict:
    doc = await document_dao.get_by_id(db, doc_id)
    if not doc:
        raise ValueError("文档不存在")
    text = _extract_text(doc.file_path, doc.file_type)
    lines = text.split("\n")
    total_pages = (len(lines) + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "filename": doc.filename,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "content": "\n".join(lines[start:end]),
        "has_next": end < len(lines),
    }


async def delete_document(db: AsyncSession, doc_id: int) -> None:
    doc = await document_dao.get_by_id(db, doc_id)
    if not doc:
        return
    try:
        chroma_repo.delete_by_doc_id(doc_id)
    except Exception:
        pass
    try:
        neo4j_repo.delete_by_doc_id(doc_id)
    except Exception:
        pass
    file_store.delete_file(doc.file_path)
    await document_dao.delete_doc(db, doc_id)
    await db.commit()
