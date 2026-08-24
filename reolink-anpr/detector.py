"""Vehicle detection, plate ANPR, and dominant-colour estimation.

Everything here runs locally on-device (YOLOv8n via ultralytics, plate
detection/OCR via fast-alpr's bundled ONNX models) — no network calls, no
API keys, no cloud accounts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import cv2

# COCO class ids for vehicle-like objects that YOLOv8n was pretrained on.
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

# Small fixed palette for naming a vehicle's dominant colour. Order matters
# only for readability; matching is nearest-neighbour in RGB space.
NAMED_COLORS = {
    "white": (255, 255, 255),
    "black": (20, 20, 20),
    "silver": (192, 192, 192),
    "grey": (120, 120, 120),
    "red": (170, 30, 30),
    "blue": (30, 60, 160),
    "green": (30, 110, 60),
    "yellow": (220, 200, 40),
    "orange": (220, 120, 30),
    "brown": (100, 65, 40),
}


@dataclass
class VehicleDetection:
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2 in original-frame coords
    vehicle_type: str
    confidence: float


@dataclass
class PlateResult:
    text: Optional[str]
    confidence: Optional[float]
    crop: Optional[np.ndarray]


class Detector:
    """Loads models once and reuses them across frames/cameras."""

    def __init__(self, detect_max_dim: int = 640):
        self.detect_max_dim = detect_max_dim

        from ultralytics import YOLO

        # Nano weights: smallest/fastest YOLOv8 variant, chosen for Pi 4 CPU.
        self._yolo = YOLO("yolov8n.pt")

        from fast_alpr import ALPR

        self._alpr = ALPR(
            detector_model="yolo-v9-t-384-license-plate-end2end",
            ocr_model="cct-xs-v2-global-model",
        )

    def detect_vehicles(self, frame: np.ndarray) -> list[VehicleDetection]:
        h, w = frame.shape[:2]
        scale = min(1.0, self.detect_max_dim / max(h, w))
        small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame

        results = self._yolo.predict(small, verbose=False, conf=0.4)
        detections: list[VehicleDetection] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id not in VEHICLE_CLASSES:
                    continue
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                if scale < 1.0:
                    x1, y1, x2, y2 = x1 / scale, y1 / scale, x2 / scale, y2 / scale
                detections.append(
                    VehicleDetection(
                        bbox=(int(x1), int(y1), int(x2), int(y2)),
                        vehicle_type=VEHICLE_CLASSES[cls_id],
                        confidence=float(box.conf[0]),
                    )
                )
        return detections

    def read_plate(self, vehicle_crop: np.ndarray) -> PlateResult:
        results = self._alpr.predict(vehicle_crop)
        if not results:
            return PlateResult(text=None, confidence=None, crop=None)

        # Multiple plates can be detected in one crop (rare for a single
        # vehicle); keep the highest-confidence OCR read.
        best = max(
            results,
            key=lambda r: getattr(getattr(r, "ocr", None), "confidence", 0.0) or 0.0,
        )
        ocr = getattr(best, "ocr", None)
        text = getattr(ocr, "text", None) if ocr else None
        confidence = getattr(ocr, "confidence", None) if ocr else None

        plate_crop = None
        detection = getattr(best, "detection", None)
        bbox = getattr(detection, "bounding_box", None) if detection else None
        if bbox is not None:
            x1 = int(getattr(bbox, "x1", 0))
            y1 = int(getattr(bbox, "y1", 0))
            x2 = int(getattr(bbox, "x2", 0))
            y2 = int(getattr(bbox, "y2", 0))
            if x2 > x1 and y2 > y1:
                plate_crop = vehicle_crop[y1:y2, x1:x2]

        return PlateResult(text=text, confidence=confidence, crop=plate_crop)

    @staticmethod
    def estimate_color(vehicle_crop: np.ndarray) -> str:
        """Dominant-colour estimate via k-means on the centre of the crop,
        to bias toward vehicle body panels over background/shadow/glass at
        the edges of the box."""
        h, w = vehicle_crop.shape[:2]
        if h == 0 or w == 0:
            return "unknown"

        y0, y1 = int(h * 0.25), int(h * 0.75)
        x0, x1 = int(w * 0.15), int(w * 0.85)
        region = vehicle_crop[y0:y1, x0:x1]
        if region.size == 0:
            region = vehicle_crop

        pixels = region.reshape(-1, 3).astype(np.float32)
        k = 2 if len(pixels) >= 2 else 1
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, k, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS
        )
        counts = np.bincount(labels.flatten())
        dominant_bgr = centers[np.argmax(counts)]
        dominant_rgb = (
            float(dominant_bgr[2]),
            float(dominant_bgr[1]),
            float(dominant_bgr[0]),
        )

        best_name, best_dist = "unknown", float("inf")
        for name, rgb in NAMED_COLORS.items():
            dist = sum((a - b) ** 2 for a, b in zip(dominant_rgb, rgb))
            if dist < best_dist:
                best_name, best_dist = name, dist
        return best_name
