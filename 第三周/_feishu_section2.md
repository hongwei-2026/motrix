## 二、八要素表（40 分）

制作一张三列表格，列名为“要素｜答案｜来源”，共 8 行。**评分**：每行 5 分（两个问题各 2 分，来源 1 分）。

**作答环境**：`go1-flat-terrain-walk`（Unitree GO1，MotrixLab v0.3.0）。以实际代码为准；未实现处已注明。

| 要素 | 答案 | 来源 |
| --- | --- | --- |
| 智能体 | ① 控制对象：GO1 的 12 个腿部关节（每腿 hip/thigh/calf），经 PD 转成关节力矩驱动整机。<br>② 策略接收 48 维观测；输出 12 维动作（相对默认站姿的关节位置偏移）。 | `locomotion_unitree_go1.md`；`walk_np.py` → `apply_action`、`_compute_torques` |
| 环境 | ① 主要对象：GO1（躯干 trunk + 四腿）、平地 floor、灯光等。<br>② 场景由 `cfg.model_file` 加载：`motrix_envs/.../go1/xmls/scene_motor_actuator.xml`（再 include `go1_motor_actuator.xml`）。 | `cfg.py` → `Go1WalkNpEnvCfg.model_file`；`scene_motor_actuator.xml` |
| 观测 | ① 共 48 维。<br>② 顺序：线速度3 + 角速度(gyro)3 + 局部重力3 + 关节角相对默认偏差12 + 关节速度12 + 上一帧动作12 + 速度命令[vx,vy,vyaw]3。 | `walk_np.py` → `_init_obs_space`、`_get_obs` |
| 动作 | ① 12 维；`action_space` 来自 `actuator_ctrl_limits`（XML motor ctrlrange **[-23.7, 23.7]**）。<br>② 作用于 12 个腿关节执行器；语义为相对默认角的位置偏移，经 `action_scale=0.05` 与 PD（kp=80, kd=1）变成关节力矩写入 `actuator_ctrls`。 | `walk_np.py` → `_init_action_space`、`_compute_torques`；`cfg.py` → `ControlConfig`；`go1_motor_actuator.xml` |
| 奖励 | ① 各子项按 `RewardConfig.scales` 加权求和，再 clip 到 [0,10000]；若 terminated 则该步奖励置 0。正项含线/角速度跟踪、腾空时间；负项含竖直速度、力矩、加速度、动作变化率、髋关节偏离等。<br>② 鼓励：跟踪速度命令、稳定协调步态、少晃动少乱扭矩。 | `walk_np.py` → `update_reward`、`_get_reward`；`cfg.py` → `RewardConfig` |
| 初始状态 | ① 基座位姿配置 `pos=[0,0,0.42]`；12 关节为默认站姿（如 thigh=0.9、calf=-1.8，见 `InitState.default_joint_angles`）。文档写的关节噪声 [-0.125,0.125]：**代码未实现**（`reset` 无加噪）。<br>② 速度：`_init_dof_vel` 全 0。 | `cfg.py` → `InitState`；`walk_np.py` → `reset`、`_init_buffer` |
| 终止条件 | ① 失败：躯干 trunk 与地面 floor 接触 → terminated=True。文档另写超速>1e8：**平地 walk_np.py 未实现**（仅 rough/stairs 有）。<br>② 截断：max_episode_seconds=20.0，ctrl_dt=0.01 → max_episode_steps=20/0.01=**2000**；步数≥2000 时 truncated=True。 | `cfg.py`；`walk_np.py` → `update_terminated`；`base.py` → `max_episode_steps`；`np/env.py` → `_update_truncate` |
| 域随机化 | ① 已实现：速度命令 commands 均匀采样，vx∈[-1,2]，vy∈[-1,1]，vyaw∈[-1,1]。`NoiseConfig` 观测噪声、关节重置噪声、质量/摩擦 DR：**未实现**（已查 `walk_np.py` 的 reset/_get_obs）。<br>② 在 **reset** 时调用 `resample_commands` 重新采样。 | `walk_np.py` → `resample_commands`、`reset`；`cfg.py` → `Commands`、`NoiseConfig` |

以实际代码为准；代码里没有实现的要素，写“未实现”，并注明查找位置。