from capture_image import captureImage
from read_image import readImage, runModel
from send_data import sendData
from multiprocessing import Process
import time
import sys
import os
import cv2
from datetime import datetime
import json
from config import verify_model_files, CAPTURE_INTERVAL
import random
import fcntl, struct
import subprocess, re

# Add project root to sys.path for absolute imports
# sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def redirect_camera_output(cam_index, camera_name):
    #now = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/camera_output_{cam_index}_{camera_name}_{datetime.now().strftime('%Y%m%d_%H')}.log"
    os.makedirs("logs", exist_ok=True)
    log_file = open(log_filename, "a")
    sys.stdout = log_file
    sys.stderr = log_file
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    print(f"[{datetime.now()}] Logging started for camera {cam_index}_{camera_name}")

def redirect_subprocess_output(cam_index, camera_name):
    #now = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/subprocess_output_{cam_index}_{camera_name}_{datetime.now().strftime('%Y%m%d_%H')}.log"
    os.makedirs("logs", exist_ok=True)
    log_file = open(log_filename, "a")
    sys.stdout = log_file
    sys.stderr = log_file
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    print(f"[{datetime.now()}] Logging started for postCapture of camera {cam_index}_{camera_name}")


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


def postCapture(name, rgd_img, camera_index, camera_details):
    redirect_subprocess_output(camera_index, {camera_details['camera_name']})

    try:
        print("reading image")
        # data = readImage(name, rgd_img, camera_index, camera_details)
        data = runModel(name, rgd_img, camera_index, camera_details)
        print(f"Data inferred from {camera_index}_{camera_details['camera_name']}: {data}")
        if data is None:
            print("No data returned from image processing")
            return
            
        data_full = {
            "oilfield" : camera_details["oilfield_name"],
            "wellhead" : camera_details["wellhead_name"],
            "gauge" : camera_details["gauge_name"],
            "reading" : data["value"],
            "unit" : data["unit"],
            "sensor_name" : camera_details["sensor_name"]
        }
        ack = sendData(data_full)  # Wrap in list as expected by sendData
        # if ack == 2:
        #     print("CV failed to read, try again later")
        #     return
            
        # count = 0
        # while ack != 1 and count < 20:
        #     time.sleep(3)
        #     count += 1
        #     ack = sendData(data)
            
        # print(f"Data processing complete. Acknowledgment: {ack}")
        print(f"Data processing complete for {camera_index}_{camera_details['camera_name']}")
        
    except Exception as e:
        print(f"Error in postCapture: {e}")

    # uncomment below later
    # if (ack == 1):
    #    deleteData(name, path)


# def get_mjpg_frame_info(dev_path):
#     """
#     Query the V4L2 driver for current MJPG stream info:
#     returns (width, height, size_bytes, fourcc_string)
#     """
#     # Define V4L2 constants (avoid external deps)
#     VIDIOC_G_FMT = 0xC0CC5604
#     V4L2_BUF_TYPE_VIDEO_CAPTURE = 1

#     # Structure of v4l2_format (simplified)
#     fmt = struct.pack("I", V4L2_BUF_TYPE_VIDEO_CAPTURE) + bytes(200)
#     fd = os.open(dev_path, os.O_RDWR)
#     try:
#         fmt = fcntl.ioctl(fd, VIDIOC_G_FMT, fmt)
#         # Offsets are from the v4l2_format struct (32-bit kernel ABI)
#         pix = fmt[8:8+200]
#         width, height, pixelformat, field, bytesperline, \
#             sizeimage, colorspace = struct.unpack_from("II4sIIII", pix)
#         fourcc = pixelformat.decode(errors='ignore')
#         return width, height, sizeimage, fourcc
#     finally:
#         os.close(fd)



def get_mjpg_frame_info(dev_path):
    cmd = ["v4l2-ctl", f"--device={dev_path}", "--get-fmt-video", "--get-parm"]
    # cmd = ["v4l2-ctl", f"--device={dev_path}", "--all"]
    out = subprocess.check_output(cmd, text=True)
    print(out.strip())
    w = int(re.search(r"Width/Height\s*:\s*(\d+)/(\d+)", out).group(1))
    h = int(re.search(r"Width/Height\s*:\s*(\d+)/(\d+)", out).group(2))
    size = int(re.search(r"Size Image\s*:\s*(\d+)", out).group(1))
    fourcc = re.search(r"Pixel Format\s*:\s*'(\w+)'", out).group(1)
    return w, h, size, fourcc



def fullProcess(camera_index, camera_details, interval):
    redirect_camera_output(camera_index, {camera_details['camera_name']})

    # camera_details in a dict with the format {camera_index : {configuration key value pairs}}
    # 
    
    print(f"Start running full process for camera {camera_index}")
    # capture must be declared within the process
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        print(f"Failed to open camera {camera_index}")
        return

    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    # # capture.set(cv2.CAP_PROP_FRAME_WIDTH, 680)
    # # capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 420)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
    # capture.set(cv2.CAP_PROP_FPS, 5)

    dev_path = f"/dev/video{camera_index}"
    # width, height, mjpg_bytes, fourcc = get_mjpg_frame_info(dev_path)
    # print(f"[Cam{camera_index}] {width}x{height} {fourcc} stream, "
    #     f"driver buffer size ≈ {mjpg_bytes/1024:.1f} KB")


    show_feed = True

    try:
        while True:
            start = time.time()
            name, frame = captureImage(capture, camera_index)
            if frame is not None:
                frame_time_s = time.time() - start        # elapsed capture time
                width, height, mjpg_bytes, fourcc = get_mjpg_frame_info(dev_path)
                success, encoded = cv2.imencode('.jpg', frame)
                if success:
                    bandwidth_mbps = (len(encoded) * 8 / 1e6) / frame_time_s
                else:
                    bandwidth_mbps = 0
                    print("Error in encoding frame")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Cam{camera_index}, {width}x{height} {fourcc} stream: {bandwidth_mbps:.2f} Mbps (MJPG ≈ {len(encoded)/1024:.1f} KB) time = {frame_time_s}")

                # frame_time_s = time.time() - start        # elapsed capture time
                # success, encoded = cv2.imencode('.jpg', frame)
                # if success:
                #     bandwidth_mbps = (len(encoded) * 8 / 1e6) / frame_time_s
                # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # print(f"[{timestamp}] Cam{camera_index}: {bandwidth_mbps:.2f} Mbps, size: {(len(encoded) * 8 / 1e6)} Mb")

                # frame_time_s = time.time() - start        # elapsed capture time
                # bandwidth_mbps = (len(frame) * 8 / 1e6) / frame_time_s
                # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # print(f"[{timestamp}] Cam{camera_index}: {bandwidth_mbps:.2f} Mbps, size: {(len(frame) * 8 / 1e6)} Mb")

                # # --- NEW: show the frame ---
                # if show_feed:
                #     preview = frame.copy()
                #     cv2.putText(preview, f"Cam {camera_index}", (10, 30),
                #                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                #     cv2.imshow(f"Camera {camera_index}", preview)
                #     # Press 'q' to close this display
                #     if cv2.waitKey(1) & 0xFF == ord('q'):
                #         show_feed = False
                #         cv2.destroyWindow(f"Camera {camera_index}")
                postCapture(name, frame, camera_index, camera_details)
                print(f"[{datetime.now()}] Camera {camera_index}_{camera_details['camera_name']}: Data processed successfully")

            else:
                print(f"[{datetime.now()}] Camera {camera_index}_{camera_details['camera_name']}: Failed to capture image")
                time.sleep(2)  # <- Give the USB bus and camera time to recover
                continue


            elapsed = time.time() - start
            sleep_time = max(0, interval - elapsed)
            print(f"[{datetime.now()}] Camera {camera_index}_{camera_details['camera_name']}: Sleeping {sleep_time:.1f}s")
            # time.sleep(30)

    except KeyboardInterrupt:
        print(f"Stopping camera {camera_index}_{camera_details['camera_name']} processing")
    finally:
        capture.release()
        cv2.destroyAllWindows()


def main():
    if not verify_model_files():
        print("Please ensure all model files are in the correct location")
        return
        
    interval = CAPTURE_INTERVAL
    if len(sys.argv) == 2:
        interval = int(sys.argv[1])

    camera_dict = {}
    with open("config_calibration.json", "r") as f:
        camera_dict_raw = json.load(f)
        camera_dict = {int(k) : v for k, v in camera_dict_raw.items()}
    
    if not camera_dict:
        print("Error loading the camera configuration file.")
        exit(1)

    try:
        activeCams = scanActiveCameras()
        if not activeCams:
            print("No active cameras found")
            return
        
        processes = []
        for camera_index in activeCams:
            if camera_index == 3: # included for testing purposes
                p = Process(target=fullProcess, args=(camera_index, camera_dict[camera_index], interval))
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