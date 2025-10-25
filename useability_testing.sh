#!/bin/bash
set -e

# === PARAMETERS ===
DURATION=480      # 8 minutes
INTERVAL=30       # seconds between captures
PYTHON_ENV="/home/is307/miniforge3/envs/gauge_reader_org_clone/bin/python"
SCRIPT="scheduled_runs.py"

# === TABLE OF CAMERA CONFIG ===
# Format: camera_index camera_name supported_resolutions
declare -A CAMS
CAMS[0]="brass_gauge_left 640x480 800x600 1024x768 1280x720 1600x1200 1920x1080 2048x1536 2592x1944"
CAMS[3]="casing_gauge 640x480 1024x768 1280x720 1280x1024 1920x1080 2048x1536"
CAMS[4]="pressure_gauge 640x480 800x600 960x540 1280x720"

# === Ensure required folders exist ===
mkdir -p logs
mkdir -p stats
mkdir -p plots

# === MAIN LOOP ===
for cam_index in "${!CAMS[@]}"; do
  read -r cam_name res_list <<< "${CAMS[$cam_index]}"
  for res in $res_list; do
    WIDTH=$(echo $res | cut -dx -f1)
    HEIGHT=$(echo $res | cut -dx -f2)

    echo "🚀 Running camera $cam_index ($cam_name) at ${WIDTH}x${HEIGHT}"

    $PYTHON_ENV $SCRIPT \
      --camera $cam_index \
      --width $WIDTH \
      --height $HEIGHT \
      --duration $DURATION \
      --interval $INTERVAL

    echo "✅ Finished run for Cam $cam_index ($res)"

    # --- Automatically analyze logs ---
    latest_bandwidth=$(ls -t logs/camera_output_${cam_index}_*.log | head -n 1)
    latest_tegrastats=$(ls -t logs/tegrastats_cam${cam_index}_${WIDTH}x${HEIGHT}_*.log | head -n 1)

    if [[ -f "$latest_bandwidth" ]]; then
      echo "📊 Analyzing bandwidth: $latest_bandwidth"
      $PYTHON_ENV analyse_camera_bandwidth.py "$(basename "$latest_bandwidth")"
    fi

    if [[ -f "$latest_tegrastats" ]]; then
      echo "⚡ Analyzing tegrastats: $latest_tegrastats"
      $PYTHON_ENV analyse_tegrastats.py "$(basename "$latest_tegrastats")"

      # --- Plot tegrastats ---
      echo "📈 Plotting power graph..."
      $PYTHON_ENV plot_tegrastats.py "$latest_tegrastats"
      plot_name="plots/$(basename "${latest_tegrastats%.*}").png"
      mv power_log_1camera.png "$plot_name" 2>/dev/null || true
      echo "✅ Plot saved to $plot_name"
    fi

    echo "----------------------------------------------------"
    sleep 10
  done
done

echo "🎯 All experiments finished."