#!/usr/bin/env python3
"""Per-camera capture worker.

Pulls RTSP from one Reolink camera over the LAN, motion-gates frame
processing so the Pi isn't running full detection continuously, and on
motion runs vehicle detection + ANPR + colour estimation, writing images
and a DB record for each vehicle found.

Usage:
    python capture_worker.py --camera cam1 [--config config.yaml]
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

import db
from config import load_config
from detector import Detector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

RECONNECT_BACKOFF_SEC = (2, 5, 10, 30)
MOTION_SAMPLE_WIDTH = 320
VEHICLE_CROP_PADDING = 0.08


class CaptureWorker:
    def __init__(self, camera_name: str, config: dict):
        self.camera_name = camera_name
        self.config = config
        self.log = logging.getLogger(camera_name)

        cameras = {c["name"]: c for c in config["cameras"]}
        if camera_name not in cameras:
            raise SystemExit(f"Camera '{camera_name}' not found in config.yaml")
        self.rtsp_url = cameras[camera_name]["rtsp_url"]

        cap_cfg = config.get("capture", {})
        self.sample_interval = float(cap_cfg.get("sample_interval_sec", 0.5))
        self.motion_threshold = float(cap_cfg.get("motion_threshold", 0.015))
        self.event_cooldown = float(cap_cfg.get("event_cooldown_sec", 4))
        self.detect_max_dim = int(cap_cfg.get("detect_max_dim", 640))

        storage_cfg = config["storage"]
        self.captures_dir = Path(storage_cfg["captures_dir"])
        self.db_path = storage_cfg["database_path"]
        db.init_db(self.db_path)

        self.detector = Detector(detect_max_dim=self.detect_max_dim)
        self._running = True
        self._prev_gray = None
        self._last_event_time = 0.0

    def stop(self, *_args):
        self.log.info("Stopping...")
        self._running = False

    def _open_capture(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    def _detect_motion(self, frame: np.ndarray) -> bool:
        h, w = frame.shape[:2]
        scale = MOTION_SAMPLE_WIDTH / w
        small = cv2.resize(frame, (MOTION_SAMPLE_WIDTH, int(h * scale)))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        if self._prev_gray is None:
            self._prev_gray = gray
            return False

        diff = cv2.absdiff(self._prev_gray, gray)
        self._prev_gray = gray
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        changed_fraction = float(np.count_nonzero(thresh)) / thresh.size
        return changed_fraction >= self.motion_threshold

    def _handle_event(self, frame: np.ndarray):
        vehicles = self.detector.detect_vehicles(frame)
        if not vehicles:
            return

        now = datetime.now()
        date_dir = now.strftime("%Y-%m-%d")
        ts = now.strftime("%Y%m%dT%H%M%S_%f")
        out_dir = self.captures_dir / date_dir / self.camera_name
        out_dir.mkdir(parents=True, exist_ok=True)

        full_rel = Path(date_dir) / self.camera_name / f"{ts}_full.jpg"
        cv2.imwrite(str(self.captures_dir / full_rel), frame)

        h, w = frame.shape[:2]
        for idx, vehicle in enumerate(vehicles):
            x1, y1, x2, y2 = vehicle.bbox
            bw, bh = x2 - x1, y2 - y1
            pad_x, pad_y = int(bw * VEHICLE_CROP_PADDING), int(bh * VEHICLE_CROP_PADDING)
            cx1, cy1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
            cx2, cy2 = min(w, x2 + pad_x), min(h, y2 + pad_y)
            crop = frame[cy1:cy2, cx1:cx2]
            if crop.size == 0:
                continue

            plate = self.detector.read_plate(crop)
            color = self.detector.estimate_color(crop)

            vehicle_rel = Path(date_dir) / self.camera_name / f"{ts}_v{idx}.jpg"
            cv2.imwrite(str(self.captures_dir / vehicle_rel), crop)

            plate_rel = None
            if plate.crop is not None and plate.crop.size > 0:
                plate_rel = Path(date_dir) / self.camera_name / f"{ts}_v{idx}_plate.jpg"
                cv2.imwrite(str(self.captures_dir / plate_rel), plate.crop)

            db.insert_event(
                self.db_path,
                timestamp=now.isoformat(timespec="seconds"),
                camera=self.camera_name,
                vehicle_type=vehicle.vehicle_type,
                plate=plate.text,
                plate_confidence=plate.confidence,
                color=color,
                full_image_path=str(full_rel),
                vehicle_image_path=str(vehicle_rel),
                plate_image_path=str(plate_rel) if plate_rel else None,
            )
            self.log.info(
                "Captured %s vehicle=%s plate=%s color=%s",
                self.camera_name, vehicle.vehicle_type, plate.text, color,
            )

    def run(self):
        self.log.info("Starting capture worker for %s", self.camera_name)
        backoff_idx = 0

        while self._running:
            cap = self._open_capture()
            if not cap.isOpened():
                wait = RECONNECT_BACKOFF_SEC[min(backoff_idx, len(RECONNECT_BACKOFF_SEC) - 1)]
                self.log.warning("Could not open RTSP stream, retrying in %ss", wait)
                cap.release()
                time.sleep(wait)
                backoff_idx += 1
                continue
            backoff_idx = 0
            self._prev_gray = None
            last_sample = 0.0

            while self._running:
                if not cap.grab():
                    self.log.warning("Lost stream, reconnecting")
                    break

                now = time.time()
                if now - last_sample < self.sample_interval:
                    continue
                last_sample = now

                ok, frame = cap.retrieve()
                if not ok or frame is None:
                    continue

                try:
                    if self._detect_motion(frame):
                        if now - self._last_event_time >= self.event_cooldown:
                            self._last_event_time = now
                            self._handle_event(frame)
                except Exception:
                    self.log.exception("Error processing frame")

            cap.release()

        self.log.info("Capture worker stopped for %s", self.camera_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", required=True, help="Camera name from config.yaml")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config) if args.config else load_config()
    worker = CaptureWorker(args.camera, config)

    signal.signal(signal.SIGTERM, worker.stop)
    signal.signal(signal.SIGINT, worker.stop)

    worker.run()


if __name__ == "__main__":
    sys.exit(main())
