#!/usr/bin/env python3
import os
import re
import statistics
import numpy as np
from datetime import datetime

LOG_DIR = "logs"
STATS_DIR = "stats"
os.makedirs(STATS_DIR, exist_ok=True)

def summarize(values, label, units=""):
    """Compute count, mean, quartiles, and IQR summary text."""
    if not values:
        return f"\n=== {label} ===\nNo data found.\n"
    q25, q50, q75 = np.percentile(values, [25, 50, 75])
    iqr = q75 - q25
    lines = [
        f"\n=== {label} ===",
        f"Count : {len(values)}",
        f"Mean  : {statistics.mean(values):.4f}{units}",
        f"Min   : {min(values):.4f}{units}",
        f"25%   : {q25:.4f}{units}",
        f"50%   : {q50:.4f}{units}",
        f"75%   : {q75:.4f}{units}",
        f"Max   : {max(values):.4f}{units}",
        f"IQR   : {iqr:.4f}{units}",
    ]
    return "\n".join(lines) + "\n"

def analyse_log(file_path):
    """Parse a single log file and extract key metrics."""
    data = {
        "bandwidth": [],
        "width": [],
        "height": [],
        "fps": [],
        "elapsed": [],
        "reading": [],
        "camera_name": None,
    }

    with open(file_path) as f:
        for line in f:
            # Camera name
            cam_match = re.search(r"Cam(\d+)", line)
            if cam_match and not data["camera_name"]:
                data["camera_name"] = cam_match.group(1)

            # Resolution
            wh_match = re.search(r"(\d+)x(\d+)", line)
            if wh_match:
                data["width"].append(int(wh_match.group(1)))
                data["height"].append(int(wh_match.group(2)))

            # Bandwidth (Mbps)
            bw_match = re.search(r"stream:\s*([\d\.]+)\s*Mbps", line)
            if bw_match:
                data["bandwidth"].append(float(bw_match.group(1)))

            # FPS
            fps_match = re.search(r"Frames per second:\s*([\d\.]+)", line)
            if fps_match:
                data["fps"].append(float(fps_match.group(1)))

            # Time elapsed
            elapsed_match = re.search(r"time elapsed:\s*([\d\.]+)\s*seconds", line)
            if elapsed_match:
                data["elapsed"].append(float(elapsed_match.group(1)))

            # Final reading
            reading_match = re.search(r"Final reading is:\s*([-+]?\d*\.?\d+)", line)
            if reading_match:
                data["reading"].append(float(reading_match.group(1)))

    return data

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze camera bandwidth, FPS, elapsed time, and readings from logs")
    parser.add_argument("logfile", help="Log file name (inside logs/)")
    args = parser.parse_args()

    file_path = os.path.join(LOG_DIR, args.logfile)
    if not os.path.exists(file_path):
        print(f"❌ Log file not found: {file_path}")
        return

    data = analyse_log(file_path)
    if not data["bandwidth"]:
        print("⚠️ No bandwidth data found in log.")
        return

    # Estimate supported cameras (USB bandwidth model)
    max_mbps = max(data["bandwidth"])
    min_mbps = min(data["bandwidth"])
    min_supported = int(240 // max_mbps)
    max_supported = int(320 // min_mbps)

    # Build report
    report = []
    report.append("=== Camera Bandwidth, FPS & Reading Analysis ===")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Source: {args.logfile}")

    report.append(summarize(data["bandwidth"], "Bandwidth (Mbps)", " Mbps"))
    report.append(summarize(data["fps"], "Frame Rate (FPS)", " FPS"))
    report.append(summarize(data["elapsed"], "Time Elapsed per Cycle", " s"))
    report.append(summarize(data["reading"], "Final Reading", " kg/cm³"))
    report.append(summarize(data["width"], "Frame Width", " px"))
    report.append(summarize(data["height"], "Frame Height", " px"))
    report.append(f"\nEstimated supported cameras: {min_supported}–{max_supported}")

    # Save report
    output_file = os.path.join(
        STATS_DIR,
        f"{os.path.splitext(args.logfile)[0]}_bandwidth_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
    )
    with open(output_file, "w") as f:
        f.write("\n".join(report))

    print("\n".join(report))
    print(f"\n✅ Summary saved to: {output_file}")

if __name__ == "__main__":
    main()
