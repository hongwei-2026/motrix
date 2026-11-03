#!/usr/bin/env python3
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

root = Path(r"D:\motrix\第三周")
pack_root = root / "_submit_pack"
pack = pack_root / "于鸿伟_MotrixLab第三周_实操证据"

if pack_root.exists():
    shutil.rmtree(pack_root)
pack.mkdir(parents=True)

dirs = {
    "doc": pack / "01_文档材料",
    "shot": pack / "02_代码与运行截图",
    "xhs": pack / "03_小红书素材",
}
for d in dirs.values():
    d.mkdir(parents=True)

# answer docs
for src, name in [
    (root / "八要素表_GO1.md", "02_八要素表_GO1.md"),
    (root / "第2题_一回合交互流程图.md", "01_一回合交互流程图.md"),
    (root / "第3题_terminated与truncated.md", "03_terminated与truncated.md"),
    (root / "第3部分_代码阅读_GO1.md", "04_代码阅读_GO1.md"),
]:
    if src.exists():
        shutil.copy2(src, dirs["doc"] / name)

# screenshots
shot_dir = root / "截图"
shot_map = {
    "01_观测_get_obs.png": "01_观测_get_obs.png",
    "02_动作_apply_action.png": "02_动作_apply_action.png",
    "03_奖励_update_reward.png": "03_奖励_update_reward.png",
    "04_失败终止_update_terminated.png": "04_失败终止_update_terminated.png",
    "05_截断与重置_env.png": "05_截断与重置_env.png",
}
for a, b in shot_map.items():
    p = shot_dir / a
    if p.exists():
        shutil.copy2(p, dirs["shot"] / b)

# xhs
xhs = root / "小红书"
if xhs.exists():
    for f in xhs.iterdir():
        if f.is_file():
            shutil.copy2(f, dirs["xhs"] / f.name)

readme = """# 于鸿伟 · MotrixLab 第三周实操证据包

- **课程周次**：第三周（环境八要素 · Unitree GO1 平地行走）
- **环境**：`go1-flat-terrain-walk`
- **代码版本**：MotrixLab **v0.3.0**
- **说明**：本周以读代码 / 填表 / 流程图为主，**不要求训练录屏**；证据以文档 + 代码截图为主。
- **飞书作业**：https://ccnz793r59f8.feishu.cn/wiki/NO7PwbbhZiz2ZRkuXHZclBhwnGf

## 目录对照提交渠道

| 文件夹 | 对应提交项 | 格式 |
|--------|------------|------|
| `01_文档材料` | Word/文档材料 | `.md` / `.html`（可另存 PDF/DOCX） |
| `02_代码与运行截图` | 运行截图 | `.png`（均 < 10MB） |
| `03_小红书素材` | 可选补充图文 | `.md` / `.png` |

> 本周无仿真训练 mp4；若平台必传视频项，可用飞书文档内已贴图说明「本周不要求训练」，或上传小红书配图作过程记录。

## 关键数值（可粘贴到文本框）

```text
env = go1-flat-terrain-walk
MotrixLab = v0.3.0
obs_dim = 48 = linvel3 + gyro3 + gravity3 + joint_pos12 + joint_vel12 + last_action12 + cmd3
action_dim = 12
action_scale = 0.05
PD: kp=80, kd=1
motor ctrlrange = [-23.7, 23.7]
terminated: trunk contact floor
truncated: max_episode_seconds=20.0 / ctrl_dt=0.01 = 2000 steps
commands resample on reset: vx[-1,2], vy[-1,1], vyaw[-1,1]
文档有、平地未实现: 关节重置噪声±0.125; 观测 NoiseConfig; 超速终止>1e8
```

## 文档索引

1. `01_一回合交互流程图.md` — 第2题流程图 + 四条关系
2. `02_八要素表_GO1.md` — 第2题八要素表
3. `03_terminated与truncated.md` — 第3题
4. `04_代码阅读_GO1.md` — 第3部分代码阅读

## 截图索引

1. 观测 `_get_obs`
2. 动作 `apply_action` / PD
3. 奖励 `update_reward`
4. 失败终止 `update_terminated`
5. 截断与重置 `np/env.py`

## 在线链接

- 飞书：https://ccnz793r59f8.feishu.cn/wiki/NO7PwbbhZiz2ZRkuXHZclBhwnGf
- 上游：https://github.com/Motphys/MotrixLab（tag v0.3.0）
"""
(dirs["doc"] / "00_提交说明_README.md").write_text(readme.lstrip(), encoding="utf-8")

(dirs["doc"] / "关键数值_可粘贴.txt").write_text(
    "\n".join(
        [
            "env=go1-flat-terrain-walk | MotrixLab v0.3.0",
            "obs=48 = linvel3+gyro3+gravity3+joint_pos12+joint_vel12+last_action12+cmd3",
            "action=12 | action_scale=0.05 | PD kp=80 kd=1 | ctrlrange=[-23.7,23.7]",
            "terminated: trunk-floor contact",
            "truncated: 20.0/0.01=2000 steps",
            "commands on reset: vx[-1,2] vy[-1,1] vyaw[-1,1]",
            "未实现(平地): joint reset noise; obs NoiseConfig; speed>1e8 terminate",
            "飞书: https://ccnz793r59f8.feishu.cn/wiki/NO7PwbbhZiz2ZRkuXHZclBhwnGf",
            "",
        ]
    ),
    encoding="utf-8",
)

(dirs["doc"] / "作业索引.html").write_text(
    """<!DOCTYPE html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>于鸿伟 · 第三周证据索引</title>
<body style="font-family:sans-serif;max-width:720px;margin:2rem auto;line-height:1.6">
<h1>于鸿伟 · MotrixLab 第三周实操证据</h1>
<p>环境：<code>go1-flat-terrain-walk</code> · v0.3.0</p>
<p>请先阅读 <code>00_提交说明_README.md</code>。</p>
<p>飞书：
<a href="https://ccnz793r59f8.feishu.cn/wiki/NO7PwbbhZiz2ZRkuXHZclBhwnGf">打开作业文档</a></p>
<ul>
<li>答题文档 → <code>01_文档材料/</code></li>
<li>代码截图 → <code>02_代码与运行截图/</code></li>
<li>小红书 → <code>03_小红书素材/</code></li>
</ul>
</body>
</html>
""",
    encoding="utf-8",
)

zip_path = root / "于鸿伟_MotrixLab第三周_实操证据.zip"
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
        over.append(("img>10MB", f.name, sz))
print("over_limit", over)
