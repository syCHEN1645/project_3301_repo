import os
import time
import sys
import cv2
import json

from config import DETECTION_MODEL_PATH, KEY_POINT_MODEL_PATH, SEGMENTATION_MODEL_PATH, CONFIG_CALIBRATION_SIMPLE_PATH
from auto_process import scanActiveCameras

INPUT_PATH = "test_cv_local/inputs/"
OUTPUT_PATH = "test_cv_local/outputs/"
TIME_GAP = 5

def main():
    # camera_index_list = scanActiveCameras()
    print("Key in folder name: ")
    folder_name = input()
    print("Key in camera index: ")
    index = (int)(input())
    print("Key in number of images: ")
    num = (int)(input())

    with open(CONFIG_CALIBRATION_SIMPLE_PATH) as f:
        data = json.load(f)
        for obj in data:
            if obj["index"] == index:
                start_marking = obj["start_marking"]
                end_marking = obj["end_marking"]
                unit = obj["unit"]
                break
    
    out_path = OUTPUT_PATH + folder_name
    in_path = INPUT_PATH + folder_name
    os.makedirs(in_path, exist_ok=True)
    os.makedirs(out_path, exist_ok=True)

    cam = cv2.VideoCapture(index)
    print(f"!!!!!!!!Taking photo in {TIME_GAP} seconds!!!!!!!!!")
    time.sleep(TIME_GAP)
    print("!!!!!!!!!Start taking photo now!!!!!!!!!!!")
    i = 1
    while i <= num:
        print(f"Took image {i}, waiting for {TIME_GAP}s...")
        ret, frame = cam.read()
        img_path = INPUT_PATH + folder_name + "/" + str(i) + ".jpg"
        print(img_path)
        flag = cv2.imwrite(img_path, frame)
        if not flag:
            print("Image save failed")
        else:
            print(f"Image {i} is saved successfully at {img_path}")
        time.sleep(TIME_GAP)
        i += 1
    cam.release()

    try:
        os.execv(sys.executable, 
                 [sys.executable, 
                  "analog_gauge_reader/pipeline_v5.py",
                  "--detection_model",
                  DETECTION_MODEL_PATH,
                  "--segmentation_model",
                  SEGMENTATION_MODEL_PATH,
                  "--key_point_model",
                  KEY_POINT_MODEL_PATH,
                  "--base_path",
                  out_path,
                  "--input",
                  in_path,
                  "--debug",
                  "--eval",
                  "--start_marking",
                  (str)(start_marking),
                  "--end_marking",
                  (str)(end_marking),
                  "--unit",
                  (str)(unit)])
    except Exception as e:
        print(f"{e}")

if __name__=="__main__":
    main()
