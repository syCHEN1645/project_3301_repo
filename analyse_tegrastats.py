#!/usr/bin/env python3
import os
import re
import statistics
import sys
from datetime import datetime

# === Accept CLI argument ===
if len(sys.argv) < 2:
    print("Usage: analyse_power_stats.py <log_file>")
    sys.exit(1)

LOG_FILE = sys.argv[1]

# Allow passing just filename or full path
if not os.path.exists(LOG_FILE):
    LOG_FILE = os.path.join("logs", LOG_FILE)
if not os.path.exists(LOG_FILE):
    print(f"❌ Log file not found: {LOG_FILE}")
    sys.exit(1)

# === OUTPUT SETUP ===
OUTPUT_DIR = "stats"
os.makedirs(OUTPUT_DIR, exist_ok=True)

base = os.path.basename(LOG_FILE)
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    f"{os.path.splitext(base)[0]}_power_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)

# === REGEX PATTERNS ===
patterns = {
    "VDD_IN": r"VDD_IN\s+(\d+)mW",
    "VDD_CPU_GPU_CV": r"VDD_CPU_GPU_CV\s+(\d+)mW",
    "VDD_SOC": r"VDD_SOC\s+(\d+)mW",
    "cpu_temp": r"cpu@([\d\.]+)C",
    "gpu_temp": r"gpu@([\d\.]+)C",
    "tj_temp": r"tj@([\d\.]+)C",
    "soc_temp": r"soc\d?@([\d\.]+)C",
    "cv_temp": r"cv\d?@([\d\.]+)C",
    "CPU_load": r"CPU\s+\[([^\]]+)\]",
}

def extract_values(line):
    vals = {}
    for key, pat in patterns.items():
        match = re.search(pat, line)
        if not match:
            continue
        if key == "CPU_load":
            core_loads = re.findall(r"(\d+)%@", match.group(1))
            if core_loads:
                vals[key] = sum(map(int, core_loads)) / len(core_loads)
        else:
            vals[key] = float(match.group(1))
    return vals

def summarize(values, label, units=""):
    if not values:
        return f"\n=== {label} ===\nNo data found.\n"
    s = [f"\n=== {label} ==="]
    s.append(f"Count : {len(values)}")
    s.append(f"Mean  : {statistics.mean(values):.2f}{units}")
    s.append(f"Median: {statistics.median(values):.2f}{units}")
    s.append(f"Min   : {min(values):.2f}{units}")
    s.append(f"Max   : {max(values):.2f}{units}")
    if len(values) > 1:
        s.append(f"Stdev : {statistics.stdev(values):.2f}{units}")
    return "\n".join(s) + "\n"

def main():
    data = {key: [] for key in patterns.keys()}

    with open(LOG_FILE, "r") as f:
        for line in f:
            vals = extract_values(line)
            for k, v in vals.items():
                data[k].append(v)

    report = []
    report.append("=== Jetson Power & Thermal Statistics Report ===")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Source log: {LOG_FILE}\n")

    report.append(summarize(data["VDD_IN"], "Total Power (VDD_IN)", " mW"))
    report.append(summarize(data["VDD_CPU_GPU_CV"], "CPU/GPU Power (VDD_CPU_GPU_CV)", " mW"))
    report.append(summarize(data["VDD_SOC"], "SoC Power (VDD_SOC)", " mW"))
    report.append(summarize(data["cpu_temp"], "CPU Temperature", " °C"))
    report.append(summarize(data["gpu_temp"], "GPU Temperature", " °C"))
    report.append(summarize(data["tj_temp"], "Tj (Junction) Temperature", " °C"))
    report.append(summarize(data["soc_temp"], "SoC Temperature", " °C"))
    report.append(summarize(data["cv_temp"], "CV Core Temperature", " °C"))
    report.append(summarize(data["CPU_load"], "Average CPU Utilization", " %"))

    summary_text = "\n".join(report)
    print(summary_text)

    with open(OUTPUT_FILE, "w") as f:
        f.write(summary_text)

    print(f"\n✅ Report saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
