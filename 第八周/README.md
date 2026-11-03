# 第八周 / MotrixArena 结营作业

学员：于鸿伟  
赛段：MotrixArena-S1 · `vbot_navigation_section01` · 走到 2026 平台

## 目录

| 路径 | 内容 |
|------|------|
| `提交/` | 作业说明、国内源说明 |
| `代码/` | 观测 67 维 / 足底力补丁、play 有限步日志、本地出片脚本 |
| `素材/` | `play_2026.mp4`、轨迹 csv、小红书配图 |
| `小红书/` | 文案 |

## 关键命令（VM）

```bash
cd /root/work/MotrixLab
uv run scripts/play.py \
  --env=vbot_navigation_section01 \
  --num-envs=1 \
  --policy=runs/vbot_navigation_section01/<RUN>/checkpoints/best_agent.pickle
```

## 状态说明（诚实记录）

- 已跑通 GPU play + 轨迹证据；当前 `play_2026.mp4` 为轨迹动画版。
- Bevy 三维窗口实拍、真正踏上 2026（y≈7.84）仍待继续：足底接触力需只用 `*_1/_2/_3` 传感器（无后缀名会 Rust panic）。
- 补丁入口：`代码/_patch_env_force.py`、`代码/vm_vbot_section01_np.py`
