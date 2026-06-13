from __future__ import annotations

from typing import Any


class Camera:
    def __init__(self, source: str | int = 0):
        self.source: str | int = int(source) if str(source).isdigit() else source
        try:
            import cv2  # type: ignore

            self._cv2 = cv2
            # Try CAP_V4L2 backend explicitly first (fixes index-based open failure on some UVC devices)
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                self.cap.release()
                self.cap = cv2.VideoCapture(self.source)
        except Exception as e:  # noqa: BLE001
            self._cv2 = None
            self.cap = None
            print(f"[warn] OpenCV unavailable: {e}")

    def read(self) -> Any | None:
        if self.cap is None:
            return None
        ok, frame = self.cap.read()
        if not ok:
            return None
        return frame

    def release(self) -> None:
        if self.cap:
            self.cap.release()
