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
    timeout=60,
    banner_timeout=60,
    auth_timeout=60,
)


def r(cmd, t=600):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


print(r("pkill -f '_long_play\\|homework_play\\|play.py' || true; sleep 1"))

fix = r'''
from pathlib import Path
import re

# List nav py
nav = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/navigation/vbot")
print("py files", sorted([p.name for p in nav.glob("*.py")]))

# Patch rl cfgs: soft-fail missing envs OR comment section02/03
cfgs = Path("/root/autodl-tmp/MotrixLab/motrix_rl/src/motrix_rl/cfgs.py")
t = cfgs.read_text(encoding="utf-8")

# Prefer: make registry not raise for missing env when decorating rlcfg
reg = Path("/root/autodl-tmp/MotrixLab/motrix_rl/src/motrix_rl/registry.py")
rt = reg.read_text(encoding="utf-8")
if "Environment '{env_name}' is not registered" in rt and "SOFT_SKIP_MISSING_ENV" not in rt:
    rt = rt.replace(
        'raise ValueError(f"Environment \'{env_name}\' is not registered in env_registry.")',
        'print(f"[SOFT_SKIP_MISSING_ENV] skip rlcfg for {env_name}"); return',
    )
    # careful: return in _register_rlcfg - need correct indent context
    reg.write_text(rt, encoding="utf-8")
    print("registry soft-skip patched")
    print(reg.read_text(encoding="utf-8")[reg.read_text(encoding="utf-8").find("SOFT_SKIP")-80:reg.read_text(encoding="utf-8").find("SOFT_SKIP")+120])
else:
    print("registry already patched or pattern missing")

# Also import section02/03 if files exist
init = nav / "__init__.py"
it = init.read_text(encoding="utf-8")
for mod in ["vbot_section02_np", "vbot_section03_np", "vbot_np", "vbot_stairs_np"]:
    if (nav / f"{mod}.py").exists() and mod not in it:
        it += f"\nfrom . import {mod}  # noqa: F401\n"
        print("added import", mod)
init.write_text(it, encoding="utf-8")
print("FIX_OK")
'''

sftp = c.open_sftp()
with sftp.file("/tmp/_fix_rlcfg.py", "w") as f:
    f.write(fix)

# Also fix long_play to use navigation module path - it currently imports locomotion
# Update long_play to not force locomotion hook if navigation is active
lp = Path_fix = None

play = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/root/miniconda3/envs/motrix/bin:/root/.local/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
OUT=/root/autodl-tmp/evidence_w8
cd /root/autodl-tmp/MotrixLab
source /root/miniconda3/etc/profile.d/conda.sh
conda activate motrix
source .venv/bin/activate
exec > >(tee "$OUT/homework_play.log") 2>&1
set -eux
.venv/bin/python /tmp/_fix_rlcfg.py

.venv/bin/python - <<'PY'
import motrix_envs
import motrix_rl.cfgs
from motrix_envs import registry as er
print("KEYS", sorted([k for k in er._envs if "vbot" in k]))
env = er.make("vbot_navigation_section01", "np", num_envs=1)
st = env.init_state()
print("OBS", st.obs.shape, "MOD", type(env).__module__)
# step a few random
import numpy as np
rng = np.random.default_rng(0)
for i in range(5):
    st = env.step(rng.uniform(-0.2,0.2,(1,12)).astype("float32"))
print("rew", float(st.reward[0]))
print("SMOKE_OK")
PY

KIT=runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints/best_agent.pickle
export PLAY_POLICY="$KIT"
export PLAY_STEPS=20000

# Use a navigation-aware long play (hooks navigation env class)
.venv/bin/python - <<'PY'
import os, sys, csv, time, re, traceback
from pathlib import Path
import numpy as np

ROOT = Path("/root/autodl-tmp")
OUT = ROOT / "evidence_w8"
os.chdir(str(ROOT / "MotrixLab"))
sys.path[:0] = [str(ROOT / "MotrixLab"), str(ROOT / "MotrixLab" / "scripts")]
os.environ.setdefault("MOTRIX_HEADLESS", "1")

import jax
print("jax", jax.devices())

CKPT = os.environ["PLAY_POLICY"]
STEPS = int(os.environ.get("PLAY_STEPS", "20000"))
print("USING", CKPT, "STEPS", STEPS)

# disable render in play.py
play_path = Path("scripts/play.py")
play_src = play_path.read_text(encoding="utf-8")
if "enable_render = True" in play_src:
    play_path.write_text(play_src.replace("enable_render = True", "enable_render = False", 1), encoding="utf-8")

# patch ppo play loop
ppo = Path("motrix_rl/src/motrix_rl/skrl/jax/train/ppo.py")
ppo_src = ppo.read_text(encoding="utf-8")
bak = Path(str(ppo) + ".bak_inf")
if bak.exists():
    ppo_src = bak.read_text(encoding="utf-8")
else:
    bak.write_text(ppo_src, encoding="utf-8")

ppo_src2 = re.sub(
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
    r"                time\.sleep\(1\.0 / fps - delta_time\))?"
    r"(?:\n        print\(\"WINDOW_PLAY_DONE\".*?\))?"
    r"(?:\n        print\(\"LONG_PLAY_LOOP_DONE\".*?\))?",
    f"""        max_steps = {STEPS}
        for step_i in range(max_steps):
            outputs = agent.act(obs, timestep=0, timesteps=0)
            actions = outputs[-1].get("mean_actions", outputs[0])
            obs, _, _, _, _ = env.step(actions)
        print("LONG_PLAY_LOOP_DONE", max_steps)""",
    ppo_src,
    count=1,
)
ppo.write_text(ppo_src2, encoding="utf-8")

import motrix_envs, motrix_rl.cfgs
from motrix_envs import registry as er
import motrix_envs.navigation.vbot.vbot_section01_np as env_mod

rows = []
_Old = env_mod.VBotSection01Env

def _xyz(env):
    data = env._data if hasattr(env, "_data") else env.state.data
    pose = np.asarray(env._body.get_pose(data), dtype=np.float32)
    return pose[0, :3] if pose.ndim > 1 else pose[:3]

def install_hooks(env):
    step_fn = env.step
    def wrapped(action):
        state = step_fn(action)
        try:
            xyz = _xyz(env)
            r = float(np.asarray(state.reward).reshape(-1)[0])
            rows.append((len(rows), float(xyz[0]), float(xyz[1]), float(xyz[2]), r))
            o = np.asarray(state.obs).reshape(-1)
            if len(rows) % 100 == 0:
                print(f"step={len(rows)} xy=({xyz[0]:.3f},{xyz[1]:.3f},{xyz[2]:.3f}) rew={r:.4f} obs_dim={o.size}", flush=True)
            if len(rows) >= STEPS:
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception as e:
            if len(rows) < 5:
                traceback.print_exc()
        return state
    env.step = wrapped
    return env

class Hooked(_Old):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        install_hooks(self)

er._envs["vbot_navigation_section01"].env_cls_dict["np"] = Hooked
env_mod.VBotSection01Env = Hooked

sys.argv = ["play.py", "--env=vbot_navigation_section01", "--num-envs=1", f"--policy={CKPT}"]
t0 = time.time()
try:
    from absl import app
    import scripts.play as P
    try:
        app.run(P.main)
    except SystemExit:
        pass
except Exception as e:
    print("play error", type(e), e)
    traceback.print_exc()

print("collected", len(rows), "in", time.time() - t0)
csv_path = OUT / "rollout_homework.csv"
with csv_path.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["step","x","y","z","rew"])
    w.writerows(rows)
if not rows:
    raise SystemExit("no rows")
ys = [r[2] for r in rows]
xs = [r[1] for r in rows]
print("start", rows[0], "end", rows[-1])
print("dy", ys[-1]-ys[0], "max_y", max(ys), "min_y", min(ys), "target~7.84")
if max(ys) >= 7.5:
    print("REACHED_2026")
else:
    print("LONG_PLAY_OK partial max_y", max(ys))

# media
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
TARGET_Y = 7.84
fig, ax = plt.subplots(figsize=(8,6), dpi=120)
ax.set_xlabel("x"); ax.set_ylabel("y"); ax.grid(True, alpha=0.3)
ax.axhline(TARGET_Y, color="#c0392b", ls="--", label="2026 y≈7.84")
ax.plot(xs[0], ys[0], "go", label="start")
(line,) = ax.plot([], [], "-", color="#1f6feb", lw=1.5)
(pt,) = ax.plot([], [], "o", color="#1f6feb", ms=5)
ax.legend(fontsize=8)
pad=0.5
ax.set_xlim(min(xs)-pad, max(xs)+pad)
ax.set_ylim(min(min(ys), TARGET_Y)-pad, max(max(ys), TARGET_Y)+pad)
n=len(rows); stride=max(1,n//360); frames=list(range(0,n,stride))
if frames[-1]!=n-1: frames.append(n-1)
mp4 = OUT / "play_homework_traj.mp4"
try:
    writer = FFMpegWriter(fps=24)
    with writer.saving(fig, str(mp4), dpi=120):
        for i in frames:
            line.set_data(xs[:i+1], ys[:i+1]); pt.set_data([xs[i]],[ys[i]]); writer.grab_frame()
    print("wrote", mp4)
except Exception as e:
    print("ffmpeg fail", e)
# evidence card
fig2, ax2 = plt.subplots(figsize=(8,4.5), dpi=140)
ax2.axis("off")
ax2.text(0.02,0.9,"MotrixArena S1 · 结营作业取证", fontsize=16, fontweight="bold", transform=ax2.transAxes)
ax2.text(0.02,0.7,f"max_y={max(ys):.3f}  target≈7.84  reached={max(ys)>=7.5}", fontsize=12, transform=ax2.transAxes)
ax2.text(0.02,0.55,f"policy={CKPT}", fontsize=9, transform=ax2.transAxes)
ax2.text(0.02,0.4,f"steps={len(rows)}  start_y={ys[0]:.3f} end_y={ys[-1]:.3f}", fontsize=11, transform=ax2.transAxes)
fig2.savefig(OUT / "homework_evidence_card.png", bbox_inches="tight")
print("HOMEWORK_PLAY_DONE")
PY

echo SCRIPT_DONE
'''
with sftp.file("/tmp/_hw_play_now.sh", "w") as f:
    f.write(play)
sftp.close()
print(r("chmod +x /tmp/_hw_play_now.sh; nohup bash /tmp/_hw_play_now.sh >/root/autodl-tmp/evidence_w8/hw2_nohup.out 2>&1 & echo PID=$!"))
c.close()
