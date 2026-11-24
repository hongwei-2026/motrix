# Section01 到达 2026 平台：2026-11-24 验收通过

云端已使用原 LM `best_agent.pt`、原地形与真实物理步进走到 2026 平台。种子 `0–9、42` 共 11 次，每次完整运行 8000 步（80 秒仿真时间），全部通过，翻滚与跌倒重置均为 0。到达平台后连续保持 66.22–66.75 秒。

## 根因与修复

项目 `uv.lock` 锁定 `motrixsim==0.5.0b2`，此前系统 Python 实际加载了 `1.0.0`。更换仿真版本后，同一权重的步态、接触观测和地形通过结果发生实质变化。已将 `0.5.0b2` 安装到独立路径，并在回放命令中明确优先加载它。

环境还会在距离终点小于 `0.45 m` 时提前判定成功并重置；原始回放实测到 `y=7.635` 就被送回出生点。现在终点阈值改为 `0.10 m`，回放到达目标后继续保留物理状态，并延长训练环境的 4000 步时间上限，使机器人能在平台上持续停留。跌倒、非数值、关节速度与机身速度异常的终止条件继续生效。

策略输入保持原来的 68 维，动作比例保持 `0.45`，使用真实接触传感器。回放没有填充观测、修改地形、传送机器狗或施加额外推力。CPU 推理结果已与原 SKRL 策略对照，初始动作最大误差为 `0.0`。

## 云端一键复测

当前云主机已经部署所有文件与离线安装包：

```bash
bash /root/autodl-tmp/codex_section01/run_2026.sh
```

默认种子 42 的完整结果：

```text
REACH_2026=True
FLIPPED_STEPS=0
FALL_RESETS=0
FINAL_POSITION=[-2.6906116, 8.1340942, 1.5341052]
FINAL_UPRIGHT_GZ=-0.9817706
ACCEPTANCE_PASS=True
```

首次进入平台验收区域：第 1345 步（13.45 秒仿真时间），当时位置 `[-2.5639, 7.8038, 1.6067]`。最大 Y 为 `8.20543`，随后留在平台至第 8000 步，连续满足平台与直立条件 6656 步。

结果保存到 `/root/autodl-tmp/codex_section01/latest_result.json`。验收在自动重置前读取机身姿态；要求 `y` 在 `[7.8, 8.6]`、`x` 在 `[-3.7, -1.7]`、机身高度在 `(1.45, 2.15)` 且投影重力 Z 小于 `-0.8`。一键命令还要求运行结束时仍在平台、翻滚与跌倒重置均为 0。

更换随机种子：

```bash
bash /root/autodl-tmp/codex_section01/run_2026.sh --seed 7
```

有桌面的主机可用同一脚本加 `--render` 打开 Bevy 窗口；当前云端只验证了无头 3D 物理回放。

## 文件与环境

- `run_2026.sh`：固定仿真版本并输出最终验收结果。
- `section01_rollout.py`：CPU 策略回放、重置前测量、平台停留验收；在云端名为 `rollout.py`。
- `section01_acceptance_2026-11-24.json`：11 个随机种子的验收数据。
- 云端 Python：`/root/miniconda3/bin/python`（3.12），Torch `2.8.0+cu128`，NumPy `2.3.2`。
- 旧版仿真：`/root/autodl-tmp/codex_section01/runtime050b2`。
- 云端项目：`/root/autodl-tmp/MotrixLab`。
- 权重：`runs/vbot_navigation_section01/known_success_PPO/checkpoints/best_agent.pt`。
- 权重 SHA256：`d0f9541e5f81f36e8b32ddd0ab9dcf048a977db47a09d3a8516054f7ed40a4cb`。

请使用上述固定版本的新入口复测；原来的系统 Python 播放命令仍会默认找到 `1.0.0`。
