import redis
import os
import time
from slack_notifications import send_slack_notification
from prometheus_metrics import increment_metric
from logger import logger

THRESHOLD_TIMEOUT = int(os.getenv("THRESHOLD_TIMEOUT", 300))  # Default to 300 seconds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))               # Default to 3 retries
PROGRESS_THRESHOLD = int(os.getenv("PROGRESS_THRESHOLD", 10)) # Default to 10 units


class JobManager:
    def __init__(self):
        self.redis_client = redis.StrictRedis(host="redis", port=6379, decode_responses=True)

    def is_valid_job_id(self, job_id):
        """
        Validate job_id format.
        """
        import re
        pattern = r"^[a-zA-Z0-9\-]+$"
        valid = bool(re.match(pattern, job_id))
        logger.debug(f"Job ID validation for {job_id}: {valid}")
        return valid

    def start_job(self, job_id):
        """
        Start a new job.
        """
        if self.redis_client.sismember("active_jobs", job_id):
            logger.warning(f"Duplicate Job ID detected: {job_id}")
            return {"status": "Duplicate Job ID", "job_id": job_id}

        # Mark the job as active and initialize metadata
        self.redis_client.sadd("active_jobs", job_id)
        self.redis_client.hmset(
            f"job:{job_id}",
            {"status": "Running", "progress": 0, "last_progress": 0, "retries": 0, "start_time": time.time()}
        )
        increment_metric("job_state_total", {"status": "Running"})
        logger.info(f"Job {job_id} started successfully.")
        return {"status": "Accepted", "job_id": job_id}

    def get_job_status(self, job_id):
        """
        Fetch the current status of a job.
        """
        if not self.redis_client.exists(f"job:{job_id}"):
            logger.error(f"Job {job_id} not found.")
            return {"status": "Not Found"}
        status = self.redis_client.hgetall(f"job:{job_id}")
        logger.debug(f"Fetched status for Job {job_id}: {status}")
        return status

    def update_progress(self, job_id, progress):
        """
        Update the progress of a running job.
        """
        if not self.redis_client.exists(f"job:{job_id}"):
            logger.error(f"Job {job_id} not found for progress update.")
            return {"status": "Not Found"}

        job_data = self.redis_client.hgetall(f"job:{job_id}")
        if job_data["status"] != "Running":
            logger.warning(f"Progress update ignored for Job {job_id} as it is not in Running state.")
            return {"status": "Not Running", "job_id": job_id}

        self.redis_client.hmset(f"job:{job_id}", {"progress": progress, "last_progress": job_data["progress"]})
        logger.info(f"Progress updated for Job {job_id}. New progress: {progress}")
        return {"status": "Progress Updated", "job_id": job_id}

    def complete_job(self, job_id):
        """
        Mark a job as completed.
        """
        if not self.redis_client.exists(f"job:{job_id}"):
            logger.error(f"Job {job_id} not found for completion.")
            return {"status": "Not Found"}

        self.redis_client.hmset(f"job:{job_id}", {"status": "Completed"})
        self.redis_client.srem("active_jobs", job_id)
        increment_metric("job_state_total", {"status": "Completed"})
        logger.info(f"Job {job_id} marked as completed.")
        return {"status": "Completed", "job_id": job_id}

    def fail_job(self, job_id):
        """
        Mark a job as failed.
        """
        if not self.redis_client.exists(f"job:{job_id}"):
            logger.error(f"Job {job_id} not found for failure.")
            return {"status": "Not Found"}

        self.redis_client.hmset(f"job:{job_id}", {"status": "Failed"})
        self.redis_client.srem("active_jobs", job_id)
        increment_metric("job_state_total", {"status": "Failed"})
        send_slack_notification(f"❌ Job {job_id} has failed.")
        logger.error(f"Job {job_id} marked as failed.")
        return {"status": "Failed", "job_id": job_id}

    def retry_job(self, job_id):
        """
        Retry a previously failed job.
        """
        if not self.redis_client.exists(f"job:{job_id}"):
            logger.error(f"Job {job_id} not found for retry.")
            return {"status": "Not Found"}

        retries = int(self.redis_client.hget(f"job:{job_id}", "retries")) + 1
        if retries > MAX_RETRIES:
            logger.warning(f"Job {job_id} exceeded max retries.")
            return {"status": "Max Retries Exceeded", "job_id": job_id}

        self.redis_client.hmset(f"job:{job_id}", {"status": "Retrying", "progress": 0, "retries": retries})
        increment_metric("job_retries_total", {"job_id": job_id})
        logger.info(f"Retrying job {job_id}. Attempt {retries}.")
        return {"status": "Retried", "job_id": job_id}

    def check_stuck_jobs(self):
        """
        Identify and handle stuck jobs.
        """
        all_jobs = self.redis_client.keys("job:*")
        for job_key in all_jobs:
            job = self.redis_client.hgetall(job_key)
            if job["status"] == "Running":
                elapsed_time = time.time() - float(job["start_time"])
                progress_diff = int(job["progress"]) - int(job["last_progress"])

                if elapsed_time > THRESHOLD_TIME and progress_diff < PROGRESS_THRESHOLD:
                    logger.warning(f"Job {job_key.split(':')[1]} is stuck. Marking as failed.")
                    self.fail_job(job_key.split(":")[1])
