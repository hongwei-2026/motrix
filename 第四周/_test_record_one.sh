#!/bin/bash
set +e
export PATH="$HOME/.local/bin:$PATH"
export LIBGL_ALWAYS_SOFTWARE=1
export WINIT_UNIX_BACKEND=x11
export XDG_RUNTIME_DIR=/tmp/runtime-root
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
cd /root/work/MotrixLab
POL=$(cat /root/work/week4_artifacts/logs/policy_cartpole.txt)
OUT=/root/work/week4_artifacts
pkill -9 Xvfb ffmpeg 2>/dev/null
Xvfb :99 -screen 0 1280x720x24 +extension GLX >/tmp/xvfb_t.log 2>&1 &
sleep 1
export DISPLAY=:99
# record in background
ffmpeg -y -f x11grab -draw_mouse 0 -video_size 1280x720 -framerate 20 -i :99.0 \
  -t 25 -pix_fmt yuv420p "$OUT/videos/cartpole_seed0.mp4" >/tmp/ff.log 2>&1 &
FPID=$!
sleep 1
timeout 22s uv run scripts/play.py --env=cartpole --rllib=skrl --policy="$POL" --seed=0 --num-envs=1 >/tmp/play_test.log 2>&1 &
PPID_PLAY=$!
sleep 8
xwininfo -root -tree 2>/dev/null | head -40
import -window root "$OUT/plots/cartpole_mid.png"
# also try grabbing largest child window
WID=$(xdotool search --name '' 2>/dev/null | head -1)
echo WID=$WID
wait "$PPID_PLAY" 2>/dev/null
wait "$FPID" 2>/dev/null
ls -lh "$OUT/videos/cartpole_seed0.mp4" "$OUT/plots/cartpole_mid.png"
file "$OUT/plots/cartpole_mid.png"
# extract mid frame from video
ffmpeg -y -ss 10 -i "$OUT/videos/cartpole_seed0.mp4" -frames:v 1 "$OUT/plots/cartpole_from_vid.png" 2>/dev/null
ls -lh "$OUT/plots/cartpole_from_vid.png"
file "$OUT/plots/cartpole_from_vid.png"
tail -n 15 /tmp/play_test.log
pkill -9 Xvfb 2>/dev/null
echo TEST_RECORD_DONE
