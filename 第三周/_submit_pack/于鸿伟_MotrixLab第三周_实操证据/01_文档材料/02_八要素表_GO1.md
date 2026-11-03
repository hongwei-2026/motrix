# 二、八要素表（40 分）· Unitree GO1 平地行走

姓名：于鸿伟  
环境：`go1-flat-terrain-walk`（MotrixLab v0.3.0）  
原则：**以实际代码为准**；文档有写但代码未跑的，标「未实现」并注明查找位置。

---

| 要素 | 答案 | 来源 |
| ---- | ---- | ---- |
| **智能体** | ① 策略控制对象：Unitree GO1 四足机器人的 **12 个腿部关节**（每腿 hip / thigh / calf），经 PD 转成关节力矩驱动整机。② 策略接收 **48 维观测**；输出 **12 维动作**（相对默认站姿的关节位置偏移指令）。 | `docs/.../locomotion_unitree_go1.md` 任务描述 / 动作空间；`walk_np.py` → `apply_action`、`_compute_torques` |
| **环境** | ① 主要对象：GO1 机器人（躯干 `trunk` + 四腿）、平地 `floor`、灯光等场景元素。② 场景文件：`cfg.model_file` 指向 `motrix_envs/.../locomotion/go1/xmls/scene_motor_actuator.xml`（再 include `go1_motor_actuator.xml`）。 | `cfg.py` → `Go1WalkNpEnvCfg.model_file`；`xmls/scene_motor_actuator.xml` |
| **观测** | ① 共 **48 维**。② 排列与含义（按 `_get_obs` 拼接顺序）：线速度 3 + 角速度(gyro) 3 + 局部重力 3 + 关节角相对默认偏差 12 + 关节速度 12 + 上一帧动作 12 + 速度命令 `[vx,vy,vyaw]` 3。 | `walk_np.py` → `_init_obs_space`（`assert num_obs == 48`）、`_get_obs`；文档观测表 |
| **动作** | ① **12 维**；代码里 `action_space` 来自模型 `actuator_ctrl_limits`（XML motor `ctrlrange` 为 **[-23.7, 23.7]**）。② 作用在 **12 个腿关节执行器**；语义为相对默认角的位置偏移，经 `action_scale=0.05` 与 PD（`kp=80, kd=1`）变成 **关节力矩** 写入 `actuator_ctrls`。 | `walk_np.py` → `_init_action_space`、`_compute_torques`；`cfg.py` → `ControlConfig`；`xmls/go1_motor_actuator.xml` → `<actuator>` |
| **奖励** | ① 各子项按 `RewardConfig.scales` 加权求和，再 `clip` 到 `[0, 10000]`；若 `terminated` 则该步奖励置 **0**。主要正项：线/角速度跟踪、腾空时间；负项：竖直速度、横滚俯仰角速度、力矩、加速度、动作变化率、髋关节偏离等。② 鼓励：**跟踪速度命令、稳定协调步态、少晃动少乱扭矩**。 | `walk_np.py` → `update_reward`、`_get_reward`；`cfg.py` → `RewardConfig` |
| **初始状态** | ① 基座目标位姿配置为 `pos=[0,0,0.42]`；12 关节角为默认站姿（如 thigh=0.9、calf=-1.8 等，见 `InitState.default_joint_angles`）。`reset` 用 `_init_dof_pos`（末 12 维写默认角）设关节。文档写的关节角噪声 **[-0.125, 0.125]：代码未实现**（`reset` 中无加噪）。② 速度：`_init_dof_vel` 全 **0**。 | `cfg.py` → `InitState`；`walk_np.py` → `reset`、`_init_buffer`；文档「初始状态」对照 |
| **终止条件** | ① **失败**：躯干 `trunk` 与地面 `floor` 发生接触 → `terminated=True`。（文档另写「线速度平方和>1e8」；**平地 `walk_np.py` 未实现**，该判断只在 rough/stairs 变体里。）② **截断**：`max_episode_seconds=20.0`，`ctrl_dt=0.01` → `max_episode_steps = 20/0.01 = **2000** 步；步数 ≥ 2000 时 `truncated=True`。 | `cfg.py` → `Asset.terminate_after_contacts_on`、`max_episode_seconds`、`ctrl_dt`；`walk_np.py` → `update_terminated`；`base.py` → `max_episode_steps`；`np/env.py` → `_update_truncate` |
| **域随机化** | ① **已实现**：速度命令 `commands` 在范围内均匀采样——`vx∈[-1,2]`，`vy∈[-1,1]`，`vyaw∈[-1,1]`（单位 m/s 或 rad/s）。`NoiseConfig`（观测噪声尺度）在 cfg 有定义，但 **`walk_np.py` 观测未加随机噪声 → 未实现**。关节重置噪声、质量/摩擦等 DR → **未实现**（已查 `walk_np.py` 的 `reset`/`_get_obs`）。② **重新采样时机**：每个环境在 **`reset` 时**调用 `resample_commands`（回合开始 / 失败或截断后重置时）。 | `walk_np.py` → `resample_commands`、`reset`；`cfg.py` → `Commands`、`NoiseConfig` |

---

## 换算备忘（终止条件第②问）

`max_episode_steps = max_episode_seconds / ctrl_dt = 20.0 / 0.01 = 2000`

---

## 未实现项汇总（便于批改核对）

| 文档/配置里有、平地代码未用 | 查找位置 |
| --------------------------- | -------- |
| 关节角重置噪声 ±0.125 | 文档「初始状态」；`walk_np.py` → `reset` 无对应采样 |
| 观测噪声 `NoiseConfig` | `cfg.py` 有类；`walk_np.py` → `_get_obs` 仅做归一化缩放，无 `np.random` |
| 超速终止 `>1e8` | 文档「终止条件」；仅 `walk_rough_terrain.py` / `walk_stairs_terrain.py` 有 |
