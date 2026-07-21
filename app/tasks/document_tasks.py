from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.document_tasks.test_background_task")
def test_background_task(message: str) -> dict[str, str]:
    return {
        "status": "completed",
        "message": message,
    }