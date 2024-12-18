from flask import Flask, jsonify, request
from health import check_health
from job_manager import JobManager
from prometheus_metrics import setup_metrics
from slack_notifications import send_slack_notification
from kubernetes_events import KubernetesEventTracker
from logger import logger

app = Flask(__name__)

# Initialize components
job_manager = JobManager()
event_tracker = KubernetesEventTracker()

# Initialize Prometheus metrics
setup_metrics(app)

@app.route('/healthz', methods=['GET'])
def health():
    """
    Health check endpoint for Job State Manager.
    Logs health status and returns appropriate HTTP status codes.
    """
    status = check_health()
    logger.info(f"Health check status: {status}")
    return jsonify(status), 200 if status["status"] == "Healthy" else 500

@app.route('/start-job', methods=['POST'])
def start_job():
    """
    API to start a new job.
    Accepts a job_id, validates it, and initiates job execution.
    """
    data = request.json
    job_id = data.get("job_id")

    if not job_manager.is_valid_job_id(job_id):
        logger.warning(f"Invalid Job ID received: {job_id}")
        return jsonify({"status": "Invalid Job ID", "job_id": job_id}), 400

    response = job_manager.start_job(job_id)
    if response["status"] == "Accepted":
        logger.info(f"Job {job_id} successfully started.")
    else:
        logger.warning(f"Failed to start job {job_id}: {response['status']}")
    return jsonify(response), 200 if response["status"] == "Accepted" else 400

@app.route('/job-status', methods=['GET'])
def job_status():
    """
    API to retrieve the current status of a job.
    Accepts a job_id as a query parameter and returns job metadata.
    """
    job_id = request.args.get("job_id")
    response = job_manager.get_job_status(job_id)
    if response["status"] != "Not Found":
        logger.info(f"Job {job_id} status fetched successfully.")
    else:
        logger.error(f"Job {job_id} not found.")
    return jsonify(response), 200 if response["status"] != "Not Found" else 404

@app.route('/fail-job', methods=['POST'])
def fail_job():
    """
    API to forcefully mark a job as failed.
    Accepts a job_id and updates its state to Failed.
    """
    data = request.json
    job_id = data.get("job_id")
    response = job_manager.fail_job(job_id)
    if response["status"] == "Failed":
        logger.info(f"Job {job_id} marked as failed successfully.")
    else:
        logger.error(f"Failed to mark job {job_id} as failed: {response['status']}")
    return jsonify(response), 200

@app.route('/retry-job', methods=['POST'])
def retry_job():
    """
    API to retry a failed job.
    Accepts a job_id and attempts to retry the job.
    """
    data = request.json
    job_id = data.get("job_id")
    response = job_manager.retry_job(job_id)
    if response["status"] == "Retried":
        logger.info(f"Retry initiated for job {job_id}.")
    elif response["status"] == "Max Retries Exceeded":
        logger.warning(f"Max retries exceeded for job {job_id}.")
    else:
        logger.error(f"Failed to retry job {job_id}: {response['status']}")
    return jsonify(response), 200

@app.route('/update-progress', methods=['POST'])
def update_progress():
    """
    API to update the progress of a running job.
    Accepts job_id and progress as parameters.
    """
    data = request.json
    job_id = data.get("job_id")
    progress = data.get("progress")

    if not isinstance(progress, int) or progress < 0:
        logger.warning(f"Invalid progress value received for job {job_id}: {progress}")
        return jsonify({"status": "Invalid Progress", "job_id": job_id}), 400

    response = job_manager.update_progress(job_id, progress)
    if response["status"] == "Progress Updated":
        logger.info(f"Progress updated for job {job_id} to {progress}.")
    else:
        logger.error(f"Failed to update progress for job {job_id}: {response['status']}")
    return jsonify(response), 200

@app.route('/complete-job', methods=['POST'])
def complete_job():
    """
    API to mark a job as completed.
    Accepts a job_id and updates its state to Completed.
    """
    data = request.json
    job_id = data.get("job_id")
    response = job_manager.complete_job(job_id)
    if response["status"] == "Completed":
        logger.info(f"Job {job_id} marked as completed successfully.")
    else:
        logger.error(f"Failed to mark job {job_id} as completed: {response['status']}")
    return jsonify(response), 200

@app.route('/check-stuck-jobs', methods=['POST'])
def check_stuck_jobs():
    """
    API to identify and fail stuck jobs.
    Periodically invoked by CronJobs to manage job state consistency.
    """
    logger.info("Stuck jobs check initiated.")
    job_manager.check_stuck_jobs()
    logger.info("Stuck jobs check completed.")
    return jsonify({"status": "Checked for stuck jobs"}), 200

@app.route('/track-events', methods=['GET'])
def track_events():
    """
    API to track Kubernetes events for relevant pods.
    """
    events = event_tracker.track_events()
    logger.info(f"Tracked {len(events)} events successfully.")
    return jsonify({"events": events}), 200

@app.route('/main-pod/state', methods=['GET'])
def main_pod_state():
    """
    API to fetch the state of the Main Pod.
    """
    states = event_tracker.track_main_pod_state()
    return jsonify({"main_pod_states": states}), 200

@app.route('/main-pod/events', methods=['GET'])
def main_pod_events():
    """
    API to fetch events for the Main Pod.
    """
    events = event_tracker.track_events()
    return jsonify({"main_pod_events": events}), 200

if __name__ == '__main__':
    logger.info("Job State Manager is starting...")
    app.run(host='0.0.0.0', port=8080)
