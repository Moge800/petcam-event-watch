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
    p.add_argument("--max-frames", type=int, default=300)
    return p.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    source = os.getenv("CAMERA_SOURCE", "0")
    conf_threshold = float(os.getenv("CONF_THRESHOLD", "0.4"))
    cooldown_seconds = int(os.getenv("COOLDOWN_SECONDS", "300"))
    model_name = os.getenv("YOLO_MODEL", "yolo26n.pt")

    print("[petcam-event-watch] starting")
    print(f"source={source} model={model_name} conf={conf_threshold}")

    if args.dry_run:
        print("dry-run: config load OK")
        return

    camera = Camera(source)
    detector = YOLODetector(model_name=model_name, conf_threshold=conf_threshold)
    gate = CooldownGate(cooldown_seconds=cooldown_seconds)

    try:
        for i in range(args.max_frames):
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

            top = max(detections, key=lambda d: d.confidence)
            event_key = f"{top.label}"

            if gate.allow(event_key):
                print(
                    f"[event] tick={i} label={top.label} conf={top.confidence:.3f} "
                    f"(cooldown={cooldown_seconds}s)"
                )

    finally:
        camera.release()


if __name__ == "__main__":
    main()
