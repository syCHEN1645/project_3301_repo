import os
import subprocess
import sys
import cv2
import json
import math

from config import DETECTION_MODEL_PATH, KEY_POINT_MODEL_PATH, SEGMENTATION_MODEL_PATH, CONFIG_CALIBRATION_SIMPLE_PATH

INPUT_PATH = "test_cv_local/inputs/"
OUTPUT_PATH = "test_cv_local/outputs/"
ANALYSIS_FILE_NAME = "analysis.txt"
CV_RESULT_FILE_NAME = "result.json"
GOOD_THRESHOLD = 1.6
OK_THRESHOLD = 3
PATITION = "========================================================="

def main():
    print(PATITION)
    print("Key in d/D to start with creating new dataset, or")
    print("key in t/T to start testing from existing dataset:")
    key = (str)(input())
    if key == "d" or key == "D":
        create_dataset()
    elif key == "t" or key == "T":
        index, start_marking, end_marking, unit = get_config()
        print("Key in dataset (input) folder name: ")
        in_name = str(input())
        in_path = INPUT_PATH + in_name
        os.makedirs(in_path, exist_ok=True)
        print("Key in result (output) folder name: ")
        out_name = str(input())
        out_path = OUTPUT_PATH + out_name
        os.makedirs(out_path, exist_ok=True)
        run_test(in_path=in_path,
                 out_path=out_path,
                 start_marking=start_marking,
                 end_marking=end_marking,
                 unit=unit)


def get_config():
    print("==============Getting configuration data===========")
    print("Key in camera index: ")
    index = (int)(input())
    with open(CONFIG_CALIBRATION_SIMPLE_PATH) as f:
        data = json.load(f)
        for obj in data:
            if obj["index"] == index:
                start_marking = obj["start_marking"]
                end_marking = obj["end_marking"]
                unit = obj["unit"]
                break

    # choose load config or manual input config
    print(f"start_marking={start_marking}\nend_marking={end_marking}\nunit={unit}")
    print("Key in Y/y to use the above loaded params, else key in any other letter to manual input:")
    key = str(input())
    if not (key == "y" or key == "Y"):
        print("Key in start marking: ")
        start_marking = (float)(input())
        print("Key in end marking: ")
        end_marking = (float)(input())
        print("Key in unit: ")
        unit = (str)(input())

    return index, start_marking, end_marking, unit



def create_dataset():
    print(PATITION)
    print("Key in dataset (input) folder name: ")
    in_name = str(input())
    print("Key in number of images: ")
    num = (int)(input())
    
    in_path = INPUT_PATH + in_name
    os.makedirs(in_path, exist_ok=True)

    index, start_marking, end_marking, unit = get_config()
    
    # start taking and saving images
    cam = cv2.VideoCapture(index)
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
        
        print(f"***CV model result will be compared with {correct_reading}***")
        print(f"Taking image {i} ...")
        
        # exhaust stale frames
        for _ in range(0, math.floor(cam.get(cv2.CAP_PROP_BUFFERSIZE)) + 1):
            ret, frame = cam.read()

        img_path = in_path + "/" + str(correct_reading) + ".jpg"
        flag = cv2.imwrite(img_path, frame)
        if not flag:
            print("Image save failed")
        else:
            print(f"Took image {i} and saved in {img_path}")
        i += 1
    cam.release()
    
    # choose quit or run test
    print(f"Key in t/T to start testing on the new dataset under the configurations of camera {index}, or")
    print("key in any other letter to exit:")
    key = str(input())
    if key == "t" or key == "T":
        print("Key in result (output) folder name: ")
        out_name = str(input())
        out_path = OUTPUT_PATH + out_name
        os.makedirs(out_path, exist_ok=True)
        run_test(in_path, out_path, start_marking, end_marking, unit)


def run_test(in_path, out_path, start_marking, end_marking, unit):
    print(PATITION)
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

    # overall test statistics
    n_good = 0
    n_ok = 0
    n_bad = 0
    n_fail = 0

    counter = 0
    for fp in os.listdir(out_path):
        # get actual reading
        if fp.endswith(".jpg"):
            counter += 1
            cv_result_path = out_path + "/" + str(fp) + "/" + CV_RESULT_FILE_NAME
            try:
                with open(f"{cv_result_path}", "r") as f:
                    data = json.load(f)
                    actual_reading = data[0]["reading"]
            except:
                print(f"Result of {fp} is not found, taken as failed")
                actual_reading = "Failed"

            # calculate statics
            try:
                correct_reading = float(str(fp)[0: str(fp).find(".jpg")])
            except ValueError:
                # expedient way to handle error
                print(f"Cannot extract the correct reading from picture name for {fp}, assume -999")
                correct_reading = -999
            if isinstance(actual_reading, float):
                error = actual_reading - correct_reading
                percent_error = abs(round(error / scale * 100, 3))
            else:
                error = "Failed"
                percent_error = "Failed"
            analysis = {
                "index": counter, 
                "correct": correct_reading, 
                "actual": actual_reading, 
                "error": error,
                "percent": percent_error
            }
            full_analysis.append(analysis)

            # add to overall statistics
            if isinstance(percent_error, str):
                n_fail += 1
            elif isinstance(percent_error, float):
                if percent_error <= GOOD_THRESHOLD:
                    n_good += 1
                elif percent_error <= OK_THRESHOLD:
                    n_ok += 1
                else:
                    n_bad += 1

    p_good = n_good / counter * 100
    p_ok = n_ok / counter * 100
    p_bad = n_bad / counter * 100
    p_fail = n_fail / counter * 100
    stat = {
        "Total number": counter,
        "Good": GOOD_THRESHOLD,
        "Good number": n_good,
        "Good percent": p_good,
        "OK": OK_THRESHOLD,
        "OK number": n_ok,
        "OK percent": p_ok,
        "Bad": "Bad",
        "Bad number": n_bad,
        "Bad percent": p_bad,
        "Fail": "Failed",
        "Fail number": n_fail,
        "Fail percent": p_fail,
    }

    # store analysis
    with open(f"{analysis_path}", "w") as f:
        json.dump({"Results" :full_analysis, "Stat": stat}, f, indent=4)

    print("=================Test Results================")
    for a in full_analysis:
        print(f"{a}")
    print("=================Overall Stats===============")
    print(stat)

if __name__=="__main__":
    main()
