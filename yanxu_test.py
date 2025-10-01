import subprocess
import re
import cv2
import os

def scanActiveCameras():
    print("Scanning for active cameras")
    activeCams = []
    # 0 maps to /dev/video0
    # 1 maps to /dev/video1
    # and so on
    for name in os.listdir("/dev"):
        #print(name)
        ret = isActiveCamera(name)
        if (ret != -1):
            activeCams.append(ret)
    print("Finished scanning for cameras")
    print(f"These cameras {activeCams} are found active")
    return activeCams


def isActiveCamera(name):
    if (name.startswith("video")):
        name = name.replace("video", "")
        if (name.isdigit()):
            index = int(name)
            try:
                capture = cv2.VideoCapture(index)
                if (capture.isOpened()):
                    print(f"Camera {index} is found active")
                    capture.release()
                    return index
                capture.release()
                print(f"Camera {index} is not active")
            except Exception as e:
                print(f"Camera {index} is not accessible")
        else:
            print(f"Invalid camera name skipped: {name}")
    return -1


def list_video_devices():
    output = subprocess.check_output(['v4l2-ctl', '--list-devices'], text=True)

    camera_info = []
    lines = output.strip().split('\n')

    i = 0
    while i < len(lines):
        if not lines[i].startswith('\t') and lines[i].strip() != "":
            camera_name = lines[i].strip()
            i += 1
            device_indexs = []
            while i < len(lines) and lines[i].startswith('\t'):
                path = lines[i].strip()
                if '/dev/video' in path:
                    camera_path = path.replace("/dev/", "")
                    print(camera_path)
                    ret = isActiveCamera(camera_path)
                    if (ret != -1):
                        device_indexs.append(ret)                   
                i += 1
            print(f"These cameras {device_indexs} are found active")
            camera_info.append({
                'name': camera_name,
                'video_devs': device_indexs
            })
        else:
            i += 1
    return camera_info

# Usage:
cameras = list_video_devices()

# activecams = scanActiveCameras()
# print(activecams)


print(cameras)
#for cam in cameras:
    #print(f"Camera: {cam['name']}")
    #print(f"Video Devices: {cam['video_devs']}")
