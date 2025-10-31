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
from config import verify_model_files, CAPTURE_INTERVAL
from capture_image import captureImage
from read_image import runModel
from send_data import sendData


# === Logging helpers ===
def redirect_camera_output(cam_index, cam_name, width, height):
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/camera_output_{cam_index}_{cam_name}_{width}_{height}.log"
    f = open(log_file, "a")
    sys.stdout = f
    sys.stderr = f
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    print(f"[{datetime.now()}] Logging started for camera {cam_index}_{cam_name}_{width}_{height}")


def redirect_subprocess_output(cam_index, cam_name, width, height):
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/subprocess_output_{cam_index}_{cam_name}_{width}_{height}.log"
    f = open(log_file, "a")
    sys.stdout = f
    sys.stderr = f
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    print(f"[{datetime.now()}] Logging started for postCapture of camera {cam_index}_{cam_name}")


# === Frame info ===
def get_mjpg_frame_info(dev_path):
    cmd = ["v4l2-ctl", f"--device={dev_path}", "--get-fmt-video", "--get-parm"]
    out = subprocess.check_output(cmd, text=True)
    print(out)
    w = int(re.search(r"Width/Height\s*:\s*(\d+)/(\d+)", out).group(1))
    h = int(re.search(r"Width/Height\s*:\s*(\d+)/(\d+)", out).group(2))
    size = int(re.search(r"Size Image\s*:\s*(\d+)", out).group(1))
    fourcc = re.search(r"Pixel Format\s*:\s*'(\w+)'", out).group(1)
    return w, h, size, fourcc


# === Post-processing ===
def postCapture(name, frame, cam_index, cam_details, width, height):
    redirect_subprocess_output(cam_index, cam_details["camera_name"], width, height)
    try:
        print("Running model inference...")
        data = runModel(name, frame, cam_index, cam_details)
        if not data:
            print("No data returned from model")
            return
        payload = {
            "oilfield": cam_details["oilfield_name"],
            "wellhead": cam_details["wellhead_name"],
            "gauge": cam_details["gauge_name"],
            "reading": data["value"],
            "unit": data["unit"],
            "sensor_name": cam_details["sensor_name"],
        }
        sendData(payload)
        print(f"✅ Data processed for {cam_index}_{cam_details['camera_name']}")
    except Exception as e:
        print(f"Error in postCapture: {e}")


# === Capture loop per camera (sequential) ===
def fullProcess(cam_index, cam_details, interval, width, height, duration):
    redirect_camera_output(cam_index, cam_details["camera_name"], width, height)
    print(f"Starting full process for camera {cam_index} ({width}x{height})")

    cap = cv2.VideoCapture(cam_index)
    time.sleep(1)
    if not cap.isOpened():
        print(f"Failed to open camera {cam_index}")
        return

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    dev_path = f"/dev/video{cam_index}"
    start_time = time.time()

    try:
        
        t0 = time.time()
        name, frame = captureImage(cap, cam_index)
        if frame is None:
            print(f"[{datetime.now()}] Camera {cam_index}: Failed to capture frame.")
            time.sleep(2)
            return

        frame_time = time.time() - t0
        width_now, height_now, _, fourcc = get_mjpg_frame_info(dev_path)
        success, encoded = cv2.imencode(".jpg", frame)
        bandwidth = (len(encoded) * 8 / 1e6) / frame_time if success else 0

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Cam{cam_index}, {width_now}x{height_now} {fourcc} stream: "
                f"{bandwidth:.2f} Mbps ({len(encoded)/1024:.1f} KB) time={frame_time:.3f}s")

        postCapture(name, frame, cam_index, cam_details, width, height)
        elapsed = time.time() - t0
        print(f"time elapsed: {elapsed:.2f} seconds")
        #time.sleep(max(0, interval - elapsed))
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"Camera {cam_index} stopped.")


# === Main (Sequential across cameras) ===
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cameras", nargs="+", type=int, required=True, help="Camera indices (e.g. 0 2 4)")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--total_duration", type=int, default=480, help="Total run time (s) across all cameras")
    parser.add_argument("--interval", type=float, default=CAPTURE_INTERVAL)
    args = parser.parse_args()

    if not verify_model_files():
        print("Missing model files.")
        return

    with open("config_calibration.json") as f:
        cam_cfg = {int(k): v for k, v in json.load(f).items()}

    for c in args.cameras:
        if c not in cam_cfg:
            print(f"Camera {c} not found in config.")
            return

    os.makedirs("logs", exist_ok=True)
    tag = "_".join(map(str, args.cameras))
    power_log = f"logs/tegrastats_cam{tag}_{args.width}x{args.height}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    print(f"Started tegrastats logging → {power_log}")

    # Each camera gets an equal slice of total time
    per_cam_duration = args.total_duration / len(args.cameras)
    print(f"Total {args.total_duration}s → {per_cam_duration:.1f}s per camera")
    start_time = time.time()
    try:
        while time.time() - start_time < per_cam_duration:
            for cam in args.cameras:
                print(f"\n=== Starting sequential run for camera {cam} ===")
                tegrastats = subprocess.Popen(
                    ["tegrastats", "--interval", "1000"],
                    stdout=open(power_log, "a"),
                    stderr=subprocess.STDOUT,
                )
                try:
                    fullProcess(cam, cam_cfg[cam], args.interval, args.width, args.height, per_cam_duration)
                finally:
                    tegrastats.terminate()
                    print(f"Stopped tegrastats logging for camera {cam}")
                    print("----------------------------------------------------")
                    time.sleep(5)
    except KeyboardInterrupt:
        print("Main interrupted. Terminating...")
    finally:
        print("All cameras finished.")


if __name__ == "__main__":
    main()
