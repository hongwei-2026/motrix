"""Kill bad 67-dim kit eval; play kit on 54-dim; then resume 67-dim train to 2026."""
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


def r(cmd, t=180):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


print("=== kill pipelines ===")
print(
    r(
        "pkill -f '_kit_pipeline.sh' || true; pkill -f '_kit_zeroforce.sh' || true; "
        "pkill -f '_long_play_autodl.py' || true; pkill -f 'scripts/play.py' || true; sleep 2; "
        "ps aux | grep -E 'long_play|kit_|train.py' | grep -v grep || echo CLEARED"
    )
)

script = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/root/miniconda3/envs/motrix/bin:/root/.local/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
export NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics
export VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json
OUT=/root/autodl-tmp/evidence_w8
cd /root/autodl-tmp/MotrixLab
source /root/miniconda3/etc/profile.d/conda.sh
conda activate motrix
source .venv/bin/activate
exec > >(tee "$OUT/kit54_pipeline.log") 2>&1
set -eux

ENV=motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py
CFG=motrix_envs/src/motrix_envs/locomotion/vbot/cfg.py

# Save current 67-dim boosted env
cp -f "$ENV" "$OUT/vbot_section01_np.py.dim67_boost"

# Restore 54-dim (pre-force) for official kit play
if [ -f "$OUT/vbot_section01_np.py.before_force" ]; then
  cp -f "$OUT/vbot_section01_np.py.before_force" "$ENV"
  echo RESTORED_54_from_before_force
else
  echo MISSING_before_force; exit 1
fi

# Ensure pose target = 2026 (10.2) and long episode for play
python - <<'PY'
from pathlib import Path
import re
c = Path("motrix_envs/src/motrix_envs/locomotion/vbot/cfg.py")
ct = c.read_text(encoding="utf-8")
marker = '@registry.envcfg("vbot_navigation_section01")'
i = ct.find(marker)
j = ct.find("@registry.envcfg", i + 10)
block = ct[i:j]
block2 = re.sub(r"max_episode_seconds: float = [0-9.]+", "max_episode_seconds: float = 120.0", block, count=1)
block2 = re.sub(r"max_episode_steps: int = \d+", "max_episode_steps: int = 12000", block2, count=1)
block2 = re.sub(r"pose_command_range = \[[^\]]+\]", "pose_command_range = [0.0, 10.2, 0.0, 0.0, 10.2, 0.0]", block2, count=1)
c.write_text(ct[:i] + block2 + ct[j:], encoding="utf-8")
print("CFG_OK_2026")
# verify obs space is 54
env = Path("motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py").read_text(encoding="utf-8")
print("has_67_space", "shape=(67,)" in env)
print("has_54_space", "shape=(54,)" in env)
print("has_force_concat", "foot_force" in env and "concatenate([obs, foot_force" in env)
PY

# Patch long_play to NOT assume force_norm if missing
export PLAY_POLICY=runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints/best_agent.pickle
export PLAY_STEPS=25000
python /tmp/_long_play_autodl.py 2>&1 | tee "$OUT/eval_kit54.log"
cp -f "$OUT/rollout_xy_long.csv" "$OUT/rollout_kit54.csv" || true
cp -f "$OUT/play_2026.mp4" "$OUT/play_kit54_2026.mp4" || true
cp -f "$OUT/play_trajectory_2026.mp4" "$OUT/play_kit54_traj.mp4" || true
grep -E 'max_y|LONG_PLAY|REACH|obs_dim' "$OUT/eval_kit54.log" | tail -40 || true

# Also agent_10000
export PLAY_POLICY=runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints/agent_10000.pickle
export PLAY_STEPS=25000
python /tmp/_long_play_autodl.py 2>&1 | tee "$OUT/eval_kit54_10000.log"
cp -f "$OUT/rollout_xy_long.csv" "$OUT/rollout_kit54_10000.csv" || true
cp -f "$OUT/play_2026.mp4" "$OUT/play_kit54_10000.mp4" || true
grep -E 'max_y|LONG_PLAY|REACH|obs_dim' "$OUT/eval_kit54_10000.log" | tail -40 || true

# ---- Restore 67-dim boost env and start proper train toward 10.2 ----
cp -f "$OUT/vbot_section01_np.py.dim67_boost" "$ENV"
# ensure reward boost still present
python - <<'PY'
from pathlib import Path
import re
p = Path("motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py")
t = p.read_text(encoding="utf-8")
# strip any ZERO_FORCE early return if present
if "ZERO_FORCE_FOR_KIT" in t:
    lines = t.splitlines(True)
    out=[]
    skip=0
    for i,l in enumerate(lines):
        if "ZERO_FORCE_FOR_KIT" in l:
            # remove this and next 2 lines (num_envs + return)
            skip=3
        if skip:
            skip -= 1
            continue
        out.append(l)
    t="".join(out)
if "y_progress = np.clip(dy * 25.0" not in t:
    t = t.replace("y_progress = np.clip(dy * 8.0, -1.0, 1.0)", "y_progress = np.clip(dy * 25.0, -2.0, 3.0)")
    t = t.replace("approach_reward = np.clip(distance_improvement * 6.0, -1.5, 1.5)", "approach_reward = np.clip(distance_improvement * 12.0, -2.0, 3.0)")
p.write_text(t, encoding="utf-8")
print("ENV67_READY", "shape=(67,)" in t, "y*25", "dy * 25.0" in t)

# curriculum: start mid then we use full 10.2 for this long train (homework target)
c = Path("motrix_envs/src/motrix_envs/locomotion/vbot/cfg.py")
ct = c.read_text(encoding="utf-8")
marker = '@registry.envcfg("vbot_navigation_section01")'
i = ct.find(marker)
j = ct.find("@registry.envcfg", i + 10)
block = ct[i:j]
block2 = re.sub(r"max_episode_seconds: float = [0-9.]+", "max_episode_seconds: float = 100.0", block, count=1)
block2 = re.sub(r"max_episode_steps: int = \d+", "max_episode_steps: int = 10000", block2, count=1)
# progressive: targets from y=3 to y=10.2 — use fixed 10.2 for reach
block2 = re.sub(r"pose_command_range = \[[^\]]+\]", "pose_command_range = [0.0, 10.2, 0.0, 0.0, 10.2, 0.0]", block2, count=1)
c.write_text(ct[:i]+block2+ct[j:], encoding="utf-8")
print("TRAIN_CFG_2026")
PY

# Resume/continue training with correct target (new run)
.venv/bin/python scripts/train.py --env=vbot_navigation_section01 --num-envs=1024 --train-backend=jax \
  2>&1 | tee "$OUT/train_reach2026.log"
echo TRAIN_REACH2026_DONE
'''

sftp = c.open_sftp()
with sftp.file("/tmp/_kit54_then_train.sh", "w") as f:
    f.write(script)
sftp.close()
print(r("chmod +x /tmp/_kit54_then_train.sh"))
print(
    r(
        "nohup bash /tmp/_kit54_then_train.sh >/root/autodl-tmp/evidence_w8/kit54_nohup.out 2>&1 & echo PID=$!"
    )
)
# verify before_force exists
print(r("ls -la /root/autodl-tmp/evidence_w8/vbot_section01_np.py.before_force; wc -l /root/autodl-tmp/evidence_w8/vbot_section01_np.py.before_force"))
c.close()
