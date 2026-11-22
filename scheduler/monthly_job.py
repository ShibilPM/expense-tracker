"""
Monthly Email Report Scheduler
Runs on the 1st of each month to send expense reports.
This is a placeholder for Phase 6 implementation.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from database.crud import get_users, get_email_config
from config import config
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def send_monthly_reports():
    """Job to send monthly reports to all users with email enabled."""
    logger.info("Running monthly report job...")

    users = get_users(active_only=True)
    for user in users:
        email_config = get_email_config(user.id)
        if email_config and email_config.is_enabled:
            logger.info(f"Sending report for {user.name} to {email_config.recipient_email}")
            # TODO: Implement actual email sending in Phase 6
            # send_report_email(user, email_config)


def start_scheduler():
    """Start the background scheduler."""
    # Run on 1st of every month at 9:00 AM
    scheduler.add_job(
        send_monthly_reports,
        trigger=CronTrigger(day=1, hour=9, minute=0, timezone=config.TIMEZONE),
        id="monthly_report",
        name="Monthly Expense Report",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started - monthly reports will run on 1st of each month at 9:00 AM")


def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")


if __name__ == "__main__":
    # For testing
    logging.basicConfig(level=logging.INFO)
    start_scheduler()

    # Keep running
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_scheduler()