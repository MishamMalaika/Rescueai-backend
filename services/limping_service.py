from ultralytics import YOLO
import cv2
import numpy as np
from collections import deque

# Models
detect_model = YOLO("yolo26n.pt")
pose_model   = YOLO("best (2).pt")

# Config
WINDOW_SIZE           = 80
PERSISTENCE_FRAMES    = 80    # ~1.5 sec at 30fps — continuous limping
ASYMMETRY_THRESHOLD   = 0.90
LOW_CONF_THRESHOLD    = 0.03
EDGE_MARGIN           = 10
INTERMITTENT_FRAMES   = 200   # ~6.5 sec at 30fps — intermittent limping

LOWER_KP      = [14, 15, 16, 17, 18, 19]
LOWER_KP_CONF = [18, 19, 20, 21, 22, 23]

def detect_limping(video_path: str) -> dict:
    left_history         = deque(maxlen=WINDOW_SIZE)
    right_history        = deque(maxlen=WINDOW_SIZE)
    limp_counter         = 0
    intermittent_counter = 0
    limping              = False
    total_frames          = 0
    limp_frames          = 0

    cap = cv2.VideoCapture(video_path)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        total_frames += 1

        # ─── Dog Detect ───────────────────────────────────────
        det_results = detect_model(frame, conf=0.1, verbose=False)
        dog_box = None
        for det in det_results:
            for box, cls in zip(
                det.boxes.xyxy.cpu().numpy(),
                det.boxes.cls.cpu().numpy()
            ):
                if int(cls) == 16:
                    dog_box = box
                    break

        if dog_box is None:
            continue

        x1, y1, x2, y2 = map(int, dog_box)

        # ─── Edge Check ───────────────────────────────────────
        if (x1 <= EDGE_MARGIN or y1 <= EDGE_MARGIN or
            x2 >= width - EDGE_MARGIN or y2 >= height - EDGE_MARGIN):
            continue

        # ─── Dog Crop ─────────────────────────────────────────
        pad = 20
        x1c = max(0, x1 - pad)
        y1c = max(0, y1 - pad)
        x2c = min(width,  x2 + pad)
        y2c = min(height, y2 + pad)
        dog_crop = frame[y1c:y2c, x1c:x2c]

        if dog_crop.size == 0:
            continue

        # ─── Pose ─────────────────────────────────────────────
        pose_results = pose_model(dog_crop, conf=0.1, verbose=False)

        for result in pose_results:
            if result.keypoints is None or len(result.keypoints.xy) == 0:
                continue

            kp   = result.keypoints.xy.cpu().numpy()[0]
            conf = result.keypoints.conf.cpu().numpy()[0]

            if len(kp) < 20:
                continue

            crop_height = y2c - y1c
            center_x    = (x2c - x1c) / 2

            if crop_height == 0:
                continue

            low_conf_paws = sum(
                1 for idx in LOWER_KP_CONF
                if idx < len(conf) and conf[idx] < LOW_CONF_THRESHOLD
            )

            left_y_vals  = []
            right_y_vals = []

            for idx in LOWER_KP:
                if idx < len(kp):
                    x, y = kp[idx]
                    if y > 0:
                        normalized_y = y / crop_height
                        if x < center_x:
                            left_y_vals.append(normalized_y)
                        else:
                            right_y_vals.append(normalized_y)

            if left_y_vals:
                left_history.append(np.mean(left_y_vals))
            if right_y_vals:
                right_history.append(np.mean(right_y_vals))

            left_missing  = len(left_y_vals) == 0
            right_missing = len(right_y_vals) == 0

            if low_conf_paws >= 2:
                limp_counter         += 2
                intermittent_counter += 1
            elif left_missing or right_missing:
                limp_counter = max(0, limp_counter - 3)
            else:
                if len(left_history) >= 10 and len(right_history) >= 10:
                    left_rom  = max(left_history)  - min(left_history)
                    right_rom = max(right_history) - min(right_history)
                    max_rom   = max(left_rom, right_rom)

                    if max_rom > 0:
                        asymmetry = abs(left_rom - right_rom) / max_rom
                        if asymmetry > ASYMMETRY_THRESHOLD:
                            limp_counter         += 1
                            intermittent_counter += 1
                        else:
                            limp_counter = max(0, limp_counter - 3)

            limp_counter = min(limp_counter, PERSISTENCE_FRAMES * 2)

            # ─── Limping Decision ─────────────────────────────
            # Case 1: Continuous — 1.5 sec
            if limp_counter >= PERSISTENCE_FRAMES:
                limping = True
                limp_frames += 1

            # Case 2: Intermittent — total accumulated signals
            if intermittent_counter >= INTERMITTENT_FRAMES:
                limping = True

            break

    cap.release()

    return {
        "limping":               limping,
        "total_frames":          total_frames,
        "limp_frames":           limp_frames,
        "intermittent_counter":  intermittent_counter,
    }