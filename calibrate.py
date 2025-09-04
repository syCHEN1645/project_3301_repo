import json
import os

from config import CONFIG_CALIBRATION_PATH

def main():
    # todo:
    # scan cameras
    # clibrate each camera
    # possibly show picture from cameras to confirm

    # todo: get a proper list of cam names
    camera_index_list = [1]

    # todo: loop this for each cam
    index = camera_index_list[0]
    print(f"Key in start point value for camera {index}: ")
    start_marking = (float)(input())
    print(f"Key in end point value for camera {index}: ")
    end_marking = (float)(input())
    print(f"Key in unit for camera {index}: ")
    unit = (str)(input())

    config = [
        {
        "index": index,
        "start_marking": start_marking,
        "end_marking": end_marking,
        "unit": unit
        }
        ]

    # write all info (from all cameras) into config file
    with open(CONFIG_CALIBRATION_PATH, "w") as f:
        json.dump(config, f)
        print("Calibration is saved")

if __name__ == "__main__":
    main()
