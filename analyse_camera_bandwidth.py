import re
import numpy as np
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import argparse
import math

# === REGEX PATTERN ===
camera_line = re.compile(
    r"Cam(\d+),\s*(\d+)x(\d+)\s+\S+\s+stream:\s*([\d\.]+)\s*Mbps"
)

def parse_log(filepath):
    """Extract camera bandwidth info from a single log file."""
    data = defaultdict(list)
    with open(filepath, "r") as f:
        for line in f:
            m = camera_line.search(line)
            if m:
                cam_id = m.group(1)
                width, height = int(m.group(2)), int(m.group(3))
                mbps = float(m.group(4))
                key = f"Camera {cam_id} ({width}x{height})"
                data[key].append(mbps)
    return data

def summarize(values):
    """Compute key statistics for a list of values."""
    arr = np.array(values)
    q1, q2, q3 = np.percentile(arr, [25, 50, 75])
    stats = {
        "count": len(arr),
        "mean": np.mean(arr),
        "min": np.min(arr),
        "q1": q1,
        "median": q2,
        "q3": q3,
        "max": np.max(arr),
        "iqr": q3 - q1,
    }

    # === Camera support estimation (floored integers) ===
    stats["min_supported"] = math.floor(240 / stats["max"]) if stats["max"] > 0 else 0
    stats["max_supported"] = math.floor(320 / stats["min"]) if stats["min"] > 0 else 0

    return stats

def summarize_to_text(stats):
    """Format one stats dictionary into readable text."""
    return (
        f"Count : {stats['count']}\n"
        f"Mean  : {stats['mean']:.2f} Mbps\n"
        f"Min   : {stats['min']:.2f} Mbps\n"
        f"Q1    : {stats['q1']:.2f} Mbps\n"
        f"Median: {stats['median']:.2f} Mbps\n"
        f"Q3    : {stats['q3']:.2f} Mbps\n"
        f"Max   : {stats['max']:.2f} Mbps\n"
        f"IQR   : {stats['iqr']:.2f} Mbps\n"
        f"Estimated Supported Cameras:\n"
        f"   • Minimum (240 / Max Mbps): {stats['min_supported']} cameras\n"
        f"   • Maximum (320 / Min Mbps): {stats['max_supported']} cameras\n"
    )

def main():
    parser = argparse.ArgumentParser(
        description="Analyze a single Jetson camera log file for Mbps statistics and estimate supported camera count."
    )
    parser.add_argument(
        "filename",
        help="Name of the log file inside the logs/ directory (e.g. camera_3_run1.txt)",
    )
    args = parser.parse_args()

    # Use script-relative directories
    BASE_DIR = Path(__file__).resolve().parent
    LOG_DIR = BASE_DIR / "logs"
    STATS_DIR = BASE_DIR / "stats"
    STATS_DIR.mkdir(parents=True, exist_ok=True)

    log_path = LOG_DIR / args.filename
    if not log_path.exists():
        print(f"❌ Log file not found: {log_path}")
        return

    output_file = STATS_DIR / f"{log_path.stem}_bandwidth_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    data = parse_log(log_path)
    if not data:
        print(f"⚠️ No camera data found in {log_path.name}")
        return

    report = [
        f"=== Camera Bandwidth Summary ===",
        f"Generated: {datetime.now()}",
        f"Source log: {log_path.name}\n",
    ]

    for cam, values in data.items():
        stats = summarize(values)
        report.append(f"--- {cam} ---\n" + summarize_to_text(stats))

    summary_text = "\n".join(report)
    print(summary_text)

    with open(output_file, "w") as f:
        f.write(summary_text)

    print(f"\n✅ Summary saved to: {output_file}")

if __name__ == "__main__":
    main()
