"""Optional Outreach polling schedule (only when OAuth is configured)."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.config import outreach_oauth_configured, settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _poll_job() -> None:
    from api.outreach_client import run_sync

    try:
        count = run_sync()
        logger.info("Scheduled Outreach sync complete: %s events ingested", count)
    except Exception as e:
        logger.error("Scheduled Outreach sync failed: %s", e, exc_info=True)


def start_scheduler() -> None:
    if not outreach_oauth_configured():
        logger.info("Outreach scheduler skipped (OAuth not configured in .env)")
        return

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
        "Outreach scheduler started (Mon-Fri 8am-5pm CT, every %s min)",
        settings.OUTREACH_POLL_INTERVAL_MINUTES,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Outreach scheduler stopped")


def get_next_run_time():
    job = scheduler.get_job("outreach_poll")
    return job.next_run_time if job else None
