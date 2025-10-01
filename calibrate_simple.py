import json
import os
import sys
import cv2

from config import CONFIG_CALIBRATION_SIMPLE_PATH
from auto_process import scanActiveCameras

def main():
    # todo: scan cameras
    # todo: get a proper list of cam names
    camera_index_list = scanActiveCameras()
    # clibrate each camera
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
                cv2.imshow(f"{index}", frame)
                cv2.waitKey(1000)
            except Exception:
                print("Failed to show image.")

        cam.release()

        print(f"Key in start point value for camera {index}: ")
        start_marking = (float)(input())
        print(f"Key in end point value for camera {index}: ")
        end_marking = (float)(input())
        print(f"Key in unit for camera {index}: ")
        unit = (str)(input())
        try:
            cv2.destroyWindow(f"{index}")
            print("Closing image")
        except Exception:
            print("Image already closed")

        config.append(
            {
            "index": index,
            "start_marking": start_marking,
            "end_marking": end_marking,
            "unit": unit
            }
            )

    # write all info (from all cameras) into config file
    with open(CONFIG_CALIBRATION_SIMPLE_PATH, "w") as f:
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


if __name__ == "__main__":
    main()
