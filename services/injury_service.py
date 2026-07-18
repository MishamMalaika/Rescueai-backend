from ultralytics import YOLO
import cv2
import numpy as np
import os

# Model load karo
injury_model = YOLO("best (1).pt")

INJURY_CONF        = 0.5
INJURY_PERSISTENCE = 3

def detect_injury(video_path: str) -> dict:
    injury_counter = 0
    injured        = False
    max_confidence = 0.0
    total_frames   = 0
    injury_frames  = 0

    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        total_frames += 1
        results = injury_model(frame, conf=INJURY_CONF, verbose=False)

        injury_detected = False
        for result in results:
            for cls, conf in zip(
                result.boxes.cls.cpu().numpy(),
                result.boxes.conf.cpu().numpy()
            ):
                if injury_model.names[int(cls)] == "injury":
                    injury_detected = True
                    if conf > max_confidence:
                        max_confidence = float(conf)

        if injury_detected:
            injury_counter += 1
            injury_frames  += 1
        else:
            injury_counter = max(0, injury_counter - 1)

        if injury_counter >= INJURY_PERSISTENCE:
            injured = True

    cap.release()

    return {
        "injured":       injured,
        "confidence":    round(max_confidence, 3),
        "total_frames":  total_frames,
        "injury_frames": injury_frames,
    }
def detect_injury_image(image_path: str) -> dict:
    frame = cv2.imread(image_path)
    if frame is None:
        return {"injured": False, "confidence": 0.0}

    results = injury_model(frame, conf=INJURY_CONF, verbose=False)

    injured        = False
    max_confidence = 0.0

    for result in results:
        for cls, conf in zip(
            result.boxes.cls.cpu().numpy(),
            result.boxes.conf.cpu().numpy()
        ):
            if injury_model.names[int(cls)] == "injury":
                injured = True
                if conf > max_confidence:
                    max_confidence = float(conf)

    return {
        "injured":    injured,
        "confidence": round(max_confidence, 3),
    }