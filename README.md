# petcam-event-watch

Event-driven pet camera monitor (YOLO + cooldown gate).

## Goal
- Avoid sending every frame to LLM
- Run local detection first (YOLO/OpenCV)
- Send only meaningful events to assistant/Discord

## Architecture
1. **Capture layer**: USB cam or RTSP
2. **Local detector**: YOLO
3. **Event gate**: label filter + consecutive hits + cooldown
4. **Notifier**: send only event snapshots
5. **Optional LLM**: summarize event image only when needed

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
```

## Tuning tips
- Too many false positives → increase `CONF_THRESHOLD` (e.g. `0.5`)
- Missed detections → set `MIN_CONSECUTIVE=1`
- Too many alerts → increase `COOLDOWN_SECONDS`

## Status
- USB camera capture: ✅
- YOLO26 inference: ✅
- Event trigger pipeline: ✅
