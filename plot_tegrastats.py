#!/usr/bin/env python3
import re
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os

# === CLI ARGUMENT HANDLING ===
if len(sys.argv) < 2:
    print("Usage: plot_tegrastats.py <log_file>")
    sys.exit(1)

LOG_FILE = sys.argv[1]

# Allow both relative and "logs/" paths
if not os.path.exists(LOG_FILE):
    LOG_FILE = os.path.join("logs", LOG_FILE)
if not os.path.exists(LOG_FILE):
    print(f"❌ Log file not found: {LOG_FILE}")
    sys.exit(1)

# === REGEX PATTERNS ===
power_pat = re.compile(r"VDD_IN\s+(\d+)mW")
cpu_pat = re.compile(r"CPU\s+\[([^\]]+)\]")
gpu_pat = re.compile(r"GR3D_FREQ\s+(\d+)%")
temp_cpu_pat = re.compile(r"cpu@([\d\.]+)C")
temp_gpu_pat = re.compile(r"gpu@([\d\.]+)C")
timestamp_pat = re.compile(r"(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})")

# === DATA STORAGE ===
timestamps, power_w, cpu_avg, gpu_util, cpu_temp, gpu_temp = [], [], [], [], [], []

with open(LOG_FILE) as f:
    for line in f:
        try:
            ts_match = timestamp_pat.search(line)
            if not ts_match:
                continue
            ts = datetime.strptime(ts_match.group(1), "%m-%d-%Y %H:%M:%S")
            timestamps.append(ts)

            # Power (convert mW → W)
            p = power_pat.search(line)
            power_w.append(int(p.group(1)) / 1000 if p else None)

            # CPU utilization
            c = cpu_pat.search(line)
            if c:
                vals = [int(x.split("%@")[0]) for x in c.group(1).split(",")]
                cpu_avg.append(sum(vals) / len(vals))
            else:
                cpu_avg.append(None)

            # GPU utilization
            g = gpu_pat.search(line)
            gpu_util.append(int(g.group(1)) if g else None)

            # Temperatures
            t_cpu = temp_cpu_pat.search(line)
            t_gpu = temp_gpu_pat.search(line)
            cpu_temp.append(float(t_cpu.group(1)) if t_cpu else None)
            gpu_temp.append(float(t_gpu.group(1)) if t_gpu else None)
        except Exception:
            continue

# === OUTPUT DIRECTORY ===
os.makedirs("plots", exist_ok=True)

# === PLOTTING ===
plt.figure(figsize=(12, 9))

# --- 1️⃣ Power Plot ---
plt.subplot(3, 1, 1)
plt.plot(timestamps, power_w, color='tab:red', linewidth=1.8, label="Power (W)")
plt.ylabel("Power (W)")
plt.title("Jetson Power Consumption")
plt.legend()
plt.grid(True)

# --- 2️⃣ Utilization Plot ---
plt.subplot(3, 1, 2)
plt.plot(timestamps, cpu_avg, label="CPU Utilization (%)", color='tab:blue')
plt.plot(timestamps, gpu_util, label="GPU Utilization (%)", color='tab:orange')
plt.ylabel("Utilization (%)")
plt.title("CPU & GPU Utilization")
plt.legend()
plt.grid(True)

# --- 3️⃣ Temperature Plot ---
plt.subplot(3, 1, 3)
plt.plot(timestamps, cpu_temp, label="CPU Temp (°C)", color='tab:green')
plt.plot(timestamps, gpu_temp, label="GPU Temp (°C)", color='tab:purple')
plt.ylabel("Temperature (°C)")
plt.xlabel("Time")
plt.title("Thermal Data")
plt.legend()
plt.grid(True)

plt.tight_layout()

# === SAVE OUTPUT ===
base_name = os.path.splitext(os.path.basename(LOG_FILE))[0]
output_file = os.path.join("plots", f"{base_name}_power_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
plt.savefig(output_file, dpi=300)
print(f"✅ Plot saved to: {output_file}")
