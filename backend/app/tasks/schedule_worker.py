"""
Background scheduler for recurring vulnerability scans.

Runs a lightweight asyncio loop that wakes periodically and dispatches
any due, enabled schedules into the shared scan executor. The loop is
started and stopped by the application lifespan.
"""

from __future__ import annotations

import asyncio

from app.core.config import settings
from app.logger import logger


def _run_tick() -> int:
    """
    Dispatch due schedules using a fresh DB session.
    """

    from app.database.session import SessionLocal
    from app.services.schedule_service import scheduler_tick

    db = SessionLocal()

    try:
        return scheduler_tick(db)
    except Exception:
        logger.exception("Scheduled scan tick failed.")
        return 0
    finally:
        db.close()


async def schedule_loop(
    stop_event: asyncio.Event,
) -> None:
    """
    Poll for due schedules until the stop event is set.
    """

    loop = asyncio.get_running_loop()

    logger.info(
        "Schedule scheduler started (tick: %ss).",
        settings.SCHEDULE_TICK_SECONDS,
    )

    while not stop_event.is_set():
        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=settings.SCHEDULE_TICK_SECONDS,
            )
        except asyncio.TimeoutError:
            pass

        if stop_event.is_set():
            break

        await loop.run_in_executor(None, _run_tick)

    logger.info("Schedule scheduler stopped.")
