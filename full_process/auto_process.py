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


def postCapture(name, rgd_img):
    try:
        data = readImage(name, rgd_img)
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


def fullProcess(index, interval):
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
                p = Process(target=postCapture, args=(name, frame))
                p.daemon = True  # Dies when main process dies
                p.start()
                # Note: Not joining process to avoid blocking
                
            time.sleep(interval)
            print(f"Break for {interval} seconds ...")
            
    except KeyboardInterrupt:
        print(f"Stopping camera {index} processing")
    finally:
        capture.release()


def main():
    if not verify_model_files():
        print("Please ensure all model files are in the correct location")
        return
        
    interval = CAPTURE_INTERVAL
    if len(sys.argv) == 2:
        interval = int(sys.argv[1])
        
    try:
        activeCams = scanActiveCameras()
        if not activeCams:
            print("No active cameras found")
            return
            
        # For now, just run the first camera (you can extend this for multiple cameras)
        fullProcess(activeCams[0], interval)
        
    except KeyboardInterrupt:
        print("Stop upon keyboard interrupt")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__=="__main__":
    main()
