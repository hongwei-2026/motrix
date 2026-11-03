# 第三周作业：CartPole 环境分析
**满分 100 分**
## 作业须知
- **代码版本**：以 MotrixLab v0.3.0 为准。课件代码与仓库不一致时，以仓库为准，并在答案中注明。
- **提交方式**：每周提交一份作业文档（PDF 或 DOCX），按题号作答；截图直接贴在文档中，视频随文档一起提交（MP4 或可访问的链接）。
- **截图和视频**：内容清晰，能看出对应的是哪道题、哪个任务。代码截图要能看到文件名。
- **来源写法**：写“文件路径 + 函数名”即可，例如 `cartpole_np.py update_state()`。
---

## **本周目标**：按照第 8 讲介绍的分析方法，把 CartPole 拆解为强化学习八要素，并在代码中找到每个要素的实现位置。**说明**：本周不要求训练。
## 一、任务与交互流程（20 分）
**1.** 用一句话回答以下两问（每问 2 分，共 4 分）：
- 策略输出的动作直接作用于哪个部件？答：直接作用于四条腿共 12 个关节（每腿 hip / thigh / calf），以相对默认站姿的位置偏移为指令，经 PD 控制器转换为关节力矩。**动作空间（Action Space）**

<lark-table rows="3" cols="2" header-row="true" column-widths="350,350">

  <lark-tr>
    <lark-td>
      项目
    </lark-td>
    <lark-td>
      详细信息
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      类型
    </lark-td>
    <lark-td>
      Box（代码以 actuator_ctrl_limits 为准；XML motor ctrlrange 为 [-23.7, 23.7]）
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      维度
    </lark-td>
    <lark-td>
      12
    </lark-td>
  </lark-tr>
</lark-table>

动作对应 12 个关节的位置控制指令（相对于默认站立姿态的偏移量），包括：

<lark-table rows="5" cols="3" header-row="true" column-widths="244,244,244">

  <lark-tr>
    <lark-td>
      序号 {align="right"}
    </lark-td>
    <lark-td>
      动作含义（关节位置变化）
    </lark-td>
    <lark-td>
      对应肢体 {align="center"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      0–2 {align="right"}
    </lark-td>
    <lark-td>
      髋关节、大腿关节、小腿关节
    </lark-td>
    <lark-td>
      前右腿 FR {align="center"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      3–5 {align="right"}
    </lark-td>
    <lark-td>
      髋关节、大腿关节、小腿关节
    </lark-td>
    <lark-td>
      前左腿 FL {align="center"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      6–8 {align="right"}
    </lark-td>
    <lark-td>
      髋关节、大腿关节、小腿关节
    </lark-td>
    <lark-td>
      后右腿 RR {align="center"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      9–11 {align="right"}
    </lark-td>
    <lark-td>
      髋关节、大腿关节、小腿关节
    </lark-td>
    <lark-td>
      后左腿 RL {align="center"}
    </lark-td>
  </lark-tr>
</lark-table>

- GO1 任务希望机器人保持什么状态？答：躯干保持直立不倒，并以稳定步态跟踪给定的速度命令（前进 / 侧移 / 转向）。**2.** 画出一个回合的交互流程图，包含以下环节：`reset`、观测、策略、动作、`step`、奖励、结束判断。（共 12 分）用箭头表示以下四条关系，每条 3 分：
1. 初始观测从哪里来；
1. 动作传给了谁；
1. 新观测怎样用于下一步；
1. 回合结束后怎样重新开始。绘图工具不限，手绘拍照也可以。**3.** `terminated` 和 `truncated` 分别表示什么？各举一个会触发它的情形。（每个标志：含义 1 分，例子 1 分，共 4 分）**terminated**
- 含义：任务失败导致回合自然结束。
- 例子：GO1 躯干撞地摔倒。**truncated**
- 含义：到最大时长/步数被截断，不是失败。
- 例子：一直正常走，但跑满约 20 秒（`max_episode_seconds = 20`）。
---

## 二、八要素表（40 分）
制作一张三列表格，列名为“要素｜答案｜来源”，共 8 行。**评分**：每行 5 分（两个问题各 2 分，来源 1 分）。**作答环境**：`go1-flat-terrain-walk`（Unitree GO1，MotrixLab v0.3.0）。以实际代码为准；未实现处已注明。

<lark-table rows="9" cols="3" header-row="true" column-widths="244,244,244">

  <lark-tr>
    <lark-td>
      要素
    </lark-td>
    <lark-td>
      答案
    </lark-td>
    <lark-td>
      来源
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      智能体
    </lark-td>
    <lark-td>
      ① 控制对象：GO1 的 12 个腿部关节（每腿 hip/thigh/calf），经 PD 转成关节力矩驱动整机。② 策略接收 48 维观测；输出 12 维动作（相对默认站姿的关节位置偏移）。
    </lark-td>
    <lark-td>
      `locomotion_unitree_go1.md`；`walk_np.py` → `apply_action`、`_compute_torques`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      环境
    </lark-td>
    <lark-td>
      ① 主要对象：GO1（躯干 trunk + 四腿）、平地 floor、灯光等。② 场景由 `cfg.model_file` 加载：`motrix_envs/.../go1/xmls/scene_motor_actuator.xml`（再 include `go1_motor_actuator.xml`）。
    </lark-td>
    <lark-td>
      `cfg.py` → `Go1WalkNpEnvCfg.model_file`；`scene_motor_actuator.xml`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      观测
    </lark-td>
    <lark-td>
      ① 共 48 维。② 顺序：线速度3 + 角速度(gyro)3 + 局部重力3 + 关节角相对默认偏差12 + 关节速度12 + 上一帧动作12 + 速度命令[vx,vy,vyaw]3。
    </lark-td>
    <lark-td>
      `walk_np.py` → `_init_obs_space`、`_get_obs`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      动作
    </lark-td>
    <lark-td>
      ① 12 维；`action_space` 来自 `actuator_ctrl_limits`（XML motor ctrlrange **[-23.7, 23.7]**）。② 作用于 12 个腿关节执行器；语义为相对默认角的位置偏移，经 `action_scale=0.05` 与 PD（kp=80, kd=1）变成关节力矩写入 `actuator_ctrls`。
    </lark-td>
    <lark-td>
      `walk_np.py` → `_init_action_space`、`_compute_torques`；`cfg.py` → `ControlConfig`；`go1_motor_actuator.xml`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      奖励
    </lark-td>
    <lark-td>
      ① 各子项按 `RewardConfig.scales` 加权求和，再 clip 到 [0,10000]；若 terminated 则该步奖励置 0。正项含线/角速度跟踪、腾空时间；负项含竖直速度、力矩、加速度、动作变化率、髋关节偏离等。② 鼓励：跟踪速度命令、稳定协调步态、少晃动少乱扭矩。
    </lark-td>
    <lark-td>
      `walk_np.py` → `update_reward`、`_get_reward`；`cfg.py` → `RewardConfig`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      初始状态
    </lark-td>
    <lark-td>
      ① 基座位姿配置 `pos=[0,0,0.42]`；12 关节为默认站姿（如 thigh=0.9、calf=-1.8，见 `InitState.default_joint_angles`）。文档写的关节噪声 [-0.125,0.125]：**代码未实现**（`reset` 无加噪）。② 速度：`_init_dof_vel` 全 0。
    </lark-td>
    <lark-td>
      `cfg.py` → `InitState`；`walk_np.py` → `reset`、`_init_buffer`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      终止条件
    </lark-td>
    <lark-td>
      ① 失败：躯干 trunk 与地面 floor 接触 → terminated=True。文档另写超速>1e8：**平地 walk_np.py 未实现**（仅 rough/stairs 有）。② 截断：max_episode_seconds=20.0，ctrl_dt=0.01 → max_episode_steps=20/0.01=**2000**；步数≥2000 时 truncated=True。
    </lark-td>
    <lark-td>
      `cfg.py`；`walk_np.py` → `update_terminated`；`base.py` → `max_episode_steps`；`np/env.py` → `_update_truncate`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      域随机化
    </lark-td>
    <lark-td>
      ① 已实现：速度命令 commands 均匀采样，vx∈[-1,2]，vy∈[-1,1]，vyaw∈[-1,1]。`NoiseConfig` 观测噪声、关节重置噪声、质量/摩擦 DR：**未实现**（已查 `walk_np.py` 的 reset/_get_obs）。② 在 **reset** 时调用 `resample_commands` 重新采样。
    </lark-td>
    <lark-td>
      `walk_np.py` → `resample_commands`、`reset`；`cfg.py` → `Commands`、`NoiseConfig`
    </lark-td>
  </lark-tr>
</lark-table>

[[SHOT_TRUNC]]以实际代码为准；代码里没有实现的要素，写“未实现”，并注明查找位置。
## 三、代码阅读（40 分，每小题 10 分）
> 作答环境：go1-flat-terrain-walk（题目模板写 CartPole，本题按实际四足代码作答）。
### 1. 观测（10 分）
**（1）截图位置（3 分）**文件：motrix_envs/.../go1/walk_np.py函数：_init_obs_space()（约 48-59 行）、_get_obs()（约 188-213 行）
<image token="Q3nmbjWaXoCc4oxiNwPc97fMnge" width="973" height="968" align="center"/>

**（2）各分量实际顺序（2 分）**

<lark-table rows="9" cols="3" header-row="true" column-widths="244,244,244">

  <lark-tr>
    <lark-td>
      顺序
    </lark-td>
    <lark-td>
      分量
    </lark-td>
    <lark-td>
      维数 {align="right"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      1
    </lark-td>
    <lark-td>
      noisy_linvel 局部线速度
    </lark-td>
    <lark-td>
      3 {align="right"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      2
    </lark-td>
    <lark-td>
      noisy_gyro 角速度
    </lark-td>
    <lark-td>
      3 {align="right"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      3
    </lark-td>
    <lark-td>
      local_gravity 局部重力方向
    </lark-td>
    <lark-td>
      3 {align="right"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      4
    </lark-td>
    <lark-td>
      noisy_joint_angle 关节角相对默认站姿偏差
    </lark-td>
    <lark-td>
      12 {align="right"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      5
    </lark-td>
    <lark-td>
      noisy_joint_vel 关节角速度
    </lark-td>
    <lark-td>
      12 {align="right"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      6
    </lark-td>
    <lark-td>
      last_actions 上一帧动作
    </lark-td>
    <lark-td>
      12 {align="right"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      7
    </lark-td>
    <lark-td>
      command 速度命令 [vx, vy, vyaw]
    </lark-td>
    <lark-td>
      3 {align="right"}
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
    </lark-td>
    <lark-td>
      合计
    </lark-td>
    <lark-td>
      48 {align="right"}
    </lark-td>
  </lark-tr>
</lark-table>

**（3）物理含义与单位（3 分）**

<lark-table rows="8" cols="3" header-row="true" column-widths="244,244,244">

  <lark-tr>
    <lark-td>
      分量
    </lark-td>
    <lark-td>
      含义
    </lark-td>
    <lark-td>
      单位（缩放前）
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      线速度
    </lark-td>
    <lark-td>
      机体坐标系下基座线速度，再乘 normalization.lin_vel=2
    </lark-td>
    <lark-td>
      m/s
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      角速度
    </lark-td>
    <lark-td>
      陀螺仪角速度，再乘 ang_vel=0.25
    </lark-td>
    <lark-td>
      rad/s
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      局部重力
    </lark-td>
    <lark-td>
      重力方向转到机体坐标，反映姿态倾斜
    </lark-td>
    <lark-td>
      无量纲方向向量
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      关节角偏差
    </lark-td>
    <lark-td>
      当前关节角减去默认站姿角，乘 dof_pos=1
    </lark-td>
    <lark-td>
      rad
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      关节速度
    </lark-td>
    <lark-td>
      12 关节角速度，乘 dof_vel=0.05
    </lark-td>
    <lark-td>
      rad/s
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      上一动作
    </lark-td>
    <lark-td>
      上一步策略输出的 12 维动作
    </lark-td>
    <lark-td>
      与动作同量纲
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      速度命令
    </lark-td>
    <lark-td>
      期望 [vx,vy,vyaw]，再乘 commands_scale
    </lark-td>
    <lark-td>
      m/s、rad/s
    </lark-td>
  </lark-tr>
</lark-table>

**（4）维度核对（2 分）**3+3+3+12+12+12+3 = 48，与 observation_space 的 48 维一致。
### 2. 动作（10 分）
**（1）截图位置（3 分）**walk_np.py → apply_action()、_compute_torques()（约 160-174 行）**（2）控制部件与物理量（3 分）**控制 12 个腿关节（FR/FL/RR/RL 的 hip、thigh、calf）。策略输出是相对默认角的位置偏移；经 PD 后写入的物理量是关节力矩（N·m），赋给 state.data.actuator_ctrls。**（3）完整路径与裁剪/缩放（4 分）**策略输出 a (12维)→ 训练 clip_actions：无（skrl/config.py 默认 False）→ apply_action：有缩放 action_scale=0.05，再 PD（kp=80, kd=1）得力矩→ XML：ctrlrange 为 -23.7 到 23.7，无 gear→ 执行器施加关节力矩
<image token="A2vIbPFlMopcgoxZ5xlcgSzcnrg" width="960" height="440" align="center"/>

### 3. 奖励（10 分）
**（1）截图位置（2 分）walk_np.py → update_reward()（约 249-264 行）（2）设每步奖励为 1、无折扣的累计奖励（各 2 分）**
<image token="I2Rzb5IkSo14rExBEelc7HPFn4e" width="1099" height="462" align="center"/>

- 持续 20 步：累计奖励 = 20
- 持续 80 步：累计奖励 = 80**（3）为何能鼓励不倒/稳定（4 分）**活得越久累计回报越大。GO1 躯干触地会 terminated 且该步奖励置 0，因此策略会被激励保持稳定、推迟失败。
### 4. 终止与截断（10 分）

<lark-table rows="4" cols="3" header-row="true" column-widths="244,244,244">

  <lark-tr>
    <lark-td>
      题目情形
    </lark-td>
    <lark-td>
      归类
    </lark-td>
    <lark-td>
      GO1 平地判据
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      1 杆角度越界
    </lark-td>
    <lark-td>
      失败终止
    </lark-td>
    <lark-td>
      等价：躯干 trunk 触地 → terminated=True
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      2 小车位置越界
    </lark-td>
    <lark-td>
      失败终止
    </lark-td>
    <lark-td>
      平地代码未实现
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      3 状态正常但超时
    </lark-td>
    <lark-td>
      时间截断
    </lark-td>
    <lark-td>
      steps>=2000（20.0/0.01）→ truncated=True
    </lark-td>
  </lark-tr>
</lark-table>

**截图：失败判定（2 分）**
<image token="XreZbYx45oue5Bxysv0cH9Rqnpc" width="960" height="330" align="center"/>

walk_np.py → update_terminated()**截图：超时截断与自动重置（2 分）**
<image token="SokTb7lsaoVs9kx7oO9c9fvSnWS" width="960" height="902" align="center"/>

np/env.py → _update_truncate()、_reset_done_envs()、step()**回合结束后谁重置（2 分）**step() 末尾调用 _reset_done_envs()，再调用子类 reset(data)。
