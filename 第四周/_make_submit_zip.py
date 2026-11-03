#!/usr/bin/env python3
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

root = Path(r"D:\motrix\第四周")
src_shot = root / "截图"
src_art = src_shot / "week4_artifacts"
pack_root = root / "_submit_pack"
pack = pack_root / "于鸿伟_MotrixLab第四周_实操证据"

if pack_root.exists():
    shutil.rmtree(pack_root)
pack.mkdir(parents=True)

dirs = {
    "doc": pack / "01_文档材料",
    "curve": pack / "02_曲线图",
    "shot": pack / "03_运行截图",
    "video": pack / "04_仿真录屏",
    "log": pack / "05_日志与代码摘录",
    "ckpt": pack / "06_模型权重_best",
}
for d in dirs.values():
    d.mkdir(parents=True)

# docs
doc_copies = [
    (root / "第四周作业_指导与答案.md", "第四周作业_指导与答案.md"),
    (root / "飞书_正文重排.md", "飞书作业正文_题下作答.md"),
    (root / "小红书" / "文案.md", "小红书文案.md"),
    (src_shot / "证据清单.md", "证据清单.md"),
]
for src, name in doc_copies:
    if src.exists():
        shutil.copy2(src, dirs["doc"] / name)

# curves
for a, b in {
    "A_cartpole_reward.png": "01_cartpole_reward.png",
    "A_pendulum_reward.png": "02_pendulum_A_reward.png",
    "B_pendulum_reward.png": "03_pendulum_B_reward.png",
    "A_acrobot_reward.png": "04_acrobot_reward.png",
}.items():
    p = src_shot / a
    if p.exists():
        shutil.copy2(p, dirs["curve"] / b)

# screenshots
for a, b in {
    "cartpole_play.png": "01_cartpole_play.png",
    "acrobot_play.png": "02_acrobot_play.png",
    "pendulum_A_play_seed0.png": "03_pendulum_A_seed0.png",
    "pendulum_A_play_seed1.png": "04_pendulum_A_seed1.png",
    "pendulum_A_play_seed2.png": "05_pendulum_A_seed2.png",
    "pendulum_B_play_seed0.png": "06_pendulum_B_seed0.png",
    "pendulum_B_play_seed1.png": "07_pendulum_B_seed1.png",
    "pendulum_B_play_seed2.png": "08_pendulum_B_seed2.png",
    "dm_reacher_view.png": "09_dm_reacher_view.png",
}.items():
    p = src_shot / a
    if p.exists():
        shutil.copy2(p, dirs["shot"] / b)

# videos
vid_dir = src_shot / "videos"
for v in sorted(vid_dir.glob("*.mp4")):
    shutil.copy2(v, dirs["video"] / v.name)

# logs + code
log_dir = src_art / "logs"
for name in [
    "train_cartpole.log",
    "train_pendulum_A.log",
    "train_pendulum_B.log",
    "train_acrobot.log",
    "policy_cartpole.txt",
    "policy_pendulum_A.txt",
    "policy_pendulum_B.txt",
    "policy_acrobot.txt",
]:
    p = log_dir / name
    if p.exists():
        shutil.copy2(p, dirs["log"] / name)

code_dir = src_art / "code_shots"
if code_dir.exists():
    shutil.copytree(code_dir, dirs["log"] / "code_shots", dirs_exist_ok=True)

# best agents only
runs = src_shot / "MotrixLab" / "runs"
for rel, name in [
    ("cartpole/skrl/26-10-25_12-21-55-090874_PPO/checkpoints/best_agent.pt", "cartpole_best_agent.pt"),
    ("pendulum/skrl/26-10-25_12-22-44-980900_PPO/checkpoints/best_agent.pt", "pendulum_A_best_agent.pt"),
    ("pendulum/skrl/26-10-25_12-27-43-111800_PPO/checkpoints/best_agent.pt", "pendulum_B_best_agent.pt"),
    ("acrobot/skrl/26-10-25_12-23-29-008041_PPO/checkpoints/best_agent.pt", "acrobot_best_agent.pt"),
]:
    p = runs.joinpath(*rel.split("/"))
    if p.exists():
        shutil.copy2(p, dirs["ckpt"] / name)
        print("ckpt", name, p.stat().st_size)
    else:
        print("MISSING", p)

readme = """# 于鸿伟 · MotrixLab 第四周实操证据包

- **课程周次**：第四周（经典控制对比 + Pendulum 能量奖励消融 + dm-reacher）
- **代码版本**：MotrixLab **v0.3.0**
- **训练后端**：`skrl` + `torch`，默认 `seed=42`，`num_envs=2048`
- **飞书作业**：https://ccnz793r59f8.feishu.cn/wiki/CTb6wEgzxipc8LkQqIZcOzgPnie

## 目录对照提交渠道

| 文件夹 | 对应提交项 | 格式 |
|--------|------------|------|
| `01_文档材料` | Word/文档材料 | `.md` / `.html`（可另存 PDF/DOCX） |
| `02_曲线图` | 运行截图/曲线图 | `.png`（均 < 10MB） |
| `03_运行截图` | 运行截图 | `.png` |
| `04_仿真录屏` | 仿真录屏视频 | `.mp4` |
| `05_日志与代码摘录` | 工程源码/日志 | `.log` / `.txt` / 代码备份 |
| `06_模型权重_best` | 工程产物（best checkpoint） | `.pt` |

## 关键命令与模型路径（可粘贴到文本框）

```text
# 训练
uv run scripts/train.py --env=cartpole --rllib=skrl --seed=42 --train-backend=torch
uv run scripts/train.py --env=pendulum --rllib=skrl --seed=42 --train-backend=torch
uv run scripts/train.py --env=acrobot --rllib=skrl --seed=42 --train-backend=torch
# Pendulum B：pendulum_np.py 中 + energy_reward 改为 + 0.0 * energy_reward 后重训

# 回放示例
uv run scripts/play.py --env=pendulum --rllib=skrl --policy=runs/pendulum/skrl/26-10-25_12-22-44-980900_PPO/checkpoints/best_agent.pt --seed=0
uv run scripts/view.py --env=dm-reacher
```

### best_agent 路径

```text
runs/cartpole/skrl/26-10-25_12-21-55-090874_PPO/checkpoints/best_agent.pt
runs/pendulum/skrl/26-10-25_12-22-44-980900_PPO/checkpoints/best_agent.pt   # A 组
runs/pendulum/skrl/26-10-25_12-27-43-111800_PPO/checkpoints/best_agent.pt   # B 组
runs/acrobot/skrl/26-10-25_12-23-29-008041_PPO/checkpoints/best_agent.pt
```

### 关键超参（Pendulum A/B 一致，仅能量项系数不同）

```text
MotrixLab=v0.3.0
rllib=skrl
train_backend=torch
seed=42
num_envs=2048
trainer.timesteps=5000
learning_rate=3e-4
policy/value hiddens=[64,64]
max_episode_seconds=10
ctrl_dt=0.025
max_episode_steps=400
A: energy_reward 系数 = 1
B: energy_reward 系数 = 0
```

### Reacher 关键数值（代码）

```text
target_size=0.02
reward=1 当 dist in [0, 0.02]
reward=0 当 dist >= 0.04
target_x ~ Uniform(-0.15, 0.15)
target_y = 0.15  (Uniform(0.15,0.15)，实际固定)
max_episode_steps = 6.0/0.025 = 240
```

## 视频清单（二.4 回放）

- `cartpole_seed0.mp4` / `acrobot_seed0.mp4`
- Pendulum A：`pendulum_A_seed{0,1,2}.mp4`
- Pendulum B：`pendulum_B_seed{0,1,2}.mp4`

## 在线链接

- 飞书作业文档：https://ccnz793r59f8.feishu.cn/wiki/CTb6wEgzxipc8LkQqIZcOzgPnie
- 上游仓库：https://github.com/Motphys/MotrixLab（tag v0.3.0）
"""
(dirs["doc"] / "00_提交说明_README.md").write_text(readme.lstrip(), encoding="utf-8")

(dirs["doc"] / "关键数值_可粘贴.txt").write_text(
    "\n".join(
        [
            "MotrixLab v0.3.0 | skrl+torch | seed=42 | num_envs=2048",
            "Pendulum timesteps=5000 lr=3e-4 hiddens=[64,64] episode_steps=400",
            "A energy_coef=1 | B energy_coef=0",
            "cartpole best: runs/cartpole/skrl/26-10-25_12-21-55-090874_PPO/checkpoints/best_agent.pt",
            "pendulum A:    runs/pendulum/skrl/26-10-25_12-22-44-980900_PPO/checkpoints/best_agent.pt",
            "pendulum B:    runs/pendulum/skrl/26-10-25_12-27-43-111800_PPO/checkpoints/best_agent.pt",
            "acrobot best:  runs/acrobot/skrl/26-10-25_12-23-29-008041_PPO/checkpoints/best_agent.pt",
            "reacher: reward=1 iff dist<=0.02; reward=0 iff dist>=0.04; target_y fixed 0.15; max_steps=240",
            "",
        ]
    ),
    encoding="utf-8",
)

(dirs["doc"] / "作业索引.html").write_text(
    """<!DOCTYPE html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>于鸿伟 · 第四周证据索引</title>
<body style="font-family:sans-serif;max-width:720px;margin:2rem auto;line-height:1.6">
<h1>于鸿伟 · MotrixLab 第四周实操证据</h1>
<p>请先阅读 <code>00_提交说明_README.md</code>。</p>
<p>飞书作业：
<a href="https://ccnz793r59f8.feishu.cn/wiki/CTb6wEgzxipc8LkQqIZcOzgPnie">打开文档</a></p>
<ul>
<li>曲线图 → <code>02_曲线图/</code></li>
<li>回放截图 → <code>03_运行截图/</code></li>
<li>录屏 → <code>04_仿真录屏/</code></li>
<li>日志/代码 → <code>05_日志与代码摘录/</code></li>
<li>权重 → <code>06_模型权重_best/</code></li>
</ul>
</body>
</html>
""",
    encoding="utf-8",
)

zip_path = root / "于鸿伟_MotrixLab第四周_实操证据.zip"
if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in pack.rglob("*"):
        if f.is_file():
            zf.write(f, f.relative_to(pack_root).as_posix())

print("ZIP", zip_path)
print("size_MB", round(zip_path.stat().st_size / 1024 / 1024, 2))
print("files", sum(1 for x in pack.rglob("*") if x.is_file()))

over = []
for f in pack.rglob("*"):
    if not f.is_file():
        continue
    sz = f.stat().st_size
    if f.suffix.lower() in {".png", ".jpg", ".jpeg"} and sz > 10 * 1024 * 1024:
        over.append(("img>10MB", str(f), sz))
    if f.suffix.lower() in {".zip", ".py", ".pt", ".log", ".tar", ".gz"} and sz > 50 * 1024 * 1024:
        over.append(("eng>50MB", str(f), sz))
print("over_limit", over)
