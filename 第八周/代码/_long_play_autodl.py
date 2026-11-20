#!/usr/bin/env python3
"""Long headless play with XY log + trajectory media on SeetaCloud autodl-tmp."""
from __future__ import annotations

import csv
import os
import re
import sys
import time
import traceback
from pathlib import Path

import numpy as np

ROOT = Path("/root/autodl-tmp")
OUT = ROOT / "evidence_w8"
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(str(ROOT / "MotrixLab"))
sys.path[:0] = [str(ROOT / "MotrixLab"), str(ROOT / "MotrixLab" / "scripts")]
os.environ.setdefault("MOTRIX_HEADLESS", "1")

import jax

print("jax", jax.devices())

ckpts = sorted(ROOT.rglob("best_agent.pickle"), key=lambda p: p.stat().st_mtime, reverse=True)
print("ckpts", ckpts[:5])
assert ckpts, "no pickle"
CKPT = os.environ.get("PLAY_POLICY") or str(ckpts[0])
print("USING", CKPT)
STEPS = int(os.environ.get("PLAY_STEPS", "12000"))
rows: list[tuple] = []
force_samples: list[float] = []

play_path = Path("scripts/play.py")
play_src = play_path.read_text(encoding="utf-8")
if "enable_render = True" in play_src:
    play_path.write_text(
        play_src.replace("enable_render = True", "enable_render = False", 1),
        encoding="utf-8",
    )
    print("play.py render disabled for headless")

ppo = Path("motrix_rl/src/motrix_rl/skrl/jax/train/ppo.py")
ppo_src = ppo.read_text(encoding="utf-8")
bak = Path(str(ppo) + ".bak_inf")
if bak.exists():
    ppo_src = bak.read_text(encoding="utf-8")

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
print("ppo loop steps", STEPS)

import motrix_envs  # noqa: F401
import motrix_rl.cfgs  # noqa: F401
import motrix_envs.locomotion.vbot.vbot_section01_np as env_mod
from motrix_envs import registry as er

_Old = env_mod.VBotSection01Env


def _xyz_from_env(env) -> np.ndarray:
    data = env._data if hasattr(env, "_data") else env.state.data
    # Motrix Body API: get_pose -> [num_envs, 7] = xyz + quat
    pose = np.asarray(env._body.get_pose(data), dtype=np.float32)
    if pose.ndim == 1:
        return pose[:3]
    return pose[0, :3]


def install_hooks(env):
    print("install_hooks on", type(env), flush=True)
    step_fn = env.step

    def wrapped(action):
        state = step_fn(action)
        try:
            xyz = _xyz_from_env(env)
            r = float(np.asarray(state.reward).reshape(-1)[0])
            rows.append((len(rows), float(xyz[0]), float(xyz[1]), float(xyz[2]), r))
            o = np.asarray(state.obs).reshape(-1)
            if o.size >= 67:
                force_samples.append(float(np.linalg.norm(o[54:66])))
            elif o.size >= 12:
                force_samples.append(float(np.linalg.norm(o[-13:-1])))
            if len(rows) % 100 == 0:
                fn = force_samples[-1] if force_samples else 0.0
                print(
                    f"step={len(rows)} xy=({xyz[0]:.3f},{xyz[1]:.3f},{xyz[2]:.3f}) "
                    f"rew={r:.4f} force_norm={fn:.3f} obs_dim={o.size}",
                    flush=True,
                )
            if len(rows) >= STEPS:
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception as e:
            if len(rows) < 8:
                print("hook err", type(e), e, flush=True)
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
print("registry hooked", er._envs["vbot_navigation_section01"].env_cls_dict["np"])

sys.argv = [
    "play.py",
    "--env=vbot_navigation_section01",
    "--num-envs=1",
    f"--policy={CKPT}",
]

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
csv_path = OUT / "rollout_xy_long.csv"
with csv_path.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["step", "x", "y", "z", "rew"])
    w.writerows(rows)
print("wrote", csv_path)
if force_samples:
    print("force_norm mean/max", float(np.mean(force_samples)), float(np.max(force_samples)))

if not rows:
    raise SystemExit("no rows collected")

xs = [r[1] for r in rows]
ys = [r[2] for r in rows]
zs = [r[3] for r in rows]
print("start", rows[0], "end", rows[-1])
print("dy", ys[-1] - ys[0], "max_y", max(ys), "min_y", min(ys), "target~7.84")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, PillowWriter

TARGET_Y = 7.84

fig, ax = plt.subplots(figsize=(8, 6), dpi=120)
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")
ax.grid(True, alpha=0.3)
ax.axhline(TARGET_Y, color="#c0392b", ls="--", lw=1.2, label="2026 platform y≈7.84")
ax.plot(xs[0], ys[0], "go", label="start")
(line,) = ax.plot([], [], "-", color="#1f6feb", lw=1.5)
(pt,) = ax.plot([], [], "o", color="#1f6feb", ms=5)
ax.legend(loc="best", fontsize=8)
pad = 0.5
ax.set_xlim(min(xs) - pad, max(xs) + pad)
ax.set_ylim(min(min(ys), TARGET_Y) - pad, max(max(ys), TARGET_Y) + pad)

n = len(rows)
stride = max(1, n // 360)
frames = list(range(0, n, stride))
if frames[-1] != n - 1:
    frames.append(n - 1)

mp4 = OUT / "play_trajectory_2026.mp4"
try:
    writer = FFMpegWriter(fps=24, metadata={"title": "MotrixArena S1"})
    with writer.saving(fig, str(mp4), dpi=120):
        for i in frames:
            line.set_data(xs[: i + 1], ys[: i + 1])
            pt.set_data([xs[i]], [ys[i]])
            ax.set_title(f"MotrixArena S1 · step {rows[i][0]} · y={ys[i]:.2f} / 7.84")
            writer.grab_frame()
    print("mp4", mp4, mp4.stat().st_size)
except Exception as e:
    print("ffmpeg writer fail", e)
    gif = OUT / "play_trajectory_2026.gif"
    writer = PillowWriter(fps=12)
    with writer.saving(fig, str(gif), dpi=100):
        for i in frames[::2]:
            line.set_data(xs[: i + 1], ys[: i + 1])
            pt.set_data([xs[i]], [ys[i]])
            writer.grab_frame()
    print("gif", gif)

fig2, ax2 = plt.subplots(figsize=(8, 6), dpi=180)
sc = ax2.scatter(xs, ys, c=range(len(xs)), cmap="viridis", s=6, linewidths=0)
ax2.plot(xs[0], ys[0], "o", color="#27ae60", ms=10, label="start")
ax2.plot(xs[-1], ys[-1], "s", color="#e74c3c", ms=10, label="end")
ax2.axhline(TARGET_Y, color="#c0392b", ls="--", label="2026 y≈7.84")
ax2.set_xlabel("x (m)")
ax2.set_ylabel("y (m)")
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_title("VBot base XY · MotrixArena-S1 section01 · to 2026")
fig2.colorbar(sc, ax=ax2, label="step")
fig2.tight_layout()
fig2.savefig(OUT / "xhs_traj_xy.png")

fig3, ax3 = plt.subplots(figsize=(9, 4), dpi=180)
ax3.plot([r[0] for r in rows], ys, label="base y", color="#1f6feb")
ax3.plot([r[0] for r in rows], zs, label="base z", color="#8e44ad", alpha=0.8)
ax3.axhline(TARGET_Y, color="#c0392b", ls="--", label="2026")
ax3.set_xlabel("step")
ax3.set_ylabel("meters")
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_title("Progress toward 2026 platform")
fig3.tight_layout()
fig3.savefig(OUT / "xhs_progress_yz.png")

fig4, ax4 = plt.subplots(figsize=(9, 3.2), dpi=180)
ax4.plot([r[0] for r in rows], [r[4] for r in rows], color="#16a085", lw=0.7)
ax4.set_xlabel("step")
ax4.set_ylabel("reward")
ax4.set_title("Per-step reward")
ax4.grid(True, alpha=0.3)
fig4.tight_layout()
fig4.savefig(OUT / "xhs_reward.png")

if force_samples:
    fig5, ax5 = plt.subplots(figsize=(9, 3.2), dpi=180)
    ax5.plot(force_samples, color="#d35400", lw=0.7)
    ax5.set_xlabel("step")
    ax5.set_ylabel("|foot force|")
    ax5.set_title("Foot-contact force magnitude in obs[54:66]")
    ax5.grid(True, alpha=0.3)
    fig5.tight_layout()
    fig5.savefig(OUT / "xhs_foot_force.png")

fig6, ax6 = plt.subplots(figsize=(10, 5.5), dpi=180)
ax6.axis("off")
reached = max(ys) >= (TARGET_Y - 0.35)
text = (
    f"MotrixArena 结营作业 · 于鸿伟\n"
    f"环境: MotrixArena-S1 / vbot_navigation_section01\n"
    f"策略: starter_kit best_agent.pickle · skrl-jax\n"
    f"观测: 67维 = 54 base + 12 foot-force + 1 pad\n"
    f"步数: {len(rows)}\n"
    f"起点 y={ys[0]:.3f} → 终点 y={ys[-1]:.3f}  max_y={max(ys):.3f}\n"
    f"目标平台 y≈{TARGET_Y}  {'已接近/到达' if reached else '仍在接近中'}\n"
    f"Δy = {ys[-1]-ys[0]:.3f} m"
)
ax6.text(
    0.04,
    0.95,
    text,
    va="top",
    ha="left",
    fontsize=14,
    family="DejaVu Sans",
    bbox=dict(boxstyle="round,pad=0.6", facecolor="#f7f9fc", edgecolor="#1f6feb"),
)
ax6.set_title("Evidence card", fontsize=16, pad=12)
fig6.tight_layout()
fig6.savefig(OUT / "xhs_evidence_card.png")

print("pngs ok")
if mp4.exists() and mp4.stat().st_size > 10000:
    dest = OUT / "play_2026.mp4"
    dest.write_bytes(mp4.read_bytes())
    print("promoted", dest, dest.stat().st_size)
print("LONG_PLAY_OK", "reached" if reached else "partial", "max_y", max(ys))
