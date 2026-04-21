import requests
import json
import logging
from .schema import DailyDigest

logger = logging.getLogger(__name__)

class NtfyNotifier:
    """Sends the daily digest to a mobile device via ntfy.sh."""
    def __init__(self, topic: str):
        self.topic = topic
        self.url = "https://ntfy.sh"

    def notify(self, digest: DailyDigest):
        """Publishes the summary and key insights to the ntfy topic."""
        # Build a structured Markdown message
        lines = [
            "📝 **DAILY DIGEST**",
            digest.enhanced_summary,
        ]

        message_body = "\n".join(lines)

        payload = {
            "topic": self.topic,
            "message": message_body,
            "title": "Your Morning Mail Digest",
            "tags": ["mailbox_with_mail", "robot"],
            "markdown": True,
            "click": "https://mail.google.com"
        }

        try:
            response = requests.post(
                self.url,
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Successfully sent notification to ntfy topic: {self.topic}")
        except Exception as e:
            logger.error(f"Failed to send ntfy notification: {e}")
            self._send_error_alert(str(e))

    def _send_error_alert(self, error_details: str):
        """Attempts to send a minimal, high-priority failure alert if the main notification fails."""
        payload = {
            "topic": self.topic,
            "message": f"⚠️ Failed to send your morning summary. Please check the agent logs.\n\nError: {error_details}",
            "title": "Mailflow Agent: Notification Error",
            "priority": "high",
            "tags": ["warning", "rotating_light"]
        }
        try:
            # We use a very short timeout here to avoid hanging the main process
            requests.post(
                self.url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                timeout=5
            )
        except Exception:
            # If even the error alert fails, we stop to avoid infinite recursion or crashing the agent
            logger.critical("Could not send even the error alert to ntfy.")