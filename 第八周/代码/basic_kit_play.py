"""Stop advanced jobs; restore stock env; play official kit to 2026."""
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


print("=== stop advanced ===")
print(
    r(
        "pkill -f 'scripts/train.py' || true; pkill -f '_long_play' || true; "
        "pkill -f '_mid_eval' || true; pkill -f 'play.py' || true; "
        "pkill -f '_train_wp' || true; sleep 2; "
        "ps aux | grep -E 'train|long_play|mid_eval' | grep -v grep || echo CLEARED"
    )
)

# Find stock/original env in starter_kit or backups
print("=== find stock env ===")
print(
    r(
        "ls -la /root/autodl-tmp/evidence_w8/vbot_section01_np.py* 2>/dev/null; "
        "find /root/autodl-tmp/starter_kit -name 'vbot_section01_np.py' 2>/dev/null; "
        "find /root/autodl-tmp -path '*vbot_0218*' -name 'vbot_section01_np.py' 2>/dev/null | head; "
        "ls /root/autodl-tmp/MotrixLab/runs/vbot_navigation_section01/26-02-05*/checkpoints/ | head"
    )
)

prep = r'''
from pathlib import Path
import re
import shutil

OUT = Path("/root/autodl-tmp/evidence_w8")
ENV = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py")
CFG = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/cfg.py")

# Keep current advanced copy
shutil.copy2(ENV, OUT / "vbot_section01_np.py.advanced_keep")

# Prefer untouched stock from starter if present, else before_force (54-dim stub)
candidates = [
    OUT / "vbot_section01_np.py.before_force",
    OUT / "vbot_section01_np.py.before_wire",
]
stock = None
for p in candidates:
    if p.exists():
        stock = p
        break
# Also search starter extract
for p in Path("/root/autodl-tmp").rglob("vbot_section01_np.py"):
    s = str(p)
    if "MotrixLab/motrix_envs" in s.replace("\\", "/"):
        continue
    if "evidence" in s:
        continue
    stock = p
    print("found external", p)
    break

assert stock is not None, "no stock env"
print("USING_STOCK", stock, "size", stock.stat().st_size)
text = stock.read_text(encoding="utf-8")
# Kit pickle expects 67-dim (earlier error: 67 vs 54). Check stock obs dim.
print("has54", "shape=(54,)" in text, "has67", "shape=(67,)" in text)
print("force_concat", "foot_force" in text and "concatenate" in text)

# If stock is 54-dim, use dim67_boost but ZERO forces (kit trained with 67 zeros or forces)
# Earlier: 54 env + 67 kit = shape error; 67 real forces = bad walk; 67 zero forces = still bad.
# Try restoring ORIGINAL kit env from runs companion or unpack navigation zip again.

# Search zip for original
import zipfile
zips = list(Path("/root/autodl-tmp").rglob("*.zip"))
for z in zips:
    try:
        with zipfile.ZipFile(z) as zf:
            names = [n for n in zf.namelist() if n.endswith("vbot_section01_np.py")]
            if names:
                print("ZIP", z, names[:3])
                data = zf.read(names[0])
                dest = OUT / "vbot_section01_np.py.from_zip"
                dest.write_bytes(data)
                stock = dest
                text = data.decode("utf-8")
                print("from_zip54", "shape=(54,)" in text, "67", "shape=(67,)" in text)
                break
    except Exception as e:
        pass

ENV.write_text(text, encoding="utf-8")
print("ENV_RESTORED")

# Fix cfg: long episode, pose at 2026 for play
ct = CFG.read_text(encoding="utf-8")
# patch the real section01 class (second marker)
idxs = []
start = 0
while True:
    i = ct.find('@registry.envcfg("vbot_navigation_section01")', start)
    if i < 0:
        break
    idxs.append(i)
    start = i + 1
out = []
last = 0
for i in idxs:
    j = ct.find("@registry.envcfg", i + 10)
    if j < 0:
        j = len(ct)
    block = ct[i:j]
    if "class VBot" not in block and "max_episode" not in block:
        out.append(ct[last:i])
        out.append(block)
        last = j
        continue
    block2 = re.sub(r"max_episode_seconds: float = [0-9.]+", "max_episode_seconds: float = 120.0", block)
    block2 = re.sub(r"max_episode_steps: int = \d+", "max_episode_steps: int = 12000", block2)
    block2 = re.sub(r"pose_command_range = \[[^\]]+\]", "pose_command_range = [0.0, 10.2, 0.0, 0.0, 10.2, 0.0]", block2)
    # keep kit action_scale 0.25 unless zip says otherwise
    out.append(ct[last:i])
    out.append(block2)
    last = j
    print("cfg lines", [ln.strip() for ln in block2.splitlines() if "max_episode" in ln or "pose_command_range =" in ln or "action_scale" in ln])
out.append(ct[last:])
CFG.write_text("".join(out), encoding="utf-8")
print("CFG_OK")
'''

sftp = c.open_sftp()
with sftp.file("/tmp/_basic_prep.py", "w") as f:
    f.write(prep)

play_sh = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/root/miniconda3/envs/motrix/bin:/root/.local/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
OUT=/root/autodl-tmp/evidence_w8
cd /root/autodl-tmp/MotrixLab
source /root/miniconda3/etc/profile.d/conda.sh
conda activate motrix
source .venv/bin/activate
exec > >(tee "$OUT/basic_kit_play.log") 2>&1
set -eux
.venv/bin/python /tmp/_basic_prep.py

# Detect obs dim of restored env
OBS=$(.venv/bin/python - <<'PY'
from pathlib import Path
t=Path('motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py').read_text()
print(67 if 'shape=(67,)' in t else 54)
PY
)
echo OBS_DIM=$OBS

KIT=runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints
# If env is 54 but kit is 67, pad obs via temporary wrap; if 67 use as-is
if [ "$OBS" = "54" ]; then
  echo "ENV is 54 — pad to 67 with zeros so kit loads"
  .venv/bin/python - <<'PY'
from pathlib import Path
p=Path('motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py')
t=p.read_text(encoding='utf-8')
# change space to 67 and pad at end of observation assembly
t=t.replace('shape=(54,)', 'shape=(67,)', 1)
# after assert obs.shape == (..., 54) pad
import re
def pad_after_assert(m):
    return m.group(0) + "\n        obs = np.concatenate([obs, np.zeros((obs.shape[0], 13), dtype=np.float32)], axis=-1)\n        assert obs.shape[-1] == 67"
# Only for compute obs asserts - simpler: replace both assert obs.shape == (data.shape[0], 54) blocks
t2=t
for old in [
    "assert obs.shape == (data.shape[0], 54)",
    "assert obs.shape == (num_envs, 54)",
]:
    if old in t2 and "zeros((obs.shape[0], 13)" not in t2[t2.find(old):t2.find(old)+200]:
        t2=t2.replace(old, old + "\n        obs = np.concatenate([obs, np.zeros((obs.shape[0], 13), dtype=np.float32)], axis=-1)\n        # padded to 67 for kit\n        assert obs.shape[-1] == 67", 1)
p.write_text(t2, encoding='utf-8')
print('PADDED_54_TO_67')
PY
fi

export PLAY_POLICY=$KIT/best_agent.pickle
export PLAY_STEPS=25000
python /tmp/_long_play_autodl.py
cp -f "$OUT/rollout_xy_long.csv" "$OUT/rollout_basic_kit.csv" || true
cp -f "$OUT/play_2026.mp4" "$OUT/play_basic_kit.mp4" || true
cp -f "$OUT/play_trajectory_2026.mp4" "$OUT/play_basic_kit_traj.mp4" || true
grep -E 'max_y|LONG_PLAY|dy |obs_dim|Error|ValueError' "$OUT/basic_kit_play.log" | tail -40 || true

# also try agent_10000
export PLAY_POLICY=$KIT/agent_10000.pickle
python /tmp/_long_play_autodl.py || true
cp -f "$OUT/rollout_xy_long.csv" "$OUT/rollout_basic_kit10000.csv" || true
grep -E 'max_y|LONG_PLAY|dy ' "$OUT/basic_kit_play.log" | tail -20 || true
echo BASIC_KIT_DONE
'''
with sftp.file("/tmp/_basic_kit_play.sh", "w") as f:
    f.write(play_sh)
sftp.close()
print(r("chmod +x /tmp/_basic_kit_play.sh; nohup bash /tmp/_basic_kit_play.sh >/root/autodl-tmp/evidence_w8/basic_nohup.out 2>&1 & echo PID=$!"))
c.close()
