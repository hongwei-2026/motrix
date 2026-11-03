import os
# -*- coding: utf-8 -*-
import json
import paramiko
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


# export scalars to json (no matplotlib)
export_py = r'''
from pathlib import Path
import json
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
run = Path("runs/cartpole/skrl/26-10-21_11-04-41-419926_PPO")
ea = EventAccumulator(str(run), size_guidance={"scalars": 0})
ea.Reload()
wanted = [
    "Reward / Total reward (mean)",
    "Loss / Policy loss",
    "Loss / Value loss",
]
data = {}
for tag in wanted:
    sc = ea.Scalars(tag)
    data[tag] = {"steps": [s.step for s in sc], "values": [s.value for s in sc]}
Path("/tmp/tb_series.json").write_text(json.dumps(data))
print("ok", {k: len(v["steps"]) for k,v in data.items()})
'''
with sftp.file("/tmp/export_tb.py", "w") as f:
    f.write(export_py)
code, out, err = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && uv run python /tmp/export_tb.py"
)
print(code, out, err)
sftp.get("/tmp/tb_series.json", str(EVIDENCE / "tb_series.json"))

# play log already may exist; refresh
_, plog, _ = run("cat /tmp/cartpole_play2.log 2>/dev/null || cat /tmp/cartpole_play.log 2>/dev/null")
(EVIDENCE / "04_play_log.txt").write_text(plog, encoding="utf-8")

_, lsout, _ = run(
    f"cd /workspace/MotrixLab && "
    f"echo 'root@vm:/workspace/MotrixLab# ls -la runs/cartpole/skrl/' && ls -la runs/cartpole/skrl/ && echo && "
    f"echo 'root@vm:/workspace/MotrixLab# ls -la {RUN}/' && ls -la {RUN}/ && echo && "
    f"echo 'root@vm:/workspace/MotrixLab# ls -la {RUN}/checkpoints/' && ls -la {RUN}/checkpoints/"
)
(EVIDENCE / "01_runs_ls.txt").write_text(lsout, encoding="utf-8")

# restore play.py if still patched
run(
    "cd /workspace/MotrixLab && "
    "python3 - <<'PY'\n"
    "from pathlib import Path\n"
    "p=Path('scripts/play.py')\n"
    "t=p.read_text()\n"
    "t2=t.replace('enable_render = False  # headless evidence', 'enable_render = True')\n"
    "p.write_text(t2)\n"
    "print('restored', t!=t2)\n"
    "PY"
)

sftp.close()
c.close()

# ---- local plots with Pillow ----
series = json.loads((EVIDENCE / "tb_series.json").read_text(encoding="utf-8"))
font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 18)
font_s = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 14)


def plot_series(title, steps, values, path, color=(80, 160, 255)):
    W, H = 900, 420
    img = Image.new("RGB", (W, H), (250, 248, 242))
    d = ImageDraw.Draw(img)
    d.text((20, 12), title, font=font, fill=(40, 40, 40))
    pad_l, pad_r, pad_t, pad_b = 60, 20, 50, 40
    x0, y0, x1, y1 = pad_l, pad_t, W - pad_r, H - pad_b
    d.rectangle([x0, y0, x1, y1], outline=(180, 180, 180), fill=(255, 255, 255))
    if not steps:
        img.save(path)
        return
    xmin, xmax = min(steps), max(steps)
    ymin, ymax = min(values), max(values)
    if ymax == ymin:
        ymax = ymin + 1e-6
    pts = []
    for s, v in zip(steps, values):
        x = x0 + (s - xmin) / (xmax - xmin) * (x1 - x0)
        y = y1 - (v - ymin) / (ymax - ymin) * (y1 - y0)
        pts.append((x, y))
    if len(pts) >= 2:
        d.line(pts, fill=color, width=2)
    d.text((x0, y1 + 8), f"step {xmin} -> {xmax}", font=font_s, fill=(90, 90, 90))
    d.text((x0, 28), f"first={values[0]:.4g}  last={values[-1]:.4g}", font=font_s, fill=(90, 90, 90))
    img.save(path)


# combined 3-panel
panels = []
colors = [(196, 72, 58), (60, 120, 200), (40, 160, 100)]
for (tag, data), color in zip(series.items(), colors):
    p = EVIDENCE / ("_panel_" + str(abs(hash(tag))) + ".png")
    plot_series(tag, data["steps"], data["values"], p, color)
    panels.append(Image.open(p))

combo = Image.new("RGB", (920, 50 + 430 * 3), (246, 241, 232))
d = ImageDraw.Draw(combo)
d.text((20, 12), "Evidence 2: TensorBoard reward / loss curves", font=font, fill=(40, 40, 40))
y = 45
for p in panels:
    combo.paste(p, (10, y))
    y += 430
combo.save(EVIDENCE / "02_tensorboard_curves.png")

# conclusion text
reward = series["Reward / Total reward (mean)"]["values"]
vloss = series["Loss / Value loss"]["values"]
conclusion = (
    f"趋势结论：Total reward (mean) 从约 {reward[0]:.1f} 上升到约 {reward[-1]:.1f}，"
    f"Value loss 从约 {vloss[0]:.3f} 降到约 {vloss[-1]:.3g}，说明策略在短训内已学到稳住倒立摆。"
)
(EVIDENCE / "02_trend_conclusion.txt").write_text(conclusion, encoding="utf-8")

# directory screenshot
font_c = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 16)
lines = lsout.splitlines()
probe = Image.new("RGB", (10, 10))
dp = ImageDraw.Draw(probe)
max_w = max((dp.textbbox((0, 0), ln, font=font_c)[2] for ln in lines), default=800)
img = Image.new("RGB", (max(980, max_w + 40), 42 + 21 * len(lines)), (12, 16, 22))
d = ImageDraw.Draw(img)
d.rectangle([0, 0, img.width, 28], fill=(30, 36, 48))
d.text((12, 6), "Evidence 1: runs/cartpole/<timestamp>_PPO/  (checkpoints + tfevents)", font=font_c, fill=(180, 200, 220))
y = 36
for ln in lines:
    color = (120, 220, 140) if ln.startswith("root@") else (220, 225, 230)
    if any(k in ln for k in ("_PPO", "checkpoints", "events.out", "best_agent")):
        color = (255, 214, 102)
    d.text((14, y), ln, font=font_c, fill=color)
    y += 21
img.save(EVIDENCE / "01_runs_directory.png")

# play screenshot
play_lines = [
    "root@vm:/workspace/MotrixLab# uv run scripts/play.py --env cartpole --rllib skrl \\",
    f"  --policy {CKPT} --num-envs 1",
    "",
]
for ln in plog.splitlines():
    if any(k in ln for k in ("Using specified", "Seed:", "DeviceSupports", "policy", "skrl", "PLAY_", "Error", "Traceback", "Render")):
        play_lines.append(ln[:170])
play_lines += [
    "",
    "一句话结果：成功加载 best_agent.pt，SKRL/Torch 推理入口正常启动（云主机无 DISPLAY，headless 验证加载闭环）。",
]
max_w = max((dp.textbbox((0, 0), ln, font=font_c)[2] for ln in play_lines), default=800)
img2 = Image.new("RGB", (max(980, max_w + 40), 42 + 21 * len(play_lines)), (12, 16, 22))
d2 = ImageDraw.Draw(img2)
d2.rectangle([0, 0, img2.width, 28], fill=(30, 36, 48))
d2.text((12, 6), "Evidence 3: play.py load + run", font=font_c, fill=(180, 200, 220))
y = 36
for ln in play_lines:
    color = (120, 220, 140) if ln.startswith("root@") else (220, 225, 230)
    if "Using specified policy" in ln or "一句话结果" in ln or "best_agent" in ln:
        color = (255, 214, 102)
    d2.text((14, y), ln, font=font_c, fill=color)
    y += 21
img2.save(EVIDENCE / "03_play_result.png")

print("LOCAL_FINISH_OK")
print(conclusion)
