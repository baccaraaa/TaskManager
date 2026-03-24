import logging
from datetime import datetime, timezone, timedelta

from app.workers.celery_app import celery_app
from app.utils.email import send_email, render_template

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, email: str, username: str):
    try:
        html_content = render_template(
            "welcome.html",
            {"username": username},
        )
        send_email(
            to_email=email,
            subject="Welcome to Task Manager!",
            html_content=html_content,
        )
        logger.info(f"Welcome email sent to {email}")
    except Exception as exc:
        logger.error(f"Failed to send welcome email to {email}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email(self, email: str, reset_token: str):
    try:
        html_content = render_template(
            "password_reset.html",
            {"reset_token": reset_token, "email": email},
        )
        send_email(
            to_email=email,
            subject="Password Reset Request",
            html_content=html_content,
        )
        logger.info(f"Password reset email sent to {email}")
    except Exception as exc:
        logger.error(f"Failed to send password reset email to {email}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_task_reminder(self, task_id: int, assignee_email: str, task_title: str, due_date: str):
    try:
        html_content = render_template(
            "task_reminder.html",
            {"task_title": task_title, "due_date": due_date},
        )
        send_email(
            to_email=assignee_email,
            subject=f"Reminder: Task '{task_title}' is due soon",
            html_content=html_content,
        )
        logger.info(f"Task reminder sent for task {task_id} to {assignee_email}")
    except Exception as exc:
        logger.error(f"Failed to send task reminder for task {task_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def check_due_tasks():
    """Check for tasks due within the next 24 hours and send reminders."""
    from app.db.database import SessionLocal
    from app.db.models import Task, TaskStatus, User
    from sqlalchemy import select, and_

    logger.info("Checking for tasks due soon...")

    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)

        stmt = (
            select(Task, User)
            .join(User, Task.assignee_id == User.id)
            .where(
                and_(
                    Task.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
                    Task.due_date.isnot(None),
                    Task.due_date <= tomorrow,
                    Task.due_date >= now,
                )
            )
        )
        results = db.execute(stmt).all()

        for task, user in results:
            send_task_reminder.delay(
                task_id=task.id,
                assignee_email=user.email,
                task_title=task.title,
                due_date=task.due_date.isoformat(),
            )

        logger.info(f"Found {len(results)} tasks due soon, reminders queued")


# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "check-due-tasks-daily": {
        "task": "app.workers.tasks.check_due_tasks",
        "schedule": 86400.0,  # Every 24 hours
    },
}
