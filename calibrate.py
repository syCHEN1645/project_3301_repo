import json
import os
import sys
import cv2

import subprocess
import platform

from config import CONFIG_CALIBRATION_PATH
from auto_process import scanActiveCameras

import time

def display_image_crossplatform(image, save_path="temp_image.jpg"):
    cv2.imwrite(save_path, image)

    # Only attempt to open if DISPLAY is available (not headless)
    if os.environ.get("DISPLAY"):
        if platform.system() == "Linux":
            subprocess.run(["xdg-open", save_path])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", save_path])
        elif platform.system() == "Windows":
            os.startfile(save_path)
    else:
        print(f"Running headless. Saved image to {save_path}.")


def main():
    # todo: scan cameras
    # todo: get a proper list of cam names
    camera_index_list = scanActiveCameras()
    # calibrate each camera
    # show picture from cameras to confirm
    config = []
    # todo: loop this for each cam
    for index in camera_index_list:
        print("Taking a photo and displaying in imageviewer...")
        # todo: open and display photo
        cam = cv2.VideoCapture(index)
        if not cam.isOpened():
            print("Camera error, please re-run the programme")
            return

        ret, frame = cam.read()
        if ret:
            try:
                # cv2.imshow(f"{index}", frame)
                # cv2.waitKey(1000)

                display_image_crossplatform(frame, f"camera_{index}_image_{time.time()}.jpg")
            except Exception:
                print("Failed to show image.")

        cam.release()

        print(f"\nDetected camera index: {index}")
        print("Please enter a list of dictionaries (one per camera) in the following format:\n")
        print("""{
            "camera_name": "Cam1",
            "wellhead_name": "WH1",
            "gauge_name": "G1",
            "start_marking": 0.0,
            "end_marking": 100.0,
            "unit": "psi"
        }""")
        print("\nPaste your input and press Enter:")

        user_input_str = input()

        expected_keys = {"camera_name", "wellhead_name", "gauge_name", "start_marking", "end_marking", "unit"}

        try:
            user_input = json.loads(user_input_str)

            if not isinstance(user_input, dict):
                raise ValueError("Input must be a dictionary.")
            
            if not expected_keys.issubset(user_input.keys()):
                raise ValueError(f"Missing keys in entry {index}: {user_input}")
            
            if not all(isinstance(user_input[key], (str)) for key in ["camera_name", "wellhead_name", "gauge_name", "unit"]):
                raise TypeError("start_marking and end_marking must both be numbers")
            if not all(isinstance(user_input[key], (float)) for key in ["start_marking", "end_marking"]):
                raise TypeError("start_marking and end_marking must both be numbers")

        except Exception as e:
            print(f"Error parsing input: {e}")
            exit(1)

        try:
            cv2.destroyWindow(f"{index}")
            print("Closing image")
        except Exception:
            print("Image already closed")

        user_input_full_dict = {index : user_input}
        config.append(user_input_full_dict)

    config = sorted(config)

    # write all info (from all cameras) into config file
    with open(CONFIG_CALIBRATION_PATH, "w") as f:
        json.dump(config, f)
        print("Calibration is saved")

    print("Please proceed to run auto_process.py")
    print("Start running auto_process.py? y/n")
    s = input()
    if (s == "y" or s == "Y"):
        try:
            os.execv(sys.executable, [sys.executable, "auto_process.py"])
        except Exception as e:
            print(f"{e}")
    else:
        print("Quit")


if __name__=="__main__":
    main()
