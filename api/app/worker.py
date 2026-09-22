"""ARQ worker for asynchronous document ingestion."""

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.services.ingestion import process_document


async def ingest_document(ctx, document_id: int, filename: str, content: bytes):
    """Process one queued document.

    process_document is intentionally reused because it already provides
    idempotent processing for retries.
    """
    return process_document(document_id, filename, content)


class WorkerSettings:
    functions = [ingest_document]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)

    # Retry failed jobs.
    max_tries = 3

    # Document parsing/embedding may involve external providers.
    job_timeout = 300