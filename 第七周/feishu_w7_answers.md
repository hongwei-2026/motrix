# 第七周答题卡（于鸿伟）

### 一、选择题（40 分）

| 题号 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 答案 | B | D | A | C | B | A | D | C | A | D |

### 二、基础实操（30 分）

训练命令：

```plaintext
uv run --extra cuda --extra tbb --extra rslrl scripts/train.py \
  task=go1-waypoint-flat/rslrl.ppo num_envs=32 algo.max_iterations=20 seed=42 checkpoint.interval=10
```

- 运行目录：`runs/go1-waypoint-flat/rslrl/torch/ppo/26-10-30_08-23-40-867714`
- checkpoint：`.../checkpoints/latest.pt`
- TensorBoard：`Loss/value`
- 回放：`scripts/play.py env=go1-waypoint-flat policy=.../latest.pt num_envs=1 seed=42`
- 行为：短训下可能朝 A 方向有运动/摇晃，未必完成 B、C（如实记录）。

### 三、slow_radius A/B

#### （a）定位

- cfg：`go1_waypoint/cfg.py` → `WaypointTaskCfg.slow_radius`
- env：`Go1WaypointFlatTask._update_goal_commands()` 传入 `slow_radius=task.slow_radius`
- logic：`logic.command_from_target()` 用 `approach_factor = clip(distance/slow_radius,0,1)` 缩放平移指令
- 预测：`slow_radius` 变大后，同一距离的 approach_factor 变小，靠近目标时前进指令更保守。

#### （b）计算

目标前方 0.4 m，`linear_kp=0.8`，`max_forward=0.6`，`heading_factor=1`

- A `slow_radius=0.8`：approach=0.4/0.8=0.5；vx=clip(0.32,-0.6,0.6)*0.5=**0.16**
- B `slow_radius=1.6`：approach=0.4/1.6=0.25；vx=0.32*0.25=**0.08**

#### （c）回放

- A：`[slow-radius-check] 0.8`
- B：`[slow-radius-check] 1.6`
- 同一 checkpoint；结束后恢复 0.8。

#### （d）结论

指令层面 B 更慢符合计算；实际速度未必同比例。只改 `logic.py` 默认参数、保留 cfg 与 env 显式传参时，环境仍用 cfg 传入值，不会采用新默认。
