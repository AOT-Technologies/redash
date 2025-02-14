import logging
from functools import partial

from rq import get_current_job
from rq.decorators import job as rq_job
from redash.utils.job_filter import CurrentJobFilter
from redash import rq_redis_connection, settings
#from redash.authentication.org_resolving import _get_current_org
from redash.tasks.worker import Queue as RedashQueue
default_operational_queues = ["periodic", "emails", "default"]
default_query_queues = ["scheduled_queries", "queries", "schemas"]
default_queues = default_operational_queues + default_query_queues


class StatsdRecordingJobDecorator(rq_job):  # noqa
    """
    RQ Job Decorator mixin that uses our Queue class to ensure metrics are accurately incremented in Statsd
    """

    queue_class = RedashQueue


job = partial(
    StatsdRecordingJobDecorator, connection=rq_redis_connection, failure_ttl=settings.JOB_DEFAULT_FAILURE_TTL
)



def get_job_logger(name):
    logger = logging.getLogger("rq.job." + name)

    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(settings.RQ_WORKER_JOB_LOG_FORMAT)
    handler.addFilter(CurrentJobFilter())

    logger.addHandler(handler)
    logger.propagate = False

    return logger
