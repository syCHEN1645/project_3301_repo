import re
import matplotlib.pyplot as plt
from datetime import datetime

# Path to your tegrastats log
LOG_FILE = "power_log_1camera.txt"

timestamps, power_mw, cpu_avg, gpu_util, cpu_temp, gpu_temp = [], [], [], [], [], []

# Regex patterns for parsing
power_pat = re.compile(r"VDD_IN\s+(\d+)mW")
cpu_pat = re.compile(r"CPU\s+\[([^\]]+)\]")
gpu_pat = re.compile(r"GR3D_FREQ\s+(\d+)%")
temp_cpu_pat = re.compile(r"cpu@([\d\.]+)C")
temp_gpu_pat = re.compile(r"gpu@([\d\.]+)C")

with open(LOG_FILE) as f:
    for line in f:
        try:
            ts = re.search(r"(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2})", line)
            if not ts:
                continue
            timestamps.append(datetime.strptime(ts.group(1), "%m-%d-%Y %H:%M:%S"))

            # Power
            p = power_pat.search(line)
            power_mw.append(int(p.group(1)) if p else None)

            # CPU usage average
            c = cpu_pat.search(line)
            if c:
                vals = [int(x.split("%@")[0]) for x in c.group(1).split(",")]
                cpu_avg.append(sum(vals) / len(vals))
            else:
                cpu_avg.append(None)

            # GPU utilization
            g = gpu_pat.search(line)
            gpu_util.append(int(g.group(1)) if g else 0)

            # Temperatures
            t_cpu = temp_cpu_pat.search(line)
            t_gpu = temp_gpu_pat.search(line)
            cpu_temp.append(float(t_cpu.group(1)) if t_cpu else None)
            gpu_temp.append(float(t_gpu.group(1)) if t_gpu else None)
        except Exception:
            continue

# Plot
plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(timestamps, [p/1000 for p in power_mw], label="Power (W)")
plt.plot(timestamps, cpu_avg, label="CPU Util (%)")
plt.plot(timestamps, gpu_util, label="GPU Util (%)")
plt.ylabel("Power / Utilization")
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(timestamps, cpu_temp, label="CPU Temp (°C)")
plt.plot(timestamps, gpu_temp, label="GPU Temp (°C)")
plt.ylabel("Temperature (°C)")
plt.xlabel("Time")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig("power_log_1camera.png", dpi=300)
