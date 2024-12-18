import os
from logger import logger

def check_health():
    try:
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = os.getenv("REDIS_PORT", 6379)

        # Mocking a health check; replace with actual checks
        logger.debug("Performing health check for Job State Manager.")
        return {"status": "Healthy", "details": {"redis_host": redis_host, "redis_port": redis_port}}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "Unhealthy", "details": {"error": str(e)}}
