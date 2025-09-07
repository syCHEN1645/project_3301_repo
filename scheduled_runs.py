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
from datetime import datetime

from pathlib import Path
from config import verify_model_files, CAPTURE_INTERVAL
from multiprocessing import Pool

# Add project root to sys.path for absolute imports
# sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def redirect_camera_output(cam_index):
    #now = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/camera_output_{cam_index}.log"
    os.makedirs("logs", exist_ok=True)
    log_file = open(log_filename, "a")
    sys.stdout = log_file
    sys.stderr = log_file
    print(f"[{datetime.now()}] Logging started for camera {cam_index}")

def redirect_subprocess_output(cam_index):
    #now = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/subprocess_output_{cam_index}.log"
    os.makedirs("logs", exist_ok=True)
    log_file = open(log_filename, "a")
    sys.stdout = log_file
    sys.stderr = log_file
    print(f"[{datetime.now()}] Logging started for postCapture of camera {cam_index}")


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


def postCapture(name, rgd_img, index):
    #redirect_subprocess_output(index)

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


def fullProcess(index):
    #redirect_camera_output(index)
    
    print(f"Start running full process for camera {index}")
    # capture must be declared within the process
    capture = cv2.VideoCapture(index)
    if not capture.isOpened():
        print(f"Failed to open camera {index}")
        return

    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    capture.set(cv2.CAP_PROP_FPS, 5)

    try:
        while True:
            start = time.time()
            name, frame = captureImage(capture, index)
            if frame is not None:
                postCapture(name, frame, index)
                print(f"[{datetime.now()}] Camera {index}: Data processed successfully")

            else:
                print(f"[{datetime.now()}] Camera {index}: Failed to capture image")
                time.sleep(2)  # <- Give the USB bus and camera time to recover
                continue


            elapsed = time.time() - start
            #sleep_time = max(0, 40 - elapsed)
            #print(f"[{datetime.now()}] Camera {index}: Sleeping {sleep_time:.1f}s")
            time.sleep(30)

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
        
        processes = []
        for index in activeCams:
            p = Process(target=fullProcess, args=(index,))
            p.start()
            processes.append(p)

        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            print("Main process interrupted. Terminating cameras...")
            for p in processes:
                p.terminate()


        # print(activeCams)
        # with Pool(processes=len(activeCams)) as pool:
        #     pool.map(fullProcess, activeCams)


        # For now, just run the first camera (you can extend this for multiple cameras)
        #fullProcess(activeCams[0], interval)
        
    except KeyboardInterrupt:
        print("Stop upon keyboard interrupt")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__=="__main__":
    main()