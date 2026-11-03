# 第五周答题卡（于鸿伟）

### 一、选择题（40 分）

| 题号 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 答案 | B | C | A | D | B | A | C | D | A | B |

### 二、基础实操（30 分）

#### （a）小规模训练与模型文件

训练命令：

```plaintext
uv run --extra cuda --extra tbb --extra rslrl scripts/train.py \
  task=go1-walk-flat/rslrl.ppo num_envs=64 algo.max_iterations=30 seed=42 checkpoint.interval=10
```

- 训练是否正常结束：是（Learning iteration 0–29 / 30，Training completed）
- 本次运行目录：`runs/go1-walk-flat/rslrl/torch/ppo/26-10-30_08-18-55-603922`
- checkpoint：`.../checkpoints/latest.pt`

#### （b）TensorBoard 曲线

```plaintext
uv run --extra cuda --extra tbb --extra rslrl tensorboard --logdir runs/go1-walk-flat
```

- 指标：`Loss/value`
- 观察：短训 30 iter，Loss/value 有波动但整体可记录，尚未充分收敛（小规模练习正常）。

#### （c）策略回放

```plaintext
uv run --extra cuda --extra tbb --extra rslrl scripts/play.py \
  env=go1-walk-flat \
  policy=runs/go1-walk-flat/rslrl/torch/ppo/26-10-30_08-18-55-603922/checkpoints/latest.pt \
  num_envs=1 seed=42 record_video=true record_seconds=6
```

- 现象：成功加载策略；机身尝试抬腿/迈步；短训下仍可能摇晃或跌倒（如实记录）。

### 三、参数拓展：action_scale A/B

#### （a）定位与预测

- cfg：`motrix_envs/.../quadruped/go1.py` → `Go1WalkDirectEnvCfg.control_config = ControlConfig(action_scale=0.1)`
- env：`motrix_envs/.../quadruped/walk_np.py` → `targets = exec_actions * action_scale + default_angles`
- 预测：`action_scale` 减半后，相同动作下相对默认角的偏移减半。

#### （b）计算

相同输入：默认角 0.9 rad，exec_action=0.5

| 组别 | action_scale | 关节位置目标（rad） | 相对默认偏移（rad） |
| --- | --- | --- | --- |
| A | 0.1 | 0.95 | 0.05 |
| B | 0.05 | 0.925 | 0.025 |

过程：`target = 0.9 + scale * 0.5`；B 偏移为 A 的一半。

#### （c）A/B 回放

同一 checkpoint：`.../26-10-30_08-18-55-603922/checkpoints/latest.pt`；`seed=42`，`num_envs=1`，约 6–8 s。

- A：`[action-scale-check] 0.1`
- B：`[action-scale-check] 0.05`
- 已恢复默认 `0.1`

#### （d）结论

观测与预测一致：配置缩放会直接改变目标角偏移，但固定策略下实际关节运动/行走速度不必按相同比例变化。本次是对固定策略的执行参数干预，不能据此断言 B 重新训练后一定更好。
