from prometheus_client import Counter, generate_latest
from flask import Response
from logger import logger

# Prometheus metrics
job_state_total = Counter("job_state_total", "Total jobs by state", ["status"])
job_retries_total = Counter("job_retries_total", "Total retries by job_id", ["job_id"])
stuck_jobs_total = Counter("stuck_jobs_total", "Total stuck jobs detected", [])

def setup_metrics(app):
    @app.route("/metrics")
    def metrics():
        logger.debug("Prometheus metrics endpoint accessed.")
        return Response(generate_latest(), content_type="text/plain")

def increment_metric(metric_name, labels):
    try:
        if metric_name == "job_state_total":
            job_state_total.labels(**labels).inc()
        elif metric_name == "job_retries_total":
            job_retries_total.labels(**labels).inc()
        elif metric_name == "stuck_jobs_total":
            stuck_jobs_total.inc()
        logger.debug(f"Metric '{metric_name}' incremented with labels: {labels}")
    except Exception as e:
        logger.error(f"Error incrementing metric '{metric_name}': {e}")
