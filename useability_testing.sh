#!/bin/bash
set -e

TOTAL_DURATION=480        # 6 minutes
INTERVAL=20         # seconds between captures
WIDTH=1280
HEIGHT=720
PYTHON_ENV="/home/is307/miniforge3/envs/gauge_reader_org_clone/bin/python"
SCRIPT="scheduled_runs.py"

mkdir -p logs stats plots

# === Define test stages ===
declare -a TESTS=(
  "0 2 7"
)
  # "0 "
  # "0 2 "
  # "0 2 3"
  # "0 2 3 5"

for cams in "${TESTS[@]}"; do
  echo "🚀 Running test with cameras: $cams at ${WIDTH}x${HEIGHT}"

  $PYTHON_ENV $SCRIPT \
    --cameras $cams \
    --width $WIDTH \
    --height $HEIGHT \
    --total_duration $TOTAL_DURATION \
    --interval $INTERVAL

  echo "✅ Finished run for cameras: $cams"

  # --- Automatically analyze logs ---
  latest_bandwidth=$(ls -t logs/subprocess_output_* | head -n 1)
  latest_tegrastats=$(ls -t logs/tegrastats_* | head -n 1)

  if [[ -f "$latest_bandwidth" ]]; then
    echo "📊 Analyzing bandwidth: $latest_bandwidth"
    $PYTHON_ENV analyse_camera_bandwidth.py "$(basename "$latest_bandwidth")"
  fi

  if [[ -f "$latest_tegrastats" ]]; then
    echo "⚡ Analyzing power usage: $latest_tegrastats"
    $PYTHON_ENV analyse_tegrastats.py "$(basename "$latest_tegrastats")"

    echo "📈 Plotting power graph..."
    $PYTHON_ENV plot_tegrastats.py "$(basename "$latest_tegrastats")"
    plot_name="plots/$(basename "${latest_tegrastats%.*}").png"
    mv power_log_1camera.png "$plot_name" 2>/dev/null || true
    echo "✅ Plot saved to $plot_name"
  fi

  echo "----------------------------------------------------"
  echo "🕒 Cooling for 10 seconds..."
  sleep 10
done

echo "🎯 All camera combination tests completed!"
