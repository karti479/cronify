import datetime
from flask import jsonify
import logging

logger = logging.getLogger(__name__)

class LicenseManager:
    def __init__(self, redis_conn):
        self.redis = redis_conn
        self.trial_days = 30
        self.valid_keys = [
            "PAID-LICENSE-001", "PAID-LICENSE-002", "PAID-LICENSE-003",
            "PAID-LICENSE-004", "PAID-LICENSE-005"
        ]

    def check_license(self):
        try:
            license_key = self.redis.get("license_key")
            start_date = self.redis.get("start_date")
            if not start_date:
                start_date = datetime.datetime.now().isoformat()
                self.redis.set("start_date", start_date)

            start_date = datetime.datetime.fromisoformat(start_date.decode())
            elapsed_days = (datetime.datetime.now() - start_date).days

            if license_key and license_key.decode() in self.valid_keys:
                return jsonify({"status": "active", "message": "Paid license active."}), 200

            if elapsed_days <= self.trial_days:
                return jsonify({"status": "trial", "message": f"Trial active, {self.trial_days - elapsed_days} days remaining."}), 200

            return jsonify({"status": "expired", "message": "Trial expired. Please update your license."}), 403
        except Exception as e:
            logger.error(f"Error checking license: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    def update_license(self, key):
        try:
            if key in self.valid_keys:
                self.redis.set("license_key", key)
                logger.info("License updated successfully.")
                return jsonify({"status": "success", "message": "License updated successfully."}), 200
            logger.warning("Invalid license key provided.")
            return jsonify({"status": "failed", "message": "Invalid license key."}), 400
        except Exception as e:
            logger.error(f"Error updating license: {str(e)}")
            return jsonify({"status": "error", "message": "Internal server error"}), 500
