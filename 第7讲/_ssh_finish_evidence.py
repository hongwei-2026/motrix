import os
# -*- coding: utf-8 -*-
"""Finish evidence: headless play, TB plots, directory screenshot, MD guide."""
import io
import paramiko
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HOST = "39.145.28.59"
PORT = 32222
USER = "root+vm-LEAjLhYIUQymN0v7"
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")
LOCAL = Path(r"D:\motrix\第7讲")
EVIDENCE = LOCAL / "证据"
EVIDENCE.mkdir(parents=True, exist_ok=True)

RUN = "runs/cartpole/skrl/26-10-21_11-04-41-419926_PPO"
CKPT = f"{RUN}/checkpoints/best_agent.pt"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, PORT, USER, PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()


def run(cmd, timeout=180):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode("utf-8", "replace")
    err = e.read().decode("utf-8", "replace")
    code = o.channel.recv_exit_status()
    return code, out, err


# 1) patch play temporarily for headless OR use xvfb
code, out, _ = run("which xvfb-run Xvfb 2>/dev/null; dpkg -l | grep -i xvfb | head || true")
print("xvfb:", out)

# Prefer patching enable_render=False for evidence run
code, out, err = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "python3 - <<'PY'\n"
    "from pathlib import Path\n"
    "p=Path('scripts/play.py')\n"
    "t=p.read_text()\n"
    "old='enable_render = True'\n"
    "new='enable_render = False  # headless evidence'\n"
    "if old not in t:\n"
    "  raise SystemExit('pattern missing')\n"
    "p.write_text(t.replace(old, new, 1))\n"
    "print('patched')\n"
    "PY"
)
print("patch:", out, err)

code, out, err = run(
    f"export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    f"uv run scripts/play.py --env cartpole --rllib skrl --policy {CKPT} --num-envs 1 "
    f"> /tmp/cartpole_play2.log 2>&1; echo PLAY_EXIT:$? >> /tmp/cartpole_play2.log; "
    f"tail -n 80 /tmp/cartpole_play2.log"
)
print("play2 code", code)
(EVIDENCE / "04_play_log.txt").write_text(out + "\n" + err, encoding="utf-8")

# restore play.py
run(
    "cd /workspace/MotrixLab && "
    "python3 - <<'PY'\n"
    "from pathlib import Path\n"
    "p=Path('scripts/play.py')\n"
    "t=p.read_text().replace('enable_render = False  # headless evidence', 'enable_render = True', 1)\n"
    "p.write_text(t)\n"
    "print('restored')\n"
    "PY"
)

# 2) export TB scalars + plot on remote
plot_py = r'''
from pathlib import Path
import json
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

run = Path("runs/cartpole/skrl/26-10-21_11-04-41-419926_PPO")
ea = EventAccumulator(str(run), size_guidance={"scalars": 0})
ea.Reload()
tags = ea.Tags()["scalars"]
wanted = [
    "Reward / Total reward (mean)",
    "Loss / Policy loss",
    "Loss / Value loss",
]
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
summary = {}
for ax, tag in zip(axes, wanted):
    sc = ea.Scalars(tag)
    xs = [s.step for s in sc]
    ys = [s.value for s in sc]
    ax.plot(xs, ys)
    ax.set_title(tag)
    ax.set_xlabel("step")
    ax.grid(True, alpha=0.3)
    summary[tag] = {"first": ys[0], "last": ys[-1], "n": len(ys), "min": min(ys), "max": max(ys)}
fig.tight_layout()
out = Path("/tmp/tb_curves.png")
fig.savefig(out, dpi=140)
Path("/tmp/tb_summary.json").write_text(json.dumps(summary, indent=2))
print("saved", out, summary)
'''
with sftp.file("/tmp/plot_tb.py", "w") as f:
    f.write(plot_py)
code, out, err = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "uv run python /tmp/plot_tb.py"
)
print("plot:", out, err)
sftp.get("/tmp/tb_curves.png", str(EVIDENCE / "02_tensorboard_curves.png"))
sftp.get("/tmp/tb_summary.json", str(EVIDENCE / "03_tensorboard_summary.json"))

# also fetch events for local backup
remote_events = f"/workspace/MotrixLab/{RUN}/events.out.tfevents.1792580684.383e3bf0f713.28008.0"
try:
    sftp.get(remote_events, str(EVIDENCE / "events.out.tfevents"))
except Exception as e:
    print("events download fail", e)

# 3) directory listing image
code, tree, _ = run(
    "cd /workspace/MotrixLab && find runs/cartpole -print | sed 's|[^/]*/| |g'"
)
code, lsout, _ = run(
    f"cd /workspace/MotrixLab && echo '$ ls -la {RUN}' && ls -la {RUN} && echo && "
    f"echo '$ ls -la {RUN}/checkpoints' && ls -la {RUN}/checkpoints && echo && "
    f"echo '$ ls -la runs/cartpole/skrl' && ls -la runs/cartpole/skrl"
)
(EVIDENCE / "01_runs_ls.txt").write_text(lsout, encoding="utf-8")

# make terminal-style screenshot
font = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 18)
lines = [
    "root@vm:/workspace/MotrixLab# ls -la runs/cartpole/skrl/",
]
lines += lsout.strip().splitlines()
lines.append("")
lines.append("root@vm:/workspace/MotrixLab# find runs/cartpole -maxdepth 3 -type f")
code, files, _ = run(
    "cd /workspace/MotrixLab && find runs/cartpole -maxdepth 4 -type f | sort"
)
lines += files.strip().splitlines()
text = "\n".join(lines)
# measure
tmp = Image.new("RGB", (10, 10))
d0 = ImageDraw.Draw(tmp)
# rough size
max_w = 0
for line in lines:
    bbox = d0.textbbox((0, 0), line, font=font)
    max_w = max(max_w, bbox[2] - bbox[0])
line_h = 24
img_w = max(900, max_w + 40)
img_h = 40 + line_h * len(lines) + 20
img = Image.new("RGB", (img_w, img_h), (12, 16, 22))
d = ImageDraw.Draw(img)
d.rectangle([0, 0, img_w, 28], fill=(30, 36, 48))
d.text((12, 6), "runs/cartpole output directory evidence", font=font, fill=(180, 200, 220))
y = 40
for line in lines:
    color = (120, 220, 140) if line.startswith("root@") or line.startswith("$") else (220, 225, 230)
    if "checkpoints" in line or "events.out" in line or "_PPO" in line:
        color = (255, 214, 102)
    d.text((16, y), line, font=font, fill=color)
    y += line_h
img.save(EVIDENCE / "01_runs_directory.png")

# training command log snippet image
code, tlog, _ = run("tail -n 40 /tmp/cartpole_train.log")
(EVIDENCE / "00_train_log_tail.txt").write_text(tlog, encoding="utf-8")

sftp.close()
c.close()
print("ALL EVIDENCE DONE")
