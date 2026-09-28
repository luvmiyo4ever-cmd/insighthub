"""ARQ worker for asynchronous document ingestion."""

import asyncio

from arq import cron
from arq.connections import RedisSettings
from prometheus_client import start_http_server

from app.core.config import get_settings
from app.core.metrics import (
    ingestion_jobs_total,
    ingestion_processing_duration,
    ingestion_queue_depth,
    ingestion_worker_up,
)
from app.services.ingestion import process_document


async def ingest_document(ctx, document_id: int, filename: str, content: bytes):
    """Process one queued document.

    process_document is intentionally reused because it already provides
    idempotent processing for retries.
    """
    settings = get_settings()
    # Only an operator-set environment value can activate this bounded Day 4
    # lab hook. It does not alter queue names, retry semantics, or the
    # processing function used for real ingestion.
    if settings.day4_chaos_enabled and settings.day4_chaos_worker_delay_seconds:
        await asyncio.sleep(settings.day4_chaos_worker_delay_seconds)
    try:
        with ingestion_processing_duration.time():
            try:
                result = process_document(document_id, filename, content)
            except Exception:
                ingestion_jobs_total.labels("failed").inc()
                raise
    finally:
        await record_queue_depth(ctx)
    ingestion_jobs_total.labels("ready").inc()
    return result


async def record_queue_depth(ctx):
    """Read ARQ's own sorted-set queue; no queue format or retry behavior changes."""
    redis = ctx["redis"]
    ingestion_queue_depth.set(await redis.zcard(redis.default_queue_name))


async def worker_startup(ctx):
    """Expose worker-only metrics without changing the public API contract."""
    server, _thread = start_http_server(get_settings().worker_metrics_port)
    ctx["metrics_server"] = server
    ingestion_worker_up.set(1)
    await record_queue_depth(ctx)


async def worker_shutdown(ctx):
    ingestion_worker_up.set(0)
    server = ctx.get("metrics_server")
    if server is not None:
        server.shutdown()


class WorkerSettings:
    functions = [ingest_document]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    on_startup = worker_startup
    on_shutdown = worker_shutdown
    cron_jobs = [cron(record_queue_depth, second={0, 15, 30, 45})]

    # Retry failed jobs.
    max_tries = 3

    # Document parsing/embedding may involve external providers.
    job_timeout = 300
