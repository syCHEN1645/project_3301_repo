from capture_image import captureImage
from read_image import readImage
from send_data import sendData, deleteData
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Process, Queue
from PIL import Image
import time
import sys
import os
import cv2

import sys
from pathlib import Path
from config import verify_model_files, CAPTURE_INTERVAL

# Add project root to sys.path for absolute imports
# sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def scanActiveCameras():
    print("Scanning for active cameras")
    activeCams = []
    # 0 maps to /dev/video0
    # 1 maps to /dev/video1
    # and so on
    for name in os.listdir("/dev"):
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


def postCapture(name, rgd_img, start_marking, end_marking):
    try:
        data = readImage(name, rgd_img, start_marking, end_marking)
        if data is None:
            print("No data returned from image processing")
            return
            
        ack = sendData(data)  # Wrap in list as expected by sendData
        if ack == 2:
            print("CV failed to read, try again later")
            return
            
        count = 0
        while ack != 1 and count < 20:
            time.sleep(3)
            count += 1
            ack = sendData(data)
            
        print(f"Data processing complete. Acknowledgment: {ack}")
        
    except Exception as e:
        print(f"Error in postCapture: {e}")

    # uncomment below later
    # if (ack == 1):
    #    deleteData(name, path)


def fullProcess(index, interval, start_marking, end_marking):
    print(f"Start running full process for camera {index}")
    # capture must be declared within the process
    capture = cv2.VideoCapture(index)
    if not capture.isOpened():
        print(f"Failed to open camera {index}")
        return

    try:
        while True:
            name, frame = captureImage(capture, index)
            if frame is not None:
                p = Process(target=postCapture, args=(name, frame, start_marking, end_marking))
                p.daemon = True  # Dies when main process dies
                p.start()
                # Note: Not joining process to avoid blocking
                
            time.sleep(interval)
            print(f"Break for {interval} seconds ...")
            
    except KeyboardInterrupt:
        print(f"Stopping camera {index} processing")
    finally:
        capture.release()
    # while True:
    #     name, rgd_img = captureImage(capture, index)
    #     #ret, frame = capture.read()
    #     #rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #     #pil_img = Image.fromarray(rgb_img)
    #     postCapture(name, rgd_img)
    #     # p = Process(target=postCapture, args=(name, path))
    #     # p.start()
    #     # todo: process p is not joined, may become zombie
    #     time.sleep(interval)
    #     print("Break for 10 seconds ...")


def main():
    if not verify_model_files():
        print("Please ensure all model files are in the correct location")
        return
        
    interval = CAPTURE_INTERVAL
    if len(sys.argv) == 4:
        interval = int(sys.argv[1])
        start_marking = float(sys.argv[2])
        end_marking = float(sys.argv[3])
        
    try:
        activeCams = scanActiveCameras()
        if not activeCams:
            print("No active cameras found")
            return
            
        # For now, just run the first camera (you can extend this for multiple cameras)
        fullProcess(activeCams[0], interval, start_marking, end_marking)
        
    except KeyboardInterrupt:
        print("Stop upon keyboard interrupt")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    # # set time interval length
    # interval = 20
    # if (len(sys.argv) == 2):
    #     interval = int(sys.argv[1])

    # try:
    #     activeCams = scanActiveCameras()
    #     # run active cameras in parallel
    #     # each camera submits a process
    #     # jetson orin has 12? cores
    #     fullProcess(activeCams[0], interval)
    #     # with ProcessPoolExecutor() as executor:
    #     #     futures = [executor.submit(fullProcess, index, interval) for index in activeCams]
    #     #     for future in futures:
    #     #         future.result()

    # except KeyboardInterrupt:
    #     print("Stop upon keyboard interrupt")
    #     exit()


if __name__=="__main__":
    main()
