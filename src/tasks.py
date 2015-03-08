import time
import datetime
import logging
import redis
from celery import Task
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from src import redis_connection, models, statsd_client, settings
from src.worker import celery

logger = get_task_logger(__name__)


class BaseTask(Task):
    abstract = True

    def after_return(self, *args, **kwargs):
        models.db.close_db(None)

    def __call__(self, *args, **kwargs):
        models.db.connect_db()
        return super(BaseTask, self).__call__(*args, **kwargs)


@celery.task(base=BaseTask)
def cleanup_query_results():
    """
    Job to cleanup unused query results -- such that no query links to them anymore, and older than a week (so it's less
    likely to be open in someone's browser and be used).

    Each time the job deletes only 100 query results so it won't choke the database in case of many such results.
    """

    unused_query_results = models.QueryResult.unused().limit(100)
    total_unused_query_results = models.QueryResult.unused().count()
    deleted_count = models.QueryResult.delete().where(models.QueryResult.id << unused_query_results).execute()

    logger.info("Deleted %d unused query results out of total of %d." % (deleted_count, total_unused_query_results))


@celery.task(base=BaseTask)
def record_event(event):
    models.Event.record(event)
