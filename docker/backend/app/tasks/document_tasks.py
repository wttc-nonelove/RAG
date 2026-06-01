import asyncio
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2)
def parse_document_task(self, doc_id: int):
    from app.database import async_session
    from app.services.document_service import parse_document

    async def _run():
        async with async_session() as db:
            await parse_document(db, doc_id)

    try:
        asyncio.run(_run())
    except Exception as exc:
        self.retry(exc=exc, countdown=30)
