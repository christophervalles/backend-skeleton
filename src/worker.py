from celery import Celery
from datetime import timedelta
from src import settings


celery = Celery('src',
                broker=settings.CELERY_BROKER,
                include='src.tasks')

# Example of how to define a task within a worker
celery_schedule = {
    'refresh_queries': {
        'task': 'app.tasks.refresh_queries',
        'schedule': timedelta(seconds=30)
    }
}

if settings.QUERY_RESULTS_CLEANUP_ENABLED:
    celery_schedule['cleanup_query_results'] = {
        'task': 'app.tasks.cleanup_query_results',
        'schedule': timedelta(minutes=5)
    }

celery.conf.update(CELERY_RESULT_BACKEND=settings.CELERY_BACKEND,
                   CELERYBEAT_SCHEDULE=celery_schedule,
                   CELERY_TIMEZONE='UTC')

if __name__ == '__main__':
    celery.start()