#import argparse
import json

def main():
    # todo:
    # scan cameras
    # clibrate each camera
    # possibly show picture from cameras to confirm

    # todo: get a proper list of cam names
    camera_name_list = ["cam 0"]

    # todo: loop this for each cam
    name = camera_name_list[0]
    print(f"Key in start point value for {name}: ")
    start_marking = (float)(input())
    print(f"Key in end point value for {name}: ")
    end_marking = (float)(input())
    print(f"Key in unit for {name}: ")
    unit = (str)(input())

    config = [{
        "name": name,
        "start_marking": start_marking,
        "end_marking": end_marking,
        "unit": unit
        }]

    # write these info into config file
    with open("config-calibration.py", "w") as f:
        json.dump(config)

