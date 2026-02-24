from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Detection:
    label: str
    confidence: float


class YOLODetector:
    """Ultralytics YOLO detector wrapper.

    If ultralytics is unavailable, this detector works in disabled mode.
    """

    def __init__(self, model_name: str = "yolo26n.pt", conf_threshold: float = 0.4):
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self._model: Any | None = None
        self.enabled = False

        try:
            from ultralytics import YOLO  # type: ignore

            self._model = YOLO(model_name)
            self.enabled = True
        except Exception as e:  # noqa: BLE001
            print(f"[warn] YOLO disabled: {e}")

    def detect(self, frame: Any) -> list[Detection]:
        if not self.enabled or self._model is None:
            return []

        results = self._model.predict(frame, conf=self.conf_threshold, verbose=False)
        detections: list[Detection] = []

        for r in results:
            names = r.names
            for box in r.boxes:
                cls_idx = int(box.cls[0])
                conf = float(box.conf[0])
                label = names.get(cls_idx, str(cls_idx))
                detections.append(Detection(label=label, confidence=conf))

        return detections
