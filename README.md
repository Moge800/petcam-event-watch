# petcam-event-watch

Private skeleton for pet camera monitoring with low-rate-limit architecture.

## Goal
- Avoid sending every frame to LLM
- Run local detection first (YOLO/OpenCV)
- Send only meaningful events to assistant/Discord

## Architecture
1. **Capture layer**: USB cam or RTSP
2. **Local detector**: YOLO (or simple motion/person/dog classifier)
3. **Event gate**: dedupe, cooldown, thresholding
4. **Notifier**: send only event snapshots
5. **Optional LLM**: summarize event image only when needed

## Quick start (skeleton)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python src/main.py --dry-run
```

## Notes
- This repo is intentionally private (contains home-ops assumptions).
