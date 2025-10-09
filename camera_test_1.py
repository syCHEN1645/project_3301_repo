import cv2
import time
import os
import sys
from datetime import datetime
from ultralytics import YOLO

from analog_gauge_reader.key_point_detection.key_point_inference import KeyPointInference, detect_key_points
from config import SEGMENTATION_MODEL_PATH, DETECTION_MODEL_PATH, KEY_POINT_MODEL_PATH

while True:
    model1 = YOLO(SEGMENTATION_MODEL_PATH)
    print(type(model1))
    print("----------------")
    model2 = YOLO(DETECTION_MODEL_PATH)
    print(type(model2))
    print(isinstance(model2, YOLO))
    print("----------------")
    model3 = key_point_inferencer = KeyPointInference(KEY_POINT_MODEL_PATH)
    print(type(model3))
    print(isinstance(model3, KeyPointInference))
    print("----------------")

os.makedirs("sample_pics", exist_ok=True)
# 0 maps to /dev/video0
# 1 maps to /dev/video1
# and so on
if len(sys.argv) == 2:
    capture = cv2.VideoCapture(int(sys.argv[1]))
else:
    capture = cv2.VideoCapture(0)

if not capture.isOpened():
    print("Camera is not open")
    exit()

try:
    while True:
        ret, frame = capture.read()
        if ret:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"sample_pics/{timestamp}.jpg"
            cv2.imwrite(filepath, frame)
            print(f"Saved {filepath}")
        else:
            print("Failed to capture")
        time.sleep(5)
except KeyboardInterrupt:
    print("Exiting")

capture.release()

