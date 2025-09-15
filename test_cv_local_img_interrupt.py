import os
import math
import sys
import subprocess
import cv2
import json

from config import DETECTION_MODEL_PATH, KEY_POINT_MODEL_PATH, SEGMENTATION_MODEL_PATH, CONFIG_CALIBRATION_SIMPLE_PATH
# from auto_process import scanActiveCameras

INPUT_PATH = "test_cv_local/inputs/"
OUTPUT_PATH = "test_cv_local/outputs/"
ANALYSIS_FILE_NAME = "analysis.txt"
CV_RESULT_FILE_NAME = "result.json"

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
    # keep in order the correct readings
    correct_readings = []
    
    i = 1
    while i <= num:
        # key in the correct reading
        print("***Next: key in the correct reading (eye-power)***")
        while (True):
            try:
                correct_reading = (float)(input())
                break
            except ValueError:
                print("Value error, should be a float")
        correct_readings.append(correct_reading)
        
        print(f"***CV model result will be compared with {correct_reading}***")
        print(f"Taking image {i} ...")
        
        # exhaust stale frames
        for _ in range(0, math.floor(cam.get(cv2.CAP_PROP_BUFFERSIZE)) + 1):
            ret, frame = cam.read()

        img_path = in_path + "/" + str(i) + ".jpg"
        flag = cv2.imwrite(img_path, frame)
        if not flag:
            print("Image save failed")
        else:
            print(f"Took image {i} and saved in {img_path}")

        i += 1
    cam.release()


    try:
        subprocess.run([
            sys.executable,
            "analog_gauge_reader/pipeline_v5.py",
            "--detection_model", DETECTION_MODEL_PATH,
            "--segmentation_model", SEGMENTATION_MODEL_PATH,
            "--key_point_model", KEY_POINT_MODEL_PATH,
            "--base_path", out_path,
            "--input", in_path,
            "--debug",
            "--eval",
            "--start_marking", str(start_marking),
            "--end_marking", str(end_marking),
            "--unit", str(unit)
        ], check=True)
    except Exception as e:
        print(f"Error running pipeline: {e}")

    # analyse correctness of results
    scale = end_marking - start_marking
    analysis_path = out_path + "/" + ANALYSIS_FILE_NAME
    full_analysis = []
    i = 1
    while i <= num:
        # get actual reading
        cv_result_path = out_path + "/" + str(i) + ".jpg" + "/" + CV_RESULT_FILE_NAME
        with open(f"{cv_result_path}", "r") as f:
            data = json.load(f)
            actual_reading = data[0]["reading"]

        # calculate statics
        correct_reading = correct_readings[i - 1]
        if isinstance(actual_reading, float):
            error = actual_reading - correct_reading
            percent_error = abs(round(error / scale * 100, 3))
        else:
            error = "Failed"
            percent_error = "Failed"
        analysis = {
            "index": i, 
            "correct": correct_reading, 
            "actual": actual_reading, 
            "error": error,
            "percent": percent_error
            }
        full_analysis.append(analysis)
        i += 1

    # store analysis
    with open(f"{analysis_path}", "w") as f:
        json.dump(full_analysis, f, indent=4)

    for a in full_analysis:
        print(f"{a}")

if __name__=="__main__":
    main()
