from __future__ import annotations

import argparse
import time


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    print("[petcam-event-watch] starting")
    if args.dry_run:
        print("dry-run: pipeline skeleton OK")
        return

    # skeleton loop
    for i in range(3):
        print(f"tick {i}: capture -> detect -> gate -> notify")
        time.sleep(1)


if __name__ == "__main__":
    main()
