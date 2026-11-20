# 第八周 / MotrixArena 结营作业

学员：于鸿伟  
赛段：MotrixArena-S1 · `vbot_navigation_section01` · 走到 2026 平台  
算力：SeetaCloud · RTX 4090 · skrl（torch / jax）

本地包根目录：`D:\motrix\第八周`  
完整文件列表见 `文件清单.txt`。

## 目录

| 路径 | 内容 |
|------|------|
| `提交/` | 作业说明、国内源说明 |
| `代码/` | 训练/回放脚本、补丁脚本、环境 cfg、`policies/best_agent.pt` |
| `代码/cfgs/` | 远端 navigation/locomotion vbot 环境与 rl cfg 备份 |
| `代码/policies/` | known_policy（`best_agent.pt` + cfg） |
| `素材/` | 全部 mp4 / 截图 / 轨迹 csv / 关键日志 |
| `素材/frames/` | 视频关键帧截图 |
| `素材/logs/` | finish / train / play 日志 |
| `小红书/` | 文案 |

## 视频（`素材/`）

- `homework_traj.mp4` / `play_homework_traj.mp4` — 作业回放（max y≈0.53）
- `play_2026.mp4` / `play_trajectory_2026.mp4` — 朝 2026 平台长 rollout
- `play_mid_best_agent.mp4` — waypoint 中期 best_agent
- `play_kit54_*.mp4` — kit54 相关回放
- `bevy_3d_play.mp4` — Bevy 尝试（Vulkan 受限）

## 截图

- `homework_traj.png` · `homework_evidence_card.png`
- `xhs_traj_xy.png` · `xhs_progress_yz.png` · `xhs_reward.png` · `xhs_foot_force.png` · `xhs_evidence_card.png`
- `frames/hw_*.png` · `frames/p26_*.png`

## 当前进度

- 目标：`y ≈ 7.84`（2026 平台）
- 已知策略回放：`max_y ≈ 0.53`，尚未到达红线
- 无头容器（无桌面）上 Bevy 真 3D 窗口起不来；需换**带图形界面**的云主机/本地 NVIDIA 桌面再录屏

## 有桌面云主机上启动 3D 回放

在 MotrixLab 仓库根目录（已 `uv sync` / `.venv`）：

```bash
cd /path/to/MotrixLab
source .venv/bin/activate
export MOTRIX_HEADLESS=0
export JAX_PLATFORMS=cpu   # 或按环境调整
export DISPLAY=:0          # 按实际桌面显示号修改

python -u scripts/play.py \
  --env=vbot_navigation_section01 \
  --num-envs=1 \
  --policy=runs/.../checkpoints/best_agent.pickle
# 或使用本目录: 代码/policies/best_agent.pt（若 play 支持 pt）
```

有桌面后直接对本机窗口录屏即可，不必再走 VirtualGL / 无头 Xorg。
