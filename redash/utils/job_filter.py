
import logging
from rq import get_current_job

class CurrentJobFilter(logging.Filter):
    org_id = "default"
    def filter(self, record):
        current_job = get_current_job()

        record.job_id = current_job.id if current_job else ""
        record.job_func_name = current_job.func_name if current_job else ""
#        record.org_id = _get_current_org()
        record.org_id = CurrentJobFilter.org_id
        return True
