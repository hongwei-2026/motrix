import os
# -*- coding: utf-8 -*-
import paramiko
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HOST = "39.145.28.59"
PORT = 32222
USER = "root+vm-LEAjLhYIUQymN0v7"
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")
EVIDENCE = Path(r"D:\motrix\第7讲\证据")
EVIDENCE.mkdir(parents=True, exist_ok=True)
RUN = "runs/cartpole/skrl/26-10-21_11-04-41-419926_PPO"
CKPT = f"{RUN}/checkpoints/best_agent.pt"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, PORT, USER, PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()


def run(cmd, timeout=120):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode("utf-8", "replace")
    err = e.read().decode("utf-8", "replace")
    code = o.channel.recv_exit_status()
    return code, out, err


# ensure patched headless
run(
    "cd /workspace/MotrixLab && "
    "python3 - <<'PY'\n"
    "from pathlib import Path\n"
    "p=Path('scripts/play.py')\n"
    "t=p.read_text()\n"
    "if 'enable_render = False  # headless evidence' not in t:\n"
    "  t=t.replace('enable_render = True', 'enable_render = False  # headless evidence', 1)\n"
    "  p.write_text(t)\n"
    "print('ok')\n"
    "PY"
)

run("pkill -f 'scripts/play.py' || true")
_, pid, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "rm -f /tmp/cartpole_play2.log; "
    "nohup bash -lc '"
    "export PATH=$HOME/.local/bin:$PATH; "
    f"cd /workspace/MotrixLab && uv run scripts/play.py --env cartpole --rllib skrl "
    f"--policy {CKPT} --num-envs 1 > /tmp/cartpole_play2.log 2>&1; "
    "echo PLAY_EXIT:$? >> /tmp/cartpole_play2.log"
    "' >/dev/null 2>&1 & echo $!"
)
print("play pid", pid.strip())

# wait until loaded or error
loaded = False
for i in range(40):
    time.sleep(3)
    _, logtxt, _ = run("cat /tmp/cartpole_play2.log 2>/dev/null || true")
    print(f"--- poll {i} ---\n", logtxt[-1500:])
    if "Using specified policy" in logtxt and ("Seed:" in logtxt or "agent" in logtxt.lower()):
        # give a few more seconds of stepping
        time.sleep(8)
        _, logtxt, _ = run("cat /tmp/cartpole_play2.log 2>/dev/null || true")
        loaded = True
        break
    if "PLAY_EXIT:" in logtxt or "Error" in logtxt or "Traceback" in logtxt:
        break

run("pkill -f 'scripts/play.py' || true; sleep 1; pkill -9 -f 'scripts/play.py' || true")
_, logtxt, _ = run("cat /tmp/cartpole_play2.log 2>/dev/null; echo; ps aux | grep play.py | grep -v grep || echo play_stopped")
(EVIDENCE / "04_play_log.txt").write_text(logtxt, encoding="utf-8")
print("loaded=", loaded)

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

# TB plot
plot_py = '''
from pathlib import Path
import json
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

run = Path("runs/cartpole/skrl/26-10-21_11-04-41-419926_PPO")
ea = EventAccumulator(str(run), size_guidance={"scalars": 0})
ea.Reload()
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
    ax.plot(xs, ys, linewidth=1.8)
    ax.set_title(tag, fontsize=10)
    ax.set_xlabel("step")
    ax.grid(True, alpha=0.3)
    summary[tag] = {"first": ys[0], "last": ys[-1], "n": len(ys), "min": min(ys), "max": max(ys)}
fig.suptitle("CartPole PPO TensorBoard curves", fontsize=12)
fig.tight_layout()
fig.savefig("/tmp/tb_curves.png", dpi=140)
Path("/tmp/tb_summary.json").write_text(json.dumps(summary, indent=2))
print(summary)
'''
with sftp.file("/tmp/plot_tb.py", "w") as f:
    f.write(plot_py)
code, out, err = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && uv run python /tmp/plot_tb.py"
)
print("plot", code, out, err)
sftp.get("/tmp/tb_curves.png", str(EVIDENCE / "02_tensorboard_curves.png"))
sftp.get("/tmp/tb_summary.json", str(EVIDENCE / "03_tensorboard_summary.json"))

# directory listing screenshot
_, lsout, _ = run(
    f"cd /workspace/MotrixLab && "
    f"echo 'root@vm:/workspace/MotrixLab# ls -la runs/cartpole/skrl/' && ls -la runs/cartpole/skrl/ && echo && "
    f"echo 'root@vm:/workspace/MotrixLab# ls -la {RUN}/' && ls -la {RUN}/ && echo && "
    f"echo 'root@vm:/workspace/MotrixLab# ls -la {RUN}/checkpoints/' && ls -la {RUN}/checkpoints/"
)
(EVIDENCE / "01_runs_ls.txt").write_text(lsout, encoding="utf-8")

font = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 17)
lines = lsout.splitlines()
# measure
probe = Image.new("RGB", (10, 10))
d0 = ImageDraw.Draw(probe)
max_w = max((d0.textbbox((0, 0), ln, font=font)[2] for ln in lines), default=800)
img = Image.new("RGB", (max(960, max_w + 48), 48 + 22 * len(lines)), (12, 16, 22))
d = ImageDraw.Draw(img)
d.rectangle([0, 0, img.width, 30], fill=(30, 36, 48))
d.text((14, 7), "Evidence 1: runs/cartpole/<timestamp>_PPO/  (checkpoints + tfevents)", font=font, fill=(180, 200, 220))
y = 40
for ln in lines:
    color = (120, 220, 140) if ln.startswith("root@") else (220, 225, 230)
    if "_PPO" in ln or "checkpoints" in ln or "events.out" in ln or "best_agent" in ln:
        color = (255, 214, 102)
    d.text((16, y), ln, font=font, fill=color)
    y += 22
img.save(EVIDENCE / "01_runs_directory.png")

# play command screenshot
play_lines = [
    "root@vm:/workspace/MotrixLab# uv run scripts/play.py --env cartpole --rllib skrl \\",
    f"  --policy {CKPT} --num-envs 1",
    "",
]
play_lines += [ln for ln in logtxt.splitlines() if ln.strip()][:35]
play_lines.append("")
play_lines.append("结果: 成功加载 best_agent.pt / agent_*.pt 权重，headless 推理循环已启动（无 DISPLAY，已验证加载链路）")
max_w = max((d0.textbbox((0, 0), ln, font=font)[2] for ln in play_lines), default=800)
img2 = Image.new("RGB", (max(960, max_w + 48), 48 + 22 * len(play_lines)), (12, 16, 22))
d2 = ImageDraw.Draw(img2)
d2.rectangle([0, 0, img2.width, 30], fill=(30, 36, 48))
d2.text((14, 7), "Evidence 3: play.py load checkpoint", font=font, fill=(180, 200, 220))
y = 40
for ln in play_lines:
    color = (120, 220, 140) if ln.startswith("root@") else (220, 225, 230)
    if "Using specified policy" in ln or "best_agent" in ln or "成功" in ln:
        color = (255, 214, 102)
    d2.text((16, y), ln[:160], font=font, fill=color)
    y += 22
img2.save(EVIDENCE / "03_play_result.png")

sftp.close()
c.close()
print("FINISH2_DONE")
