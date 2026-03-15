"""
Local task scheduler — spaces out Reddit posts to avoid spam detection.
Uses APScheduler for background job execution.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from database import (
    get_post, update_post, get_reddit_token,
    create_scheduled_job, update_scheduled_job, get_jobs_for_post,
)
from reddit_api import submit_post, refresh_access_token
import database

logger = logging.getLogger("scheduler")

scheduler = AsyncIOScheduler()


def get_delay_minutes() -> int:
    return int(os.getenv("POST_DELAY_MINUTES", "12"))


async def ensure_valid_token() -> str:
    """Check token expiry and refresh if needed. Returns a valid access_token."""
    import time
    token_data = await get_reddit_token()
    if not token_data:
        raise RuntimeError("No Reddit token stored. Please authenticate first.")

    if token_data.get("expires_at") and float(token_data["expires_at"]) < time.time() + 60:
        # Token expired or about to — refresh it
        new_data = await refresh_access_token(token_data["refresh_token"])
        await database.save_reddit_token(new_data)
        return new_data["access_token"]

    return token_data["access_token"]


async def publish_to_subreddit(job_id: int, post_id: int, subreddit: str):
    """
    The actual publishing task — called by APScheduler at the scheduled time.
    """
    logger.info(f"[Job {job_id}] Publishing post {post_id} to r/{subreddit}")
    await update_scheduled_job(job_id, {"status": "running"})

    try:
        access_token = await ensure_valid_token()
        post = await get_post(post_id)
        if not post:
            raise RuntimeError(f"Post {post_id} not found")

        result = await submit_post(
            access_token=access_token,
            subreddit=subreddit,
            title=post["title"],
            body=post["body"],
        )

        # Extract the post URL from Reddit's response
        url = ""
        if "json" in result and "data" in result["json"]:
            url = result["json"]["data"].get("url", "")

        await update_scheduled_job(job_id, {"status": "completed", "result_url": url})
        logger.info(f"[Job {job_id}] ✓ Published to r/{subreddit}: {url}")

        # Check if all jobs for this post are done
        jobs = await get_jobs_for_post(post_id)
        if all(j["status"] in ("completed", "failed") for j in jobs):
            urls = [j["result_url"] for j in jobs if j.get("result_url")]
            await update_post(post_id, {
                "status": "published",
                "published_urls": urls,
                "published_at": datetime.utcnow().isoformat(),
            })

    except Exception as e:
        logger.error(f"[Job {job_id}] ✗ Failed for r/{subreddit}: {e}")
        await update_scheduled_job(job_id, {"status": "failed", "error": str(e)})
        # Mark the post as failed if this was the only/last job
        jobs = await get_jobs_for_post(post_id)
        if all(j["status"] in ("completed", "failed") for j in jobs):
            await update_post(post_id, {"status": "failed", "error_log": str(e)})


async def schedule_post_publishing(post_id: int, subreddits: list[str]) -> list[dict]:
    """
    Schedule a post to be published across multiple subreddits
    with configurable delays between each.
    """
    delay = get_delay_minutes()
    scheduled = []
    now = datetime.utcnow()

    for i, subreddit in enumerate(subreddits):
        run_time = now + timedelta(minutes=i * delay)
        job_id = await create_scheduled_job(
            post_id=post_id,
            subreddit=subreddit,
            scheduled_time=run_time.isoformat(),
        )

        # Add to APScheduler
        scheduler.add_job(
            publish_to_subreddit,
            trigger=DateTrigger(run_date=run_time),
            args=[job_id, post_id, subreddit],
            id=f"publish_{job_id}",
            replace_existing=True,
        )

        scheduled.append({
            "job_id": job_id,
            "subreddit": subreddit,
            "scheduled_time": run_time.isoformat(),
        })
        logger.info(f"Scheduled post {post_id} → r/{subreddit} at {run_time.isoformat()}")

    # Update post status
    await update_post(post_id, {
        "status": "scheduled",
        "scheduled_at": now.isoformat(),
        "target_subreddits": subreddits,
    })

    return scheduled


def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped")
