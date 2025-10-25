#!/usr/bin/env python3
import argparse
import os
import sys
import time
import cv2
import json
import subprocess
import re
from datetime import datetime
from multiprocessing import Process
from config import verify_model_files, CAPTURE_INTERVAL
from capture_image import captureImage
from read_image import runModel
from send_data import sendData


# === Logging helpers ===
def redirect_camera_output(cam_index, camera_name):
    os.makedirs("logs", exist_ok=True)
    log_filename = f"logs/camera_output_{cam_index}_{camera_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file = open(log_filename, "a")
    sys.stdout = log_file
    sys.stderr = log_file
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    print(f"[{datetime.now()}] Logging started for camera {cam_index}_{camera_name}")


def redirect_subprocess_output(cam_index, camera_name):
    os.makedirs("logs", exist_ok=True)
    log_filename = f"logs/subprocess_output_{cam_index}_{camera_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file = open(log_filename, "a")
    sys.stdout = log_file
    sys.stderr = log_file
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    print(f"[{datetime.now()}] Logging started for postCapture of camera {cam_index}_{camera_name}")


# === Camera scanning ===
def scanActiveCameras():
    print("Scanning for active cameras...")
    active = []
    for name in os.listdir("/dev"):
        if name.startswith("video") and name[5:].isdigit():
            idx = int(name[5:])
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                active.append(idx)
                print(f"✅ Camera {idx} active")
            cap.release()
    print(f"Detected active cameras: {active}")
    return active


# === Frame info ===
def get_mjpg_frame_info(dev_path):
    cmd = ["v4l2-ctl", f"--device={dev_path}", "--get-fmt-video", "--get-parm"]
    out = subprocess.check_output(cmd, text=True)
    w = int(re.search(r"Width/Height\s*:\s*(\d+)/(\d+)", out).group(1))
    h = int(re.search(r"Width/Height\s*:\s*(\d+)/(\d+)", out).group(2))
    size = int(re.search(r"Size Image\s*:\s*(\d+)", out).group(1))
    fourcc = re.search(r"Pixel Format\s*:\s*'(\w+)'", out).group(1)
    return w, h, size, fourcc


# === Post-processing ===
def postCapture(name, frame, camera_index, camera_details):
    redirect_subprocess_output(camera_index, camera_details['camera_name'])
    try:
        print("Running model inference...")
        data = runModel(name, frame, camera_index, camera_details)
        if not data:
            print("No data returned from model")
            return
        data_full = {
            "oilfield": camera_details["oilfield_name"],
            "wellhead": camera_details["wellhead_name"],
            "gauge": camera_details["gauge_name"],
            "reading": data["value"],
            "unit": data["unit"],
            "sensor_name": camera_details["sensor_name"]
        }
        sendData(data_full)
        print(f"✅ Data processed for {camera_index}_{camera_details['camera_name']}")
    except Exception as e:
        print(f"Error in postCapture: {e}")


# === Main capture loop ===
def fullProcess(camera_index, camera_details, interval, width, height, duration):
    redirect_camera_output(camera_index, camera_details['camera_name'])
    print(f"Starting full process for camera {camera_index} ({width}x{height})")

    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        print(f"Failed to open camera {camera_index}")
        return

    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    dev_path = f"/dev/video{camera_index}"
    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            t0 = time.time()
            name, frame = captureImage(capture, camera_index)
            if frame is None:
                print(f"[{datetime.now()}] Camera {camera_index}: Failed to capture frame.")
                time.sleep(2)
                continue

            frame_time = time.time() - t0
            width_now, height_now, mjpg_bytes, fourcc = get_mjpg_frame_info(dev_path)
            success, encoded = cv2.imencode('.jpg', frame)
            if success:
                bandwidth = (len(encoded) * 8 / 1e6) / frame_time
            else:
                bandwidth = 0

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Cam{camera_index}, {width_now}x{height_now} {fourcc} stream: "
                  f"{bandwidth:.2f} Mbps (MJPG ≈ {len(encoded)/1024:.1f} KB) time={frame_time:.3f}s")

            postCapture(name, frame, camera_index, camera_details)
            elapsed = time.time() - t0
            sleep_time = max(0, interval - elapsed)
            print(f"[{datetime.now()}] Sleeping {sleep_time:.2f}s\n")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        capture.release()
        cv2.destroyAllWindows()
        print(f"Camera {camera_index} stopped.")


def main():
    parser = argparse.ArgumentParser(description="Scheduled Jetson Camera Pipeline")
    parser.add_argument("--camera", type=int, required=True, help="Camera index to use")
    parser.add_argument("--width", type=int, required=True, help="Frame width")
    parser.add_argument("--height", type=int, required=True, help="Frame height")
    parser.add_argument("--duration", type=int, default=480, help="Duration in seconds (default 480s = 8 min)")
    parser.add_argument("--interval", type=float, default=CAPTURE_INTERVAL, help="Capture interval (s)")
    args = parser.parse_args()

    if not verify_model_files():
        print("Missing model files.")
        return

    with open("config_calibration.json") as f:
        camera_config = {int(k): v for k, v in json.load(f).items()}

    if args.camera not in camera_config:
        print(f"Camera {args.camera} not found in config.")
        return

    os.makedirs("logs", exist_ok=True)
    power_log = f"logs/tegrastats_cam{args.camera}_{args.width}x{args.height}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    tegrastats_proc = subprocess.Popen(["tegrastats", "--interval", "1000"],
                                       stdout=open(power_log, "w"),
                                       stderr=subprocess.STDOUT)
    print(f"Started tegrastats logging -> {power_log}")

    try:
        p = Process(target=fullProcess,
                    args=(args.camera, camera_config[args.camera],
                          args.interval, args.width, args.height, args.duration))
        p.start()
        p.join()
    except KeyboardInterrupt:
        print("Interrupted main process.")
    finally:
        tegrastats_proc.terminate()
        print("Stopped tegrastats logging.")


if __name__ == "__main__":
    main()
