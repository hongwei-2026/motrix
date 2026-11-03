# 第六周答题卡（于鸿伟）

### 一、选择题（40 分）

| 题号 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 答案 | B | C | A | D | B | C | A | D | B | C |

说明：第 8 题 `3/0.02=150` 步 → D；第 9 题 `0.5+0.275=0.775` → B。

### 二、基础实操（30 分）

训练命令：

```plaintext
uv run --extra cuda --extra tbb --extra rslrl scripts/train.py \
  task=go1-slope-platform/rslrl.ppo num_envs=32 algo.max_iterations=20 seed=42 checkpoint.interval=10
```

- 运行目录：`runs/go1-slope-platform/rslrl/torch/ppo/26-10-30_08-23-12-580158`
- checkpoint：`.../checkpoints/latest.pt`
- TensorBoard：`Loss/value`（短训有波动）
- 回放：`scripts/play.py env=go1-slope-platform policy=.../latest.pt num_envs=1 seed=42`
- 行为：短训策略可能未稳定上坡/停稳；已如实观察并保留画面。

### 三、max_speed A/B

#### （a）定位

- cfg：`go1_slope_platform/cfg.py` → `PlatformTaskCfg.max_speed`（属 `Go1SlopePlatformEnvCfg.platform_task`）
- env：`go1_slope_platform/env.py` → `Go1SlopePlatformTask._update_goal_commands()` 使用 `task.max_speed`
- 预测：远离目标时指令速度上限减半；实际速度未必同比例变化。

#### （b）计算

`position_gain=0.8`，`stop_radius=0.25`，yaw=0

| 目标相对位置 | v_raw | A (max=0.5) | B (max=0.25) |
| --- | --- | --- | --- |
| [2.0, 0.0] | [1.6, 0] | [0.5, 0, 0] | [0.25, 0, 0] |
| [0.3, 0.0] | [0.24, 0] | [0.24, 0, 0] | [0.24, 0, 0] |

第一种触发限速；第二种 ||v_raw||=0.24 低于两档上限。

#### （c）回放日志

- A：`[max-speed-check] 0.5`
- B：`[max-speed-check] 0.25`
- 同一 checkpoint，seed=42，num_envs=1；结束后已恢复 0.5。

#### （d）结论

指令上限确随 `max_speed` 变化；实际机身速度还受策略与动力学约束，不能断言按相同比例下降。
