import requests
import os
from logger import logger

# Load Slack webhook URL from environment
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_slack_notification(message: str):
    """
    Sends a notification to Slack using the configured webhook URL.

    :param message: The message to send to Slack.
    """
    if not SLACK_WEBHOOK_URL:
        logger.error("Slack Webhook URL is not configured.")
        return

    payload = {
        "text": message,
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            logger.info("Slack notification sent successfully.")
        else:
            logger.error(f"Failed to send Slack notification. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
