#!/usr/bin/env bash
set +e
export PATH="$HOME/.local/bin:$PATH"
export LIBGL_ALWAYS_SOFTWARE=1
export WINIT_UNIX_BACKEND=x11
export XDG_RUNTIME_DIR=/tmp/runtime-root
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

cd /root/work/MotrixLab
OUT=/root/work/week4_artifacts
mkdir -p "$OUT/videos" "$OUT/plots"

A_POL=$(cat "$OUT/logs/policy_pendulum_A.txt")
B_POL=$(cat "$OUT/logs/policy_pendulum_B.txt")
CPOL=$(cat "$OUT/logs/policy_cartpole.txt")
APOL=$(cat "$OUT/logs/policy_acrobot.txt")

record_play () {
  local env="$1" pol="$2" seed="$3" label="$4"
  local disp=":99"
  local vid="$OUT/videos/${label}_seed${seed}.mp4"
  local png="$OUT/plots/${label}_seed${seed}_frame.png"
  echo "==== record $label seed=$seed ===="
  pkill -9 Xvfb ffmpeg 2>/dev/null
  sleep 0.5
  Xvfb "$disp" -screen 0 1280x720x24 +extension GLX >/tmp/xvfb_${label}.log 2>&1 &
  sleep 1
  export DISPLAY="$disp"
  ffmpeg -y -f x11grab -draw_mouse 0 -video_size 1280x720 -framerate 20 -i "${disp}.0" \
    -t 22 -pix_fmt yuv420p "$vid" >/tmp/ff_${label}.log 2>&1 &
  local FPID=$!
  sleep 1
  timeout 20s uv run scripts/play.py --env="$env" --rllib=skrl --policy="$pol" --seed="$seed" --num-envs=1 \
    >/tmp/play_${label}_s${seed}.log 2>&1 &
  local PP=$!
  sleep 8
  import -window root "$png"
  wait "$PP" 2>/dev/null
  wait "$FPID" 2>/dev/null
  ffmpeg -y -ss 8 -i "$vid" -frames:v 1 "${png%.png}_fromvid.png" 2>/dev/null
  ls -lh "$vid" "$png"
  file "$png"
  pkill -9 Xvfb 2>/dev/null
}

record_play cartpole "$CPOL" 0 cartpole
record_play acrobot "$APOL" 0 acrobot
for s in 0 1 2; do
  record_play pendulum "$A_POL" "$s" pendulum_A
  record_play pendulum "$B_POL" "$s" pendulum_B
done

echo "==== dm-reacher view ===="
pkill -9 Xvfb 2>/dev/null
Xvfb :98 -screen 0 1280x720x24 +extension GLX >/tmp/xvfb_view.log 2>&1 &
sleep 1
export DISPLAY=:98
timeout 30s uv run scripts/view.py --env=dm-reacher >/tmp/view2.log 2>&1 &
VP=$!
sleep 12
import -window root "$OUT/plots/dm_reacher_view.png"
ls -lh "$OUT/plots/dm_reacher_view.png"
file "$OUT/plots/dm_reacher_view.png"
kill "$VP" 2>/dev/null
pkill -9 Xvfb 2>/dev/null
tail -n 15 /tmp/view2.log

# save train log tails for screenshots
mkdir -p "$OUT/log_tails"
for f in train_cartpole train_pendulum_A train_acrobot train_pendulum_B; do
  tail -n 40 "$OUT/logs/${f}.log" > "$OUT/log_tails/${f}_tail.txt"
done

cd /root/work
tar czf week4_artifacts.tar.gz week4_artifacts
ls -lh week4_artifacts.tar.gz
ls -lh "$OUT/videos"
ls -lh "$OUT/plots"/*.png | head -40
echo RECORD_DONE
