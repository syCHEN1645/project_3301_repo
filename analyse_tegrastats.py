import os
import re
import statistics
from datetime import datetime

# === CONFIGURATION ===
LOG_FILE = "power_stat_archive/power_log_1camera.txt"
OUTPUT_DIR = "power_stat_archive"
OUTPUT_FILE = f"{OUTPUT_DIR}/power_log_1camera_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

    # Save report to file
    with open(OUTPUT_FILE, "w") as f:
        f.write(summary_text)

    print(f"\n✅ Report saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
