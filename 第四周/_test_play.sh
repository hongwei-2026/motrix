#!/bin/bash
set +e
export PATH="$HOME/.local/bin:$PATH"
cd /root/work/MotrixLab
POL=$(cat /root/work/week4_artifacts/logs/policy_cartpole.txt)
echo "POL=$POL"
pkill Xvfb 2>/dev/null
Xvfb :99 -screen 0 1280x720x24 >/tmp/xvfb_t.log 2>&1 &
sleep 1
export DISPLAY=:99
timeout 15s uv run scripts/play.py --env=cartpole --rllib=skrl --policy="$POL" --seed=0 --num-envs=1 >/tmp/play_test.log 2>&1
echo EXIT:$?
tail -n 40 /tmp/play_test.log
import -window root /root/work/week4_artifacts/plots/cartpole_test.png
ls -lh /root/work/week4_artifacts/plots/cartpole_test.png
file /root/work/week4_artifacts/plots/cartpole_test.png
pkill Xvfb 2>/dev/null
