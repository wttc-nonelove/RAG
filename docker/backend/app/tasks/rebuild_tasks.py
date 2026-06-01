import asyncio
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True)
def rebuild_vectors_task(self, target_dimension: int):
    from app.database import async_session
    from app.dao import document_dao, chroma_repo
    from app.utils.embedding import embedding_client
    from app.services.document_service import _extract_text
    from app.utils.text_processor import clean_text, chunk_text

    async def _run():
        async with async_session() as db:
            docs, _ = await document_dao.get_list(db, page=1, size=10000, status="completed")
            for doc in docs:
                try:
                    chroma_repo.delete_by_doc_id(doc.id)
                    text = _extract_text(doc.file_path, doc.file_type)
                    text = clean_text(text)
                    chunks = chunk_text(text)
                    embeddings = await embedding_client.encode_batch(chunks)
                    ids = [f"doc{doc.id}_chunk{i}" for i in range(len(chunks))]
                    metadatas = [{"doc_id": doc.id, "filename": doc.filename, "chunk_index": i} for i in range(len(chunks))]
                    chroma_repo.add_batch(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
                except Exception:
                    continue

    asyncio.run(_run())
