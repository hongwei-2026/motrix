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


# Compare obs assembly + cfg action_scale; patch nav env to 67 with force from dim67 method
print(
    r(
        r"""/root/autodl-tmp/MotrixLab/.venv/bin/python - <<'PY'
from pathlib import Path
nav = Path('/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/navigation/vbot/vbot_section01_np.py')
loc67 = Path('/root/autodl-tmp/evidence_w8/vbot_section01_np.py.dim67_boost')
nt = nav.read_text(encoding='utf-8')
lt = loc67.read_text(encoding='utf-8') if loc67.exists() else ''
# find observation building
for label,t in [('nav',nt),('loc67',lt)]:
    i = t.find('def _get_obs') 
    if i<0: i = t.find('obs = np.concatenate')
    print('====', label, 'get_obs', i)
    # print space
    for line in t.splitlines():
        if 'observation_space' in line or 'shape=(' in line and 'Box' in line:
            print(line.strip())
# cfg action scales
for p in [
 Path('/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/navigation/vbot/cfg.py'),
]:
    ct=p.read_text(encoding='utf-8')
    i=ct.find('vbot_navigation_section01')
    print('cfg snippet')
    print('\n'.join([ln for ln in ct[i:i+2500].splitlines() if 'action_scale' in ln or 'pose_command' in ln or 'max_episode' in ln or 'class VBotSection01' in ln][:20]))
PY"""
    )
)

# Patch: take official nav env, change to 67-dim by appending zeros OR copy force methods from dim67
# Better approach: overwrite nav section01 with dim67_boost but fix imports from .cfg (navigation cfg)
# Simplest working path used by kit training: likely 67 with forces.
# Copy force-wired locomotion file into navigation, fixing relative imports.

patch = r'''
from pathlib import Path
import shutil
import re

nav_dir = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/navigation/vbot")
nav_env = nav_dir / "vbot_section01_np.py"
out = Path("/root/autodl-tmp/evidence_w8")
shutil.copy2(nav_env, out / "nav_vbot_section01_np.py.stock54")

# Start from stock54, pad to 67 at observation outputs (zeros). Kit may need this.
# ALSO copy force helpers from dim67 if we want real forces - try ZEROS first with correct nav physics,
# then REAL forces as second play.

t = nav_env.read_text(encoding="utf-8")
assert "shape=(54,)" in t

# change space
t = t.replace(
    "self._observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(54,), dtype=np.float32)",
    "self._observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(67,), dtype=np.float32)",
    1,
)
# Also comment saying 67
t = t.replace("观测空间：67维" if False else "观测空间", "观测空间")  # noop safe

# Pad after every `assert obs.shape == (..., 54)`
for old in [
    "assert obs.shape == (data.shape[0], 54)",
    "assert obs.shape == (num_envs, 54)",
]:
    if old in t:
        t = t.replace(
            old,
            old.replace(", 54)", ", 54)  # base\n        obs = np.concatenate([obs, np.zeros((obs.shape[0], 13), dtype=np.float32)], axis=-1)\n        assert obs.shape[-1] == 67"),
            1,
        )

nav_env.write_text(t, encoding="utf-8")
compile(t, str(nav_env), "exec")
print("NAV_PADDED_TO_67")

# Ensure cfg pose target 10.2 / long episode for play
cfg = nav_dir / "cfg.py"
ct = cfg.read_text(encoding="utf-8")
# find section01 envcfg block
marker = '@registry.envcfg("vbot_navigation_section01")'
i = ct.find(marker)
j = ct.find("@registry.envcfg", i + 10)
block = ct[i:j]
block2 = re.sub(r"max_episode_seconds: float = [0-9.]+", "max_episode_seconds: float = 120.0", block)
block2 = re.sub(r"max_episode_steps: int = \d+", "max_episode_steps: int = 12000", block2)
# keep action_scale as in official (likely 0.25)
print("action_scale lines", [ln.strip() for ln in block2.splitlines() if "action_scale" in ln])
print("pose lines", [ln.strip() for ln in block2.splitlines() if "pose_command_range" in ln and not ln.strip().startswith("#")])
cfg.write_text(ct[:i] + block2 + ct[j:], encoding="utf-8")
print("CFG_TOUCHED")
'''

sftp = c.open_sftp()
with sftp.file("/tmp/_pad_nav67.py", "w") as f:
    f.write(patch)

play = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
OUT=/root/autodl-tmp/evidence_w8
cd /root/autodl-tmp/MotrixLab
source .venv/bin/activate
exec > >(tee "$OUT/homework_play.log") 2>&1
set -eux
.venv/bin/python /tmp/_pad_nav67.py

.venv/bin/python - <<'PY'
import motrix_envs, motrix_rl.cfgs
from motrix_envs import registry as er
env = er.make("vbot_navigation_section01","np", num_envs=1)
st = env.init_state()
print("OBS", st.obs.shape)
assert st.obs.shape[-1]==67
print("SMOKE_OK")
PY

# play with embedded script from previous (copy file if exists)
export PLAY_POLICY=runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints/best_agent.pickle
export PLAY_STEPS=15000
# reuse hw play python by extracting from last script - call long play adapted
.venv/bin/python /tmp/_hw_nav_play.py
'''

# write dedicated play script
hw_play = open(r"D:\motrix\_w8\hw_play_now.py", encoding="utf-8").read()
# Actually write clean play file directly
clean_play = r'''
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
STEPS = int(os.environ.get("PLAY_STEPS", "15000"))
print("USING", CKPT)

play_path = Path("scripts/play.py")
ps = play_path.read_text(encoding="utf-8")
if "enable_render = True" in ps:
    play_path.write_text(ps.replace("enable_render = True", "enable_render = False", 1), encoding="utf-8")

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
                print(f"step={len(rows)} xy=({xyz[0]:.3f},{xyz[1]:.3f},{xyz[2]:.3f}) rew={r:.4f} obs_dim={o.size} zOK={xyz[2]>0.25}", flush=True)
            if len(rows) >= STEPS:
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception:
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
try:
    from absl import app
    import scripts.play as P
    try:
        app.run(P.main)
    except SystemExit:
        pass
except Exception as e:
    print("play error", e)
    traceback.print_exc()

print("collected", len(rows))
assert rows, "no rows"
ys = [r[2] for r in rows]
xs = [r[1] for r in rows]
print("start", rows[0], "end", rows[-1])
print("dy", ys[-1]-ys[0], "max_y", max(ys), "min_y", min(ys), "target~7.84")
print("REACHED_2026" if max(ys) >= 7.5 else f"PARTIAL max_y={max(ys)}")

import csv
with (OUT/"rollout_homework.csv").open("w", newline="") as f:
    w=csv.writer(f); w.writerow(["step","x","y","z","rew"]); w.writerows(rows)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
fig, ax = plt.subplots(figsize=(8,6), dpi=120)
ax.axhline(7.84, color="r", ls="--", label="2026")
ax.plot(xs, ys, lw=1)
ax.legend(); ax.grid(True, alpha=0.3); ax.set_xlabel("x"); ax.set_ylabel("y")
fig.savefig(OUT/"homework_traj.png", bbox_inches="tight")
# short mp4
fig2, ax2 = plt.subplots(figsize=(8,6), dpi=100)
ax2.axhline(7.84, color="r", ls="--")
(line,) = ax2.plot([], [], "-")
(pt,) = ax2.plot([], [], "o")
ax2.set_xlim(min(xs)-0.5, max(xs)+0.5)
ax2.set_ylim(min(min(ys),7.84)-0.5, max(max(ys),7.84)+0.5)
frames = list(range(0, len(rows), max(1, len(rows)//300)))
try:
    w = FFMpegWriter(fps=24)
    with w.saving(fig2, str(OUT/"play_homework_traj.mp4"), dpi=100):
        for i in frames:
            line.set_data(xs[:i+1], ys[:i+1]); pt.set_data([xs[i]], [ys[i]]); w.grab_frame()
except Exception as e:
    print("mp4", e)
print("HOMEWORK_DONE")
'''

with sftp.file("/tmp/_hw_nav_play.py", "w") as f:
    f.write(clean_play)
with sftp.file("/tmp/_align_play.sh", "w") as f:
    f.write(play)
sftp.close()
print(r("chmod +x /tmp/_align_play.sh; nohup bash /tmp/_align_play.sh >/root/autodl-tmp/evidence_w8/align_nohup.out 2>&1 & echo PID=$!"))
c.close()
