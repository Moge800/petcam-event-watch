from __future__ import annotations

import argparse
import itertools
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # noqa: BLE001
    def load_dotenv() -> None:
        return None

from capture.camera import Camera
from detect.yolo_detector import YOLODetector
from events.gate import CooldownGate
from notify.discord_webhook import DiscordWebhookNotifier


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--max-frames", type=int, default=0)
    return p.parse_args()


def _now_local() -> datetime:
    return datetime.now().astimezone()


def _save_snapshot(frame: Any, snapshots_dir: Path, event_label: str, tick: int) -> str | None:
    try:
        import cv2  # type: ignore

        snapshots_dir.mkdir(parents=True, exist_ok=True)
        ts = _now_local().strftime("%Y%m%d-%H%M%S")
        safe_label = event_label.replace("/", "_").replace(" ", "_")
        out_path = snapshots_dir / f"{ts}_{safe_label}_tick{tick}.jpg"
        ok = cv2.imwrite(str(out_path), frame)
        if not ok:
            return None
        return str(out_path)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] snapshot save failed: {e}")
        return None


def _append_event_log(log_path: Path, payload: dict[str, Any]) -> bool:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[warn] event log append failed: {e}")
        return False


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
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    notify_enabled = os.getenv("NOTIFY_ENABLED", "true").lower() in {"1", "true", "yes", "on"}

    # local persistence
    save_snapshots = os.getenv("SAVE_SNAPSHOTS", "true").lower() in {"1", "true", "yes", "on"}
    snapshots_dir = Path(os.getenv("SNAPSHOTS_DIR", "data/snapshots"))
    event_log_path = Path(os.getenv("EVENT_LOG_PATH", "data/events/events.jsonl"))

    print("[petcam-event-watch] starting")
    print(f"source={source} model={model_name} conf={conf_threshold}")
    print(f"save_snapshots={save_snapshots} snapshots_dir={snapshots_dir}")
    print(f"event_log_path={event_log_path}")

    if args.dry_run:
        print("dry-run: config load OK")
        return

    camera = Camera(source)
    detector = YOLODetector(model_name=model_name, conf_threshold=conf_threshold)
    gate = CooldownGate(cooldown_seconds=cooldown_seconds)
    notifier = (
        DiscordWebhookNotifier(discord_webhook_url)
        if notify_enabled and discord_webhook_url
        else None
    )
    consecutive_hits: dict[str, int] = {}

    try:
        frame_iter = range(args.max_frames) if args.max_frames > 0 else itertools.count()
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
                now = _now_local()
                snapshot_path = (
                    _save_snapshot(frame, snapshots_dir=snapshots_dir, event_label=top.label, tick=i)
                    if save_snapshots
                    else None
                )

                event = {
                    "timestamp": now.isoformat(),
                    "tick": i,
                    "label": top.label,
                    "confidence": round(float(top.confidence), 6),
                    "cooldown_seconds": cooldown_seconds,
                    "hits": consecutive_hits[event_key],
                    "source": str(source),
                    "snapshot_path": snapshot_path,
                }
                logged = _append_event_log(event_log_path, event)

                print(
                    f"[event] tick={i} label={top.label} conf={top.confidence:.3f} "
                    f"(cooldown={cooldown_seconds}s, hits={consecutive_hits[event_key]}) "
                    f"snapshot={snapshot_path} logged={logged}"
                )

                if notifier is not None:
                    sent = notifier.send_event(
                        label=top.label,
                        confidence=top.confidence,
                        frame=frame,
                    )
                    print(f"[notify] discord webhook sent={sent}")
                consecutive_hits[event_key] = 0

    finally:
        camera.release()


if __name__ == "__main__":
    main()
