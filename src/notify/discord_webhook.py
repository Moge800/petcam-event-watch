from __future__ import annotations

from datetime import datetime
from typing import Any

import requests


class DiscordWebhookNotifier:
    def __init__(self, webhook_url: str, timeout_seconds: float = 8.0):
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def send_event(self, label: str, confidence: float, frame: Any) -> bool:
        try:
            import cv2  # type: ignore

            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                return False

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = f"[petcam] {label} detected (conf={confidence:.3f}) at {ts}"

            files = {
                "file": ("snapshot.jpg", buf.tobytes(), "image/jpeg"),
            }
            data = {"content": content}

            r = requests.post(
                self.webhook_url,
                data=data,
                files=files,
                timeout=self.timeout_seconds,
            )
            return 200 <= r.status_code < 300
        except Exception as e:  # noqa: BLE001
            print(f"[warn] Discord webhook notify failed: {e}")
            return False
