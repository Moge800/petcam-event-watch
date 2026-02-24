from __future__ import annotations

import argparse
import os
import time

try:
    from dotenv import load_dotenv
except Exception:  # noqa: BLE001
    def load_dotenv() -> None:
        return None

from capture.camera import Camera
from detect.yolo_detector import YOLODetector
from events.gate import CooldownGate


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max-frames", type=int, default=0)
    return p.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    source = os.getenv("CAMERA_SOURCE", "0")
    conf_threshold = float(os.getenv("CONF_THRESHOLD", "0.4"))
    cooldown_seconds = int(os.getenv("COOLDOWN_SECONDS", "45"))
    model_name = os.getenv("YOLO_MODEL", "yolo26n.pt")
    allowed_labels = {
        x.strip().lower()
        for x in os.getenv("ALLOWED_LABELS", "dog,person").split(",")
        if x.strip()
    }
    min_consecutive = int(os.getenv("MIN_CONSECUTIVE", "2"))

    print("[petcam-event-watch] starting")
    print(f"source={source} model={model_name} conf={conf_threshold}")

    if args.dry_run:
        print("dry-run: config load OK")
        return

    camera = Camera(source)
    detector = YOLODetector(model_name=model_name, conf_threshold=conf_threshold)
    gate = CooldownGate(cooldown_seconds=cooldown_seconds)
    consecutive_hits: dict[str, int] = {}

    try:
        
        frame_iter = range(args.max_frames) if args.max_frames > 0 else iter(int, 1)
        for i in frame_iter:
            frame = camera.read()
            if frame is None:
                print("[warn] camera frame read failed")
                time.sleep(0.2)
                continue

            detections = detector.detect(frame)
            if not detections:
                if i % 60 == 0:
                    print(f"tick={i} no detections")
                continue

            filtered = [d for d in detections if d.label.lower() in allowed_labels]
            if not filtered:
                continue

            top = max(filtered, key=lambda d: d.confidence)
            event_key = f"{top.label.lower()}"
            consecutive_hits[event_key] = consecutive_hits.get(event_key, 0) + 1

            if consecutive_hits[event_key] < min_consecutive:
                continue

            if gate.allow(event_key):
                print(
                    f"[event] tick={i} label={top.label} conf={top.confidence:.3f} "
                    f"(cooldown={cooldown_seconds}s, hits={consecutive_hits[event_key]})"
                )
                consecutive_hits[event_key] = 0

    finally:
        camera.release()


if __name__ == "__main__":
    main()
