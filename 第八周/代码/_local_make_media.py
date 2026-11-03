#!/usr/bin/env python3
"""Make submission mp4 + xhs pngs from rollout CSV locally."""
import csv
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, PillowWriter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "submit_assets"
OUT.mkdir(exist_ok=True)
csv_path = OUT / "rollout_xy_long.csv"
if not csv_path.exists():
    csv_path = ROOT / "rollout_xy_long.csv"
rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
assert rows, "empty csv"
xs = [float(r["x"]) for r in rows]
ys = [float(r["y"]) for r in rows]
zs = [float(r["z"]) for r in rows]
rews = [float(r.get("rew", 0) or 0) for r in rows]
TARGET_Y = 7.84
print(f"n={len(rows)} y=[{min(ys):.3f},{max(ys):.3f}] start={ys[0]:.3f} end={ys[-1]:.3f}")

fig, ax = plt.subplots(figsize=(10, 7), dpi=140)
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")
ax.grid(True, alpha=0.35)
ax.axhline(TARGET_Y, color="#c0392b", ls="--", lw=1.4, label="2026 platform y≈7.84")
ax.plot(xs[0], ys[0], "o", color="#27ae60", ms=10, label="start")
(line,) = ax.plot([], [], "-", color="#1f6feb", lw=2.0)
(pt,) = ax.plot([], [], "o", color="#e67e22", ms=7)
ax.legend(loc="best")
pad = 0.6
ax.set_xlim(min(xs) - pad, max(xs) + pad)
ax.set_ylim(min(min(ys), TARGET_Y) - pad, max(max(ys), TARGET_Y) + pad)

n = len(rows)
stride = max(1, n // 480)
frames = list(range(0, n, stride))
if frames[-1] != n - 1:
    frames.append(n - 1)

mp4 = OUT / "play_trajectory_2026.mp4"
ok = False
if shutil.which("ffmpeg"):
    try:
        writer = FFMpegWriter(fps=24, metadata={"title": "MotrixArena S1 to 2026"})
        with writer.saving(fig, str(mp4), dpi=140):
            for i in frames:
                line.set_data(xs[: i + 1], ys[: i + 1])
                pt.set_data([xs[i]], [ys[i]])
                ax.set_title(f"MotrixArena S1 · step {i} · y={ys[i]:.2f} / 7.84")
                writer.grab_frame()
        print("mp4", mp4, mp4.stat().st_size)
        ok = True
    except Exception as e:
        print("ffmpeg writer fail", e)

if not ok:
    gif = OUT / "play_trajectory_2026.gif"
    writer = PillowWriter(fps=12)
    with writer.saving(fig, str(gif), dpi=100):
        for i in frames[::2]:
            line.set_data(xs[: i + 1], ys[: i + 1])
            pt.set_data([xs[i]], [ys[i]])
            ax.set_title(f"step {i} y={ys[i]:.2f}")
            writer.grab_frame()
    print("gif", gif, gif.stat().st_size)
    # try gif->mp4 if ffmpeg exists
    if shutil.which("ffmpeg"):
        import subprocess

        subprocess.check_call(
            ["ffmpeg", "-y", "-i", str(gif), "-movflags", "faststart", "-pix_fmt", "yuv420p", str(mp4)]
        )
        ok = mp4.exists()

if ok:
    (OUT / "play_2026.mp4").write_bytes(mp4.read_bytes())
    print("play_2026.mp4", (OUT / "play_2026.mp4").stat().st_size)

fig2, ax2 = plt.subplots(figsize=(9, 6), dpi=180)
sc = ax2.scatter(xs, ys, c=range(len(xs)), cmap="viridis", s=8, linewidths=0)
ax2.plot(xs[0], ys[0], "o", color="#27ae60", ms=10, label="start")
ax2.plot(xs[-1], ys[-1], "s", color="#e74c3c", ms=10, label="end")
ax2.axhline(TARGET_Y, color="#c0392b", ls="--", label="2026")
ax2.set_xlabel("x")
ax2.set_ylabel("y")
ax2.grid(True, alpha=0.3)
ax2.legend()
ax2.set_title("VBot base XY · toward 2026")
fig2.colorbar(sc, ax=ax2, label="step")
fig2.tight_layout()
fig2.savefig(OUT / "xhs_traj_xy.png")

fig3, ax3 = plt.subplots(figsize=(9, 4), dpi=180)
ax3.plot(ys, label="y")
ax3.plot(zs, label="z", alpha=0.85)
ax3.axhline(TARGET_Y, color="#c0392b", ls="--", label="2026")
ax3.set_xlabel("step")
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_title("Progress toward 2026")
fig3.tight_layout()
fig3.savefig(OUT / "xhs_progress_yz.png")

fig4, ax4 = plt.subplots(figsize=(9, 3), dpi=180)
ax4.plot(rews, color="#16a085", lw=0.7)
ax4.set_title("reward")
ax4.grid(True, alpha=0.3)
fig4.tight_layout()
fig4.savefig(OUT / "xhs_reward.png")

reached = max(ys) >= TARGET_Y - 0.35
fig5, ax5 = plt.subplots(figsize=(10, 5.2), dpi=180)
ax5.axis("off")
txt = (
    f"MotrixArena 结营作业 · 于鸿伟\n"
    f"MotrixArena-S1 / vbot_navigation_section01 / skrl-jax / RTX 4090\n"
    f"steps={len(rows)}  start_y={ys[0]:.3f}  end_y={ys[-1]:.3f}  max_y={max(ys):.3f}\n"
    f"target y≈{TARGET_Y}  {'接近/到达' if reached else '行进中'}  Δy={ys[-1]-ys[0]:.3f}"
)
ax5.text(
    0.05,
    0.9,
    txt,
    va="top",
    fontsize=15,
    bbox=dict(boxstyle="round,pad=0.6", facecolor="#f7f9fc", edgecolor="#1f6feb"),
)
fig5.tight_layout()
fig5.savefig(OUT / "xhs_evidence_card.png")
print("pngs done ->", OUT)
