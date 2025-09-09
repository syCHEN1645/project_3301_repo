import cv2
import time
import os
import sys
from datetime import datetime

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

