# petcam-event-watch

Event-driven pet camera monitor (YOLO + cooldown gate).

## Goal
- Avoid sending every frame to LLM
- Run local detection first (YOLO/OpenCV)
- Send only meaningful events to assistant/Discord
- Persist event history locally (JSONL + snapshots)

## Architecture
1. **Capture layer**: USB cam or RTSP
2. **Local detector**: YOLO
3. **Event gate**: label filter + consecutive hits + cooldown
4. **Local persistence**: event JSONL log + snapshot image
5. **Notifier**: send only event snapshots
6. **Optional LLM**: summarize event image only when needed

## Quick start (uv)
```bash
cd /home/moge/develop/petcam-event-watch
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
uv run python src/main.py --dry-run
```

## Run
```bash
uv run python src/main.py --max-frames 300
# daemon mode
uv run python src/main.py --max-frames 0
```

## Recommended pet profile (dog only)
Set in `.env`:

```env
CAMERA_SOURCE=0
YOLO_MODEL=yolo26n.pt
CONF_THRESHOLD=0.4
ALLOWED_LABELS=dog
MIN_CONSECUTIVE=2
COOLDOWN_SECONDS=45
SAVE_SNAPSHOTS=true
SNAPSHOTS_DIR=data/snapshots
EVENT_LOG_PATH=data/events/events.jsonl
```

## Output files
- Event log: `data/events/events.jsonl`
- Snapshot images: `data/snapshots/*.jpg`

Example event line (JSONL):
```json
{"timestamp":"2026-02-25T18:40:01+09:00","tick":120,"label":"dog","confidence":0.842,"cooldown_seconds":45,"hits":2,"source":"0","snapshot_path":"data/snapshots/20260225-184001_dog_tick120.jpg"}
```

## Tuning tips
- Too many false positives → increase `CONF_THRESHOLD` (e.g. `0.5`)
- Missed detections → set `MIN_CONSECUTIVE=1`
- Too many alerts → increase `COOLDOWN_SECONDS`

## Status
- USB camera capture: ✅
- YOLO26 inference: ✅
- Event trigger pipeline: ✅
- Local event persistence: ✅
