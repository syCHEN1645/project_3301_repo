import subprocess
import os
import json
import time
import sys
from pathlib import Path
from analog_gauge_reader.pipeline_v6 import process_image
from config import DETECTION_MODEL_PATH, KEY_POINT_MODEL_PATH, SEGMENTATION_MODEL_PATH, RESULT_PATH, CONFIG_CALIBRATION_PATH

# params:
# imageName is the name of image without .jpg (name = f"{index}_{timestamp}")
# imagePath is the absolute path of the original image
# returns:
# data object converted from .json file
def readImage(imageName, rgd_img, camera_index, camera_details):
    data = runModel(imageName, rgd_img, camera_index, camera_details)
    # data = retrieveResult(imageName)
    return data


def runModel(imageName, rgd_img, camera_index, camera_details, debug=True, eval_mode=True):
    """
    Run the gauge reading model directly on an OpenCV frame (NumPy array).

    Args:
        rgd_img (np.ndarray): Raw OpenCV RGB frame
        run_path (str): Path to save logs/results/plots
        debug (bool): Enable debugging plots
        eval_mode (bool): Enable full result output
    """
    print("Running model on in-memory frame...")
    base_path = RESULT_PATH
    os.makedirs(base_path, exist_ok=True)
    run_path = os.path.join(base_path, imageName)
    # detection_model_path = "models/gauge_detection_model.pt"
    # key_point_model_path = "models/key_point_model.pt"
    # segmentation_model_path = "models/segmentation_model.pt"

    # Ensure run path exists
    os.makedirs(run_path, exist_ok=True)

    # Convert OpenCV BGR to RGB, as expected by process_image()
    #image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


    start_marking = camera_details["start_marking"]
    end_marking = camera_details["end_marking"]
    unit = camera_details["unit"]
    # index = (int)(imageName[0])
    # with open(CONFIG_CALIBRATION_PATH) as f:
    #     data = json.load(f)
    #     for obj in data:
    #         if obj["index"] == index:
    #             start_marking = obj["start_marking"]
    #             end_marking = obj["end_marking"]
    #             unit = obj["unit"]
    #             break
    # Run the full gauge-reading pipeline
    result = process_image(
        image=rgd_img,
        detection_model_path=DETECTION_MODEL_PATH,
        key_point_model_path=KEY_POINT_MODEL_PATH,
        segmentation_model_path=SEGMENTATION_MODEL_PATH,
        run_path=run_path,
        debug=debug,
        eval_mode=eval_mode,
        start_marking=start_marking,
        end_marking=end_marking,
        unit=unit,
        image_is_raw=False  # It's a NumPy array already
    )
    return result  # dict with {'value': ..., 'unit': ...}

# def runModel_original(imagePath):
#     print(f"Running model on {imagePath}")
#     # update args below to match the actual commands for cv model
#     args = [
#         "python",
#         "pipeline_v2.py",
#         "--detection_model",
#         "models/gauge_detection_model.pt",
#         "--segmentation_model",
#         "models/best.pt",
#         "--key_point_model",
#         "models/key_point_model.pt",
#         "--base_path",
#         RESULT_PATH,
#         "--input",
#         str(imagePath)
#     ]
#     env = os.environ.copy()
#     subprocess.run(
#         args,
#         cwd=os.path.expanduser("~/Desktop/project_3301/analog_gauge_reader"),
#         env=env
#     )

def retrieveResult(imageName):
    result_path = os.path.join(RESULT_PATH, f"{imageName}", "result.json")
    print(f"Retrieving result from {result_path}")
    count = 0
    while (count < 5):
        try:
            import json
            with open(result_path) as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            print(f"Result file not found: {result_path}")
            count += 1
            time.sleep(2)
        except Exception as e:
            print(f"Error reading result file: {e}")
            return None

