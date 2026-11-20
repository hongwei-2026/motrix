import paramiko
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "connect.cqa1.seetacloud.com",
    port=31748,
    username="root",
    password="IBH0VOb08eXI",
    timeout=60,
    banner_timeout=60,
    auth_timeout=60,
)


def r(cmd, t=120):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


print("=== pause train ===")
print(r("pkill -f 'scripts/train.py' || true; sleep 3; nvidia-smi --query-gpu=memory.used --format=csv,noheader"))

sh = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/root/miniconda3/envs/motrix/bin:/root/.local/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
OUT=/root/autodl-tmp/evidence_w8
cd /root/autodl-tmp/MotrixLab
source /root/miniconda3/etc/profile.d/conda.sh
conda activate motrix
source .venv/bin/activate
exec > >(tee "$OUT/mid_eval_wp.log") 2>&1
set -eux

for CKPT in \
  runs/vbot_navigation_section01/26-11-04_21-48-47-031616_PPO/checkpoints/agent_1500.pickle \
  runs/vbot_navigation_section01/26-11-04_21-48-47-031616_PPO/checkpoints/agent_1000.pickle \
  runs/vbot_navigation_section01/26-11-04_21-48-47-031616_PPO/checkpoints/best_agent.pickle
do
  [ -f "$CKPT" ] || continue
  echo "==== $CKPT ===="
  export PLAY_POLICY="$CKPT"
  export PLAY_STEPS=15000
  python /tmp/_long_play_autodl.py || true
  b=$(basename "$CKPT" .pickle)
  cp -f "$OUT/rollout_xy_long.csv" "$OUT/rollout_mid_${b}.csv" || true
  cp -f "$OUT/play_2026.mp4" "$OUT/play_mid_${b}.mp4" || true
  grep -E 'max_y|LONG_PLAY|dy |start |end ' "$OUT/mid_eval_wp.log" | tail -10 || true
done

# resume train
nohup bash /tmp/_train_wp2.sh >/root/autodl-tmp/evidence_w8/wp2_resume_nohup.out 2>&1 &
echo RESUME_PID=$!
echo MID_EVAL_DONE
'''
# Note: _train_wp2.sh will re-VERIFY then train from scratch (new run) - OK
sftp = c.open_sftp()
with sftp.file("/tmp/_mid_eval_wp.sh", "w") as f:
    f.write(sh)
# upload post eval too
with open(r"D:\motrix\_w8\_post_eval_pack.sh", "r", encoding="utf-8") as f:
    pe = f.read()
with sftp.file("/tmp/_post_eval_pack.sh", "w") as f:
    f.write(pe)
sftp.close()
print(r("chmod +x /tmp/_mid_eval_wp.sh /tmp/_post_eval_pack.sh; nohup bash /tmp/_mid_eval_wp.sh >/root/autodl-tmp/evidence_w8/mid_wp_nohup.out 2>&1 & echo PID=$!"))
c.close()
