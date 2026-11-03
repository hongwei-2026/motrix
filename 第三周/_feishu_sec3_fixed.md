## 三、代码阅读（40 分，每小题 10 分）

> 作答环境：`go1-flat-terrain-walk`（题目模板写 CartPole，本题按实际四足代码作答）。

### 1. 观测（10 分）

**（1）截图位置（3 分）**

文件：`motrix_envs/src/motrix_envs/locomotion/go1/walk_np.py`  
函数：`_init_obs_space()`（约 48–59 行）、`_get_obs()`（约 188–213 行）

<image token="DFtRbGwWDodqMFxshU1cDHbuntd" width="973" height="968" align="center"/>

**（2）各分量实际顺序（2 分）**

| 顺序 | 分量 | 维数 |
| --- | --- | ---: |
| 1 | `noisy_linvel` 局部线速度 | 3 |
| 2 | `noisy_gyro` 角速度 | 3 |
| 3 | `local_gravity` 局部重力方向 | 3 |
| 4 | `noisy_joint_angle` 关节角相对默认站姿偏差 | 12 |
| 5 | `noisy_joint_vel` 关节角速度 | 12 |
| 6 | `last_actions` 上一帧动作 | 12 |
| 7 | `command` 速度命令 `[vx, vy, vyaw]` | 3 |
| | **合计** | **48** |

**（3）物理含义与单位（3 分）**

| 分量 | 含义 | 单位（缩放前） |
| --- | --- | --- |
| 线速度 | 机体坐标系下基座线速度，再乘 `normalization.lin_vel=2` | m/s |
| 角速度 | 陀螺仪角速度，再乘 `ang_vel=0.25` | rad/s |
| 局部重力 | 重力方向转到机体坐标，反映姿态倾斜 | 无量纲方向向量 |
| 关节角偏差 | 当前关节角 − 默认站姿角，乘 `dof_pos=1` | rad |
| 关节速度 | 12 关节角速度，乘 `dof_vel=0.05` | rad/s |
| 上一动作 | 上一步策略输出的 12 维动作 | 与动作同量纲 |
| 速度命令 | 期望 `[vx,vy,vyaw]`，再乘 commands_scale | m/s、rad/s |

**（4）维度核对（2 分）**

`3+3+3+12+12+12+3 = 48`，与 `_init_obs_space` 中 `observation_space = Box(..., (48,))` 及 `assert num_obs == 48` 一致。

---

### 2. 动作（10 分）

**（1）截图位置（3 分）**

`walk_np.py` → `apply_action()`、`_compute_torques()`（约 160–174 行）

<image token="TfaTbbNwLoXbjIxauIlcRNGxnxb" width="960" height="440" align="center"/>

**（2）控制部件与物理量（3 分）**

控制 **12 个腿关节**（FR/FL/RR/RL 的 hip、thigh、calf）。策略输出是相对默认角的位置偏移；经 PD 后写入的物理量是 **关节力矩**（N·m），赋给 `state.data.actuator_ctrls`。

**（3）完整路径与裁剪/缩放（4 分）**

`策略输出 a (12维)`  
→ **训练 clip_actions：无**（`skrl/config.py` 默认 `clip_actions=False`；`tasks/go1.py` 未改为 True）  
→ **apply_action：有缩放** — `actions_scaled = a * action_scale`（`action_scale=0.05`）；再 PD：`τ = kp*(a_scaled + default_angles − q) − kd*q̇`（`kp=80, kd=1`）  
→ **执行器 XML：有 ctrlrange、无 gear** — 文件 `go1_motor_actuator.xml`：`ctrlrange="-23.7 23.7"`，未设置 `gear`  
→ **执行器施加关节力矩 τ**

路径：`策略输出 →（无 clip）→ ×0.05 → +默认角 → PD 得力矩 → 12 个 motor（±23.7）→ 关节力矩`

---

### 3. 奖励（10 分）

**（1）截图位置（2 分）**

`walk_np.py` → `update_reward()`（约 249–264 行）

<image token="Le49bdGzEoHIFFxsPhncasemnid" width="1099" height="462" align="center"/>

**（2）设每步奖励为 1、无折扣的累计奖励（各 2 分）**

- 持续 **20** 步：累计奖励 = `1 × 20 = **20**`
- 持续 **80** 步：累计奖励 = `1 × 80 = **80**`

**（3）为何能鼓励不倒/稳定（4 分）**

在“每步 +1”假设下：活得越久累计回报越大。对应 GO1：躯干触地会 `terminated`，且该步奖励置 0；不摔倒就能继续拿跟踪速度等正奖励，因此策略会被激励保持稳定、推迟失败。

---

### 4. 终止与截断（10 分）

| 题目情形 | 归类 | GO1 平地判据 |
| --- | --- | --- |
| ① 杆角度越界 | 失败终止（CartPole 语义） | GO1 无杆角判据；等价失败是 **躯干 trunk 触地** → `terminated=True` |
| ② 小车位置越界 | 失败终止（CartPole 语义） | GO1 平地 **未实现**位置越界终止 |
| ③ 状态正常但超时 | 时间截断 | `steps >= 2000`（`20.0/0.01`）→ `truncated=True` |

**截图：失败判定（2 分）**

`walk_np.py` → `update_terminated()`

<image token="NCZibbkl5onoJ1xKSz7c76lHnAf" width="960" height="330" align="center"/>

**截图：超时截断与自动重置（2 分）**

`np/env.py` → `_update_truncate()`、`_reset_done_envs()`、`step()`

<image token="CIqcb345No4G8pxOBd7cfnqZnVy" width="960" height="902" align="center"/>

**回合结束后谁重置（2 分）**

由环境基类在 `step()` 末尾调用 **`_reset_done_envs()`**；对 `done = terminated | truncated` 的环境，再调用子类 **`reset(data)`**（`walk_np.py`）。
