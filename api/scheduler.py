"""
APScheduler setup for Outreach activity polling.
Runs poll job Mon-Fri 8am-5pm America/Chicago every OUTREACH_POLL_INTERVAL_MINUTES.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _poll_job() -> None:
    """Scheduled job: fetch Outreach activity and ingest into Project Rift."""
    from api.outreach_client import run_sync

    try:
        count = run_sync()
        logger.info(f"Scheduled Outreach sync complete: {count} events ingested")
    except Exception as e:
        logger.error(f"Scheduled Outreach sync failed: {e}", exc_info=True)


def start_scheduler() -> None:
    """Start the APScheduler. Called once during FastAPI lifespan startup."""
    scheduler.add_job(
        _poll_job,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour="8-17",
            minute=f"*/{settings.OUTREACH_POLL_INTERVAL_MINUTES}",
            timezone="America/Chicago",
        ),
        id="outreach_poll",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"Outreach scheduler started "
        f"(Mon-Fri 8am-5pm CT, every {settings.OUTREACH_POLL_INTERVAL_MINUTES} min)"
    )


def stop_scheduler() -> None:
    """Stop the scheduler. Called during FastAPI lifespan shutdown."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Outreach scheduler stopped")


def get_next_run_time():
    """Return the next scheduled run time, or None if scheduler isn't running."""
    job = scheduler.get_job("outreach_poll")
    return job.next_run_time if job else None
