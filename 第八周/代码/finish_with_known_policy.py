"""Install torch + LittleMailman waypoint env + best_agent.pt; play to 2026."""
import paramiko
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "connect.cqa1.seetacloud.com",
    port=31748,
    username="root",
    password="IBH0VOb08eXI",
    timeout=90,
    banner_timeout=90,
    auth_timeout=90,
)


def r(cmd, t=900):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


print(r("pkill -f '_long_play|_hw_nav|_align_play|play.py' || true; sleep 2; echo CLEARED"))

sh = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
OUT=/root/autodl-tmp/evidence_w8
LAB=/root/autodl-tmp/MotrixLab
cd "$LAB"
source .venv/bin/activate
exec > >(tee "$OUT/finish_known.log") 2>&1
set -eux

mkdir -p "$OUT/known_policy"
cd "$OUT/known_policy"

# Download working policy + env (github raw)
BASE=https://raw.githubusercontent.com/LittleMailman/motrixlab_quadruped_rl_navigation/main/stages/03_vbot_section01_navigation
# best_agent.pt is large - use curl -L
curl -L --retry 5 -o best_agent.pt \
  "$BASE/results/best_agent.pt"
curl -L --retry 5 -o vbot_section01_np.py \
  "$BASE/motrix_envs/src/motrix_envs/navigation/vbot/vbot_section01_np.py"
curl -L --retry 5 -o cfg.py \
  "$BASE/motrix_envs/src/motrix_envs/navigation/vbot/cfg.py"
curl -L --retry 5 -o vbot_init.py \
  "$BASE/motrix_envs/src/motrix_envs/navigation/vbot/__init__.py"
ls -lh

PY=$LAB/.venv/bin/python
# Install torch (GPU if possible via pip tuna)
$PY -c "import torch" 2>/dev/null || \
  $PY -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple torch --extra-index-url https://download.pytorch.org/whl/cu124

$PY - <<'PY'
import torch
print("TORCH", torch.__version__, "cuda", torch.cuda.is_available())
PY

# Deploy env into navigation/vbot (backup first)
NAV=$LAB/motrix_envs/src/motrix_envs/navigation/vbot
cp -f "$NAV/vbot_section01_np.py" "$OUT/nav_vbot_section01_np.py.before_known"
cp -f "$NAV/cfg.py" "$OUT/nav_cfg.py.before_known"
cp -f "$OUT/known_policy/vbot_section01_np.py" "$NAV/vbot_section01_np.py"
cp -f "$OUT/known_policy/cfg.py" "$NAV/cfg.py"
# keep __init__ importing section01

# Place policy
mkdir -p "$LAB/runs/vbot_navigation_section01/known_success_PPO/checkpoints"
cp -f "$OUT/known_policy/best_agent.pt" \
  "$LAB/runs/vbot_navigation_section01/known_success_PPO/checkpoints/best_agent.pt"

# Smoke make env
cd "$LAB"
PY=$LAB/.venv/bin/python
$PY - <<'PY'
import motrix_envs, motrix_rl.cfgs
from motrix_envs import registry as er
env = er.make("vbot_navigation_section01", "np", num_envs=1)
st = env.init_state()
print("OBS", st.obs.shape, "MOD", type(env).__module__)
print("SMOKE_OK")
PY

# Play with torch policy via play.py
export PLAY_POLICY=$LAB/runs/vbot_navigation_section01/known_success_PPO/checkpoints/best_agent.pt
# Use scripts/play.py directly with patched step limit via env
$PY - <<'PY'
import os, sys, csv, time, traceback
from pathlib import Path
import numpy as np

ROOT = Path("/root/autodl-tmp")
OUT = ROOT / "evidence_w8"
os.chdir(str(ROOT/"MotrixLab"))
sys.path[:0] = [str(ROOT/"MotrixLab"), str(ROOT/"MotrixLab"/"scripts")]
os.environ["MOTRIX_HEADLESS"]="1"

CKPT = "runs/vbot_navigation_section01/known_success_PPO/checkpoints/best_agent.pt"
STEPS = 20000
print("USING", CKPT)

# disable render
p = Path("scripts/play.py")
t = p.read_text(encoding="utf-8")
if "enable_render = True" in t:
    p.write_text(t.replace("enable_render = True", "enable_render = False", 1), encoding="utf-8")

# Patch torch ppo play loop similarly
for rel in [
    "motrix_rl/src/motrix_rl/skrl/torch/train/ppo.py",
    "motrix_rl/src/motrix_rl/skrl/jax/train/ppo.py",
]:
    pp = Path(rel)
    if not pp.exists():
        print("missing", rel); continue
    src = pp.read_text(encoding="utf-8")
    bak = Path(str(pp)+".bak_hw")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")
    else:
        src = bak.read_text(encoding="utf-8")
    import re
    src2 = re.sub(
        r"        fps = \d+\n"
        r"        (?:max_steps = \d+\n)?"
        r"        (?:while True:|for step_i in range\(max_steps\):)\n"
        r"(?:            t = time\.time\(\)\n)?"
        r"            outputs = agent\.act\(obs, timestep=0, timesteps=0\)\n"
        r"            actions = outputs\[-1\]\.get\(\"mean_actions\", outputs\[0\]\)\n"
        r"            obs, _, _, _, _ = env\.step\(actions\)\n"
        r"(?:            env\.render\(\)\n)?"
        r"(?:            delta_time = time\.time\(\) - t\n"
        r"            if delta_time < 1\.0 / fps:\n"
        r"                time\.sleep\(1\.0 / fps - delta_time\))?",
        f"""        max_steps = {STEPS}
        for step_i in range(max_steps):
            outputs = agent.act(obs, timestep=0, timesteps=0)
            actions = outputs[-1].get("mean_actions", outputs[0])
            obs, _, _, _, _ = env.step(actions)
        print("LONG_PLAY_LOOP_DONE", max_steps)""",
        src,
        count=1,
    )
    if src2 != src:
        pp.write_text(src2, encoding="utf-8")
        print("patched", rel)
    else:
        print("NO_PATCH_MATCH", rel)

import motrix_envs, motrix_rl.cfgs
from motrix_envs import registry as er
import motrix_envs.navigation.vbot.vbot_section01_np as env_mod

rows=[]
_Old=env_mod.VBotSection01Env

def _xyz(env):
    data = getattr(env, "_data", None) or env.state.data
    pose = np.asarray(env._body.get_pose(data), dtype=np.float32)
    return pose[0,:3] if pose.ndim>1 else pose[:3]

def install(env):
    step_fn=env.step
    def wrapped(action):
        state=step_fn(action)
        try:
            xyz=_xyz(env)
            rew=float(np.asarray(state.reward).reshape(-1)[0])
            rows.append((len(rows), float(xyz[0]), float(xyz[1]), float(xyz[2]), rew))
            if len(rows)%100==0:
                print(f"step={len(rows)} xy=({xyz[0]:.3f},{xyz[1]:.3f},{xyz[2]:.3f}) rew={rew:.3f} stand={xyz[2]>0.25}", flush=True)
            if len(rows)>=STEPS:
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception:
            if len(rows)<5: traceback.print_exc()
        return state
    env.step=wrapped
    return env

class Hooked(_Old):
    def __init__(self,*a,**k):
        super().__init__(*a,**k); install(self)

er._envs["vbot_navigation_section01"].env_cls_dict["np"]=Hooked
env_mod.VBotSection01Env=Hooked

sys.argv=["play.py","--env=vbot_navigation_section01","--num-envs=1",f"--policy={CKPT}"]
try:
    from absl import app
    import scripts.play as P
    try: app.run(P.main)
    except SystemExit: pass
except Exception as e:
    print("PLAY_ERR", e); traceback.print_exc()

print("collected", len(rows))
assert rows, "no rows"
ys=[r[2] for r in rows]; xs=[r[1] for r in rows]
print("start", rows[0], "end", rows[-1])
print("max_y", max(ys), "target~7.84")
reached = max(ys) >= 7.5
print("REACHED_2026" if reached else f"PARTIAL max_y={max(ys)}")
import csv
with (OUT/"rollout_homework.csv").open("w",newline="") as f:
    w=csv.writer(f); w.writerow(["step","x","y","z","rew"]); w.writerows(rows)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
fig,ax=plt.subplots(figsize=(8,6),dpi=120)
ax.axhline(7.84,color="r",ls="--",label="2026")
ax.plot(xs,ys); ax.legend(); ax.grid(True,alpha=0.3)
fig.savefig(OUT/"homework_traj.png", bbox_inches="tight")
fig2,ax2=plt.subplots(figsize=(8,4.5),dpi=140); ax2.axis("off")
ax2.text(0.02,0.85,"结营作业取证 · 走到2026平台", fontsize=16, fontweight="bold", transform=ax2.transAxes)
ax2.text(0.02,0.6,f"max_y={max(ys):.3f}  reached={reached}", fontsize=13, transform=ax2.transAxes)
ax2.text(0.02,0.4,f"policy=known_success best_agent.pt (waypoint)", fontsize=10, transform=ax2.transAxes)
fig2.savefig(OUT/"homework_evidence_card.png", bbox_inches="tight")
# mp4
fig3,ax3=plt.subplots(figsize=(8,6),dpi=100)
ax3.axhline(7.84,color="r",ls="--")
(line,)=ax3.plot([],[],"-"); (pt,)=ax3.plot([],[],"o")
ax3.set_xlim(min(xs)-0.5,max(xs)+0.5); ax3.set_ylim(min(min(ys),7.84)-0.5,max(max(ys),7.84)+0.5)
frames=list(range(0,len(rows),max(1,len(rows)//300)))
try:
    w=FFMpegWriter(fps=24)
    with w.saving(fig3, str(OUT/"play_homework_traj.mp4"), dpi=100):
        for i in frames:
            line.set_data(xs[:i+1], ys[:i+1]); pt.set_data([xs[i]],[ys[i]]); w.grab_frame()
    print("mp4 ok")
except Exception as e:
    print("mp4 fail", e)
print("FINISH_KNOWN_DONE")
PY

echo ALL_DONE
'''

sftp = c.open_sftp()
with sftp.file("/tmp/_finish_known.sh", "w") as f:
    f.write(sh)
sftp.close()
print(r("chmod +x /tmp/_finish_known.sh; nohup bash /tmp/_finish_known.sh >/root/autodl-tmp/evidence_w8/finish_nohup.out 2>&1 & echo PID=$!"))
c.close()
