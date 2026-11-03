
**满分 100 分**

## 作业须知

- **代码版本**：以 MotrixLab v0.3.0 为准。课件代码与仓库不一致时，以仓库为准，并在答案中注明。
- **提交方式**：每周提交一份作业文档（PDF 或 DOCX），按题号作答；截图直接贴在文档中，视频随文档一起提交（MP4 或可访问的链接）。
- **截图和视频**：内容清晰，能看出对应的是哪道题、哪个任务。代码截图要能看到文件名。
- **来源写法**：写“文件路径 + 函数名”即可，例如 `cartpole_np.py update_state()`。
  
---


**本周目标**：

- 跑通 CartPole、Pendulum、Acrobot 三个 Demo，并比较它们的设计；
- 通过对照实验，观察单摆的能量奖励起什么作用；
- 独立分析 dm-reacher 任务。
  
**建议**：先读完第二题，再训练 Pendulum。按默认设置训练出的 Pendulum 结果可以直接作为第二题的 A 组。

---


## 说明

- 回放命令参考：`uv run scripts/play.py --env <任务名> --rllib skrl --policy <模型文件路径>`。
- “一个完整回合”指从回合开始到环境自动重置为止。
- 算力不足时可以提前停止训练，在文档中注明实际训练步数即可。
  
---


## 一、三个 Demo 的运行与比较（35 分）

**1. 训练并回放 CartPole、Pendulum、Acrobot**

每个任务提交下表 5 项，每项 1 分，三个任务共 15 分。

1. 训练命令和回放命令；
2. 训练结束日志截图；
3. 回放所加载的模型文件路径；
4. 训练曲线截图（TensorBoard 奖励曲线，注明任务名）；
5. 一个完整回合的回放视频。
  
CartPole 可以沿用第二周的训练结果。

**2. 八要素对比表（16 分）**

制作一张五列表格，列名为“要素｜CartPole｜Pendulum｜Acrobot｜比较与来源”，共 8 行。

- 要素与第三周相同，每行回答第三周对应的两个问题；
- “比较与来源”一列至少写出一处共同点或差异，并注明代码位置。
  
**评分**：每行内容 1 分，比较与来源 1 分，共 16 分。

**附件**：Pendulum 和 Acrobot 的观测、动作、奖励代码截图（CartPole 可引用第三周的截图）。

**提示**：填写“终止条件”一行时，注意比较三个任务超时时 `terminated` 和 `truncated` 的取值是否相同，并用代码说明原因。

**3. 观测编码与欠驱动（4 分）**

- 角度从 π 跨到 −π 时，直接输入角度和输入 sin/cos 有什么区别？给出跨越前后两种编码的具体数值（2 分）。
- Acrobot 有几个关节？动作是几维？结合 `acrobot.xml` 中 `<actuator>` 部分的截图，指出哪个关节直接受到驱动（2 分）。
  
---


## 二、单摆能量奖励对照实验（40 分）

### 实验设置


<lark-table rows="3" cols="2" column-widths="200,200">

  <lark-tr>
    <lark-td>
      组别
    </lark-td>
    <lark-td>
      奖励
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A 组
    </lark-td>
    <lark-td>
      默认奖励
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B 组
    </lark-td>
    <lark-td>
      只把能量奖励项对总奖励的贡献改为 0
    </lark-td>
  </lark-tr>
</lark-table>


两组都从头训练，其余奖励项、环境设置和训练设置完全相同。

**1. 能量项的代码（8 分）**

- 截图展示能量项的计算代码，以及它加入总奖励的那一行（4 分）。
- 只把能量项的贡献改为 0，提交修改后的代码截图，并标出修改的行（4 分）。
  
**2. 对照参数表（8 分）**

制作一张四列表格，列名为“参数｜A 组｜B 组｜来源”，填写以下四项：

1. MotrixLab 版本、训练后端；
2. 训练种子、并行环境数；
3. 训练步数（注明单位）、学习率；
4. 网络结构、其他奖励项的系数、回合时长。
  
**评分**：每项记录完整 1 分，两组一致 1 分。

**3. 训练证据（6 分）**

A、B 两组分别提交以下 3 项，每项 1 分：

- 训练命令；
- 训练结束日志截图；
- 回放所用的模型文件路径。
  
**4. 回放记录（10 分）**

**回放方式**：

- 每组回放 3 个完整回合，两组视角保持一致；
- 如果支持设置种子（`--seed`），两组都用 0、1、2。
  
**判据**：摆杆与竖直向上方向的夹角不超过 15°，视为处于直立范围。

**记录表**：填写下表，共 6 行，每行 1 分。判断填“是”“否”或“无法判断”。


<lark-table rows="7" cols="5" column-widths="200,200,200,200,200">

  <lark-tr>
    <lark-td>
      组别 / 回合
    </lark-td>
    <lark-td>
      初始姿态
    </lark-td>
    <lark-td>
      是否曾到达直立范围
    </lark-td>
    <lark-td>
      末帧是否在直立范围内
    </lark-td>
    <lark-td>
      证据时间点
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 0
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 1
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 2
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 0
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 1
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 2
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
</lark-table>


**提交**（每项 1 分，共 4 分）：

- A 组三个回合的视频；
- B 组三个回合的视频；
- A 组第一个回合的末帧截图，标出摆杆偏离竖直方向的大致角度；
- B 组第一个回合的末帧截图，同样标出角度。
  
**5. 分析（8 分）**

1. 两组在到达直立范围和末帧姿态上有什么差异？（3 分）
2. 能量奖励可能怎样影响了这些现象？（3 分）
3. 这次实验的结论有哪些局限？至少写两点。（2 分）
  
**评分说明**：

- 本题按实验过程和证据评分，不要求 B 组表现更好；
- 两组的奖励定义不同，不能用总奖励的大小来判断哪组更好；
- 末帧姿态不能证明整个回合都保持稳定。
  
---


## 三、双关节机械臂 dm-reacher 分析（25 分）

本题不要求训练。

**准备**：用 `uv run scripts/view.py --env dm-reacher` 打开场景，截图并标出两段连杆、两个关节和目标点。

**1. 八要素表（选做，单独评价 16 分）**

**选做说明**：本小题单独评价，不计入本作业 100 分总分。

按第三周第二题的格式，填写 dm-reacher 的“要素｜答案｜来源”表。

**评分**：每行内容 1 分，来源 1 分。

**注意**：

- **观测**：以代码实际拼接出的维度为准，写出每个分量的含义。如果与官方文档不一致，请结合 `reacher.xml` 中的关节列表解释原因。
- **域随机化**：分别写出目标点在 x、y 两个方向的采样范围，以及实际的变化范围。
  
**2. 关键代码（15 分）**

分别截图展示以下三段代码，每段代码 2 分；每段配一句解释，每句 3 分。


<lark-table rows="4" cols="2" column-widths="200,200">

  <lark-tr>
    <lark-td>
      代码
    </lark-td>
    <lark-td>
      需要解释的内容
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      观测构造
    </lark-td>
    <lark-td>
      目标信息是怎样进入观测的
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      动作应用
    </lark-td>
    <lark-td>
      每个动作分量控制哪个关节
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      奖励计算
    </lark-td>
    <lark-td>
      末端与目标的距离怎样影响奖励；写出奖励为 1 的距离区间，以及奖励降为 0 的距离
    </lark-td>
  </lark-tr>
</lark-table>


**3. 思考题（10 分）**

目标点每个回合都会变化。如果观测中不包含任何目标位置信息（包括末端到目标的相对位置），策略还能可靠地到达目标吗？

请写出以下三点（判断 2 分，原因 4 分，代码依据 4 分）：

- 判断；
- 原因；
- 代码依据：逐一检查观测的各个分量，说明需要去掉哪些分量，观测才算完全不含目标信息。


---

# 【作答区】于鸿伟 · 第四周（文字已填；截图/视频请自行粘贴）
> 代码版本：**MotrixLab v0.3.0**。命令以仓库 `scripts/train.py` / `play.py` / `view.py` 为准。标注「📷」处由实操同学补截图/视频。
---

## 一.1 训练并回放（命令模板；路径/截图你补）
### CartPole
```plaintext
训练：python scripts/train.py --env=cartpole --rllib=skrl
回放：python scripts/play.py --env=cartpole --rllib=skrl --policy=runs/cartpole/skrl/<时间戳>/checkpoints/best_agent.pt

```

- 📷 训练结束日志
- 模型路径：（填写）
- 📷 TB 奖励曲线（注明 cartpole）
- 🎬 完整一回合回放视频
- （可沿用第二周结果，注明即可）
### Pendulum
```plaintext
训练：python scripts/train.py --env=pendulum --rllib=skrl --seed=42
回放：python scripts/play.py --env=pendulum --rllib=skrl --policy=runs/pendulum/skrl/<时间戳>/checkpoints/best_agent.pt

```

- 📷 日志 / TB / 🎬 视频（本结果可同时作第二题 A 组）
### Acrobot
```plaintext
训练：python scripts/train.py --env=acrobot --rllib=skrl
回放：python scripts/play.py --env=acrobot --rllib=skrl --policy=runs/acrobot/skrl/<时间戳>/checkpoints/best_agent.pt

```

- 📷 日志 / TB / 🎬 视频
---

## 一.2 八要素对比表

<lark-table rows="9" cols="5" header-row="true" column-widths="146,146,146,146,146">

  <lark-tr>
    <lark-td>
      要素
    </lark-td>
    <lark-td>
      CartPole
    </lark-td>
    <lark-td>
      Pendulum
    </lark-td>
    <lark-td>
      Acrobot
    </lark-td>
    <lark-td>
      比较与来源
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **智能体**
    </lark-td>
    <lark-td>
      ① 控制小车+倒立杆；输出 1 维力。② 观测 4 维，动作 1 维。
    </lark-td>
    <lark-td>
      ① 控制单摆扭矩；动作先 clip 到 [-1,1] 再缩放。② 观测 3 维，动作 1 维。
    </lark-td>
    <lark-td>
      ① 控制双连杆；输出 1 维肘扭矩。② 观测 6 维，动作 1 维。
    </lark-td>
    <lark-td>
      **同**低维连续控制；**异** Acrobot 欠驱动（2 关节/1 动作）。来源：各自 `*_np.py` 的 `action_space` / `observation_space`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **环境**
    </lark-td>
    <lark-td>
      `cartpole.xml`
    </lark-td>
    <lark-td>
      `pendulum.xml`
    </lark-td>
    <lark-td>
      `acrobot.xml`（含 tip/target site）
    </lark-td>
    <lark-td>
      均由 `cfg.model_file` 指向 xml。来源：各自 `cfg.py`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **观测**
    </lark-td>
    <lark-td>
      `concat(dof_pos,dof_vel)`，4 维
    </lark-td>
    <lark-td>
      `[cosθ,sinθ,ω]`，3 维
    </lark-td>
    <lark-td>
      上/下臂水平与垂直分量（cos/sin）+ 两关节角速度，6 维
    </lark-td>
    <lark-td>
      **异**：CartPole 用原始角；另两者用三角函数。来源：`update_state` / `_get_obs`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **动作**
    </lark-td>
    <lark-td>
      `Box(-3,3,(1,))`，直接写 `actuator_ctrls`
    </lark-td>
    <lark-td>
      `Box(-1,1,(1,))`；XML motor `ctrlrange="-1 1"` gear=5
    </lark-td>
    <lark-td>
      `Box(-1,1,(1,))`；XML **仅** elbow 有 motor
    </lark-td>
    <lark-td>
      **异**：Acrobot 只驱动 elbow。来源：`apply_action`；`acrobot.xml` `<actuator>`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **奖励**
    </lark-td>
    <lark-td>
      每步恒为 1（存活）
    </lark-td>
    <lark-td>
      `3·upright + energy_reward − 0.2ω² − 0.001 ctrl² − 0.001 Δctrl²`；`energy=0.5ω²+(1−cosθ)` 再 `tolerance`
    </lark-td>
    <lark-td>
      tip→target 距离 `tolerance` + 在目标内奖励 + 距离塑形 − 速度惩罚
    </lark-td>
    <lark-td>
      **异**：CartPole 稀疏存活；Pendulum 有能量塑形；Acrobot 追目标。来源：各自 `update_state`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **初始状态**
    </lark-td>
    <lark-td>
      默认姿态 + `reset_noise_scale=0.01`
    </lark-td>
    <lark-td>
      θ∼U(−π,π)；角速度默认 0
    </lark-td>
    <lark-td>
      肩/肘 ∼U(−π,π)，速度小噪声 0.1
    </lark-td>
    <lark-td>
      **同**有随机重置。来源：`reset` + `cfg.py`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **终止条件**
    </lark-td>
    <lark-td>
      terminated：`
    </lark-td>
    <lark-td>
      角
    </lark-td>
    <lark-td>
      >0.2` 或 x∉[-0.8,0.8] 或 NaN；truncated：≥1000 步（10s/0.01）。超时**只** truncated
    </lark-td>
    <lark-td>
      terminated：NaN；truncated：≥400 步（10s/0.025）。超时只 truncated
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **域随机化**
    </lark-td>
    <lark-td>
      仅 reset 噪声
    </lark-td>
    <lark-td>
      仅初始角（可选角速度）随机
    </lark-td>
    <lark-td>
      仅初始关节随机
    </lark-td>
    <lark-td>
      **同**无在线质量/摩擦 DR。来源：`reset`
    </lark-td>
  </lark-tr>
</lark-table>

📷 附件：Pendulum / Acrobot 观测、动作、奖励代码截图（能看见文件名）。
---

## 一.3 观测编码与欠驱动
### （1）π 跨到 −π
取跨越前 `θ=π−0.01≈3.1316`，跨越后 `θ=−π+0.01≈−3.1316`：

<lark-table rows="4" cols="4" header-row="true" column-widths="183,183,183,183">

  <lark-tr>
    <lark-td>
      编码
    </lark-td>
    <lark-td>
      跨越前
    </lark-td>
    <lark-td>
      跨越后
    </lark-td>
    <lark-td>
      说明
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      直接 θ
    </lark-td>
    <lark-td>
      3.1316
    </lark-td>
    <lark-td>
      −3.1316
    </lark-td>
    <lark-td>
      差值约 **6.26**，假跳变
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      cosθ
    </lark-td>
    <lark-td>
      ≈−1.000
    </lark-td>
    <lark-td>
      ≈−1.000
    </lark-td>
    <lark-td>
      连续
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      sinθ
    </lark-td>
    <lark-td>
      ≈0.010
    </lark-td>
    <lark-td>
      ≈−0.010
    </lark-td>
    <lark-td>
      连续变号，无 2π 跳变
    </lark-td>
  </lark-tr>
</lark-table>

结论：直接角度在 ±π 边界不连续；sin/cos 在圆周上连续，适合网络输入。
### （2）Acrobot
- 关节：**2**（shoulder、elbow）
- 动作维：**1**
- 直接驱动：**elbow**（`<actuator>` 仅 `<motor ... joint="elbow"/>`）
📷 请贴 `acrobot.xml` 的 `<actuator>` 截图。
---

## 二.1 能量项代码说明
文件：`motrix_envs/.../pendulum/pendulum_np.py` → `update_state`
```python
energy = 0.5 * ang_vel**2 + (1.0 - np.cos(angle_wrapped))
energy_reward = reward_utils.tolerance(energy, bounds=(2.0, 2.0), margin=2.0, value_at_margin=0.1, sigmoid="gaussian")
reward = (3.0 * upright + energy_reward - vel_penalty - 0.001 * ctrl**2 - 0.001 * ctrl_delta**2)

```

**B 组修改（只改贡献为 0）：**
```python
reward = (3.0 * upright + 0.0 * energy_reward - vel_penalty - 0.001 * ctrl**2 - 0.001 * ctrl_delta**2)

```

📷 A 组能量项代码截图；📷 B 组修改行截图（训完改回）。
---

## 二.2 对照参数表

<lark-table rows="5" cols="4" header-row="true" column-widths="183,183,183,183">

  <lark-tr>
    <lark-td>
      参数
    </lark-td>
    <lark-td>
      A 组
    </lark-td>
    <lark-td>
      B 组
    </lark-td>
    <lark-td>
      来源
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      版本与后端
    </lark-td>
    <lark-td>
      MotrixLab **v0.3.0**；`--rllib=skrl`
    </lark-td>
    <lark-td>
      同 A
    </lark-td>
    <lark-td>
      仓库；`scripts/train.py`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      种子与并行数
    </lark-td>
    <lark-td>
      `--seed=42`；默认 `num_envs=2048`（若未改）
    </lark-td>
    <lark-td>
      同 A
    </lark-td>
    <lark-td>
      `train.py`；`skrl/config.py`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      训练步数与学习率
    </lark-td>
    <lark-td>
      `trainer.timesteps=5000`；`learning_rate=3e-4`
    </lark-td>
    <lark-td>
      同 A
    </lark-td>
    <lark-td>
      `motrix_rl/.../tasks/pendulum.py`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      网络；其它奖励系数；回合时长
    </lark-td>
    <lark-td>
      hiddens `[64,64]`；upright×3，vel=`0.2ω²`，ctrl/Δctrl 系数 `0.001`；`max_episode_seconds=10`，`ctrl_dt=0.025` → **400 步**
    </lark-td>
    <lark-td>
      同 A（仅 energy 系数改为 0）
    </lark-td>
    <lark-td>
      `pendulum.py`；`pendulum_np.py`；`pendulum/cfg.py`
    </lark-td>
  </lark-tr>
</lark-table>

（若实际 seed/num-envs/提前停训不同，以你日志为准改表。）
---

## 二.3 训练证据（你填）
**A 组**
```plaintext
python scripts/train.py --env=pendulum --rllib=skrl --seed=42

```

- 📷 结束日志
- 模型路径：`runs/pendulum/skrl/<A时间戳>/checkpoints/best_agent.pt`
**B 组**（改代码后）
```plaintext
python scripts/train.py --env=pendulum --rllib=skrl --seed=42

```

- 📷 结束日志
- 模型路径：`runs/pendulum/skrl/<B时间戳>/checkpoints/best_agent.pt`
---

## 二.4 回放记录（你填判断）
回放：`--seed=0/1/2`；直立判据：与竖直向上夹角 ≤15°。

<lark-table rows="7" cols="5" header-row="true" column-widths="146,146,146,146,146">

  <lark-tr>
    <lark-td>
      组别/回合
    </lark-td>
    <lark-td>
      初始姿态
    </lark-td>
    <lark-td>
      是否曾到达直立范围
    </lark-td>
    <lark-td>
      末帧是否在直立范围内
    </lark-td>
    <lark-td>
      证据时间点
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 0
    </lark-td>
    <lark-td>
      （填）
    </lark-td>
    <lark-td>
      是/否/无法判断
    </lark-td>
    <lark-td>
      是/否/无法判断
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 1
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 2
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 0
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 1
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 2
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
    <lark-td>
    </lark-td>
  </lark-tr>
</lark-table>

🎬 A×3 + B×3 视频；📷 A/B 第一回合末帧并标角。
---

## 二.5 分析
**1）差异（跑完按表微调）：**A 组（有能量奖励）通常更多回合曾进入直立范围，末帧也更常停在直立附近；B 组更常见整回合到不了直立，或短暂甩过但末帧仍大幅偏离。若表中两组接近，则注明「本种子/步数下次数接近，但 A 末帧更稳 / 差异不明显」。
**2）能量奖励如何影响：**upright 主要在接近倒立时才大，从底部探索信号弱。`energy=0.5ω²+(1−cosθ)` 经 tolerance 塑形，在「泵能量、抬高」阶段也给分，引导先积机械能再立住。去掉后更依赖偶然摆高才拿到 upright，更难稳定倒立。比较应看行为（是否直立），不能比总 reward 大小（奖励定义已变）。
**3）局限（至少两点）：**① 种子与训练步数有限，结论外推受限。② 末帧直立不能证明整回合都稳定（作业已提示）。③（可选）并行环境数、jax/torch 后端、play 渲染设置都会影响观感。
---

## 三.0 准备（你做）
```plaintext
python scripts/view.py --env=dm-reacher

```

📷 场景截图，标出两段连杆、两个关节、目标点。
---

## 三.1 八要素表（选做）

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
      **智能体**
    </lark-td>
    <lark-td>
      平面双关节臂；动作 2 维扭矩；观测维=`num_dof_pos+2+num_dof_vel`
    </lark-td>
    <lark-td>
      `reacher_np.py` `_init_*_space`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **环境**
    </lark-td>
    <lark-td>
      双连杆+目标球；`reacher.xml`
    </lark-td>
    <lark-td>
      `cfg.py`；xml
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **观测**
    </lark-td>
    <lark-td>
      `concat(qpos, to_target_xy, qvel)`；`to_target=target_xy−finger_xy`。XML 含 shoulder/wrist/target_x/target_y；若均入 dof，常为 **10** 维；文档写 6 维未计目标 slide。以 `observation_space.shape` 为准
    </lark-td>
    <lark-td>
      `_get_obs`；`reacher.xml`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **动作**
    </lark-td>
    <lark-td>
      2 维；`actions[0]→shoulder`，`actions[1]→wrist`
    </lark-td>
    <lark-td>
      `apply_action`；xml `<actuator>`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **奖励**
    </lark-td>
    <lark-td>
      `tolerance(dist, bounds=(0,0.02), margin=0.02, linear, value_at_margin=0)`
    </lark-td>
    <lark-td>
      `update_state`；`target_size=0.02`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **初始状态**
    </lark-td>
    <lark-td>
      臂角 ∼U(−π,π)；目标在 reset 写入
    </lark-td>
    <lark-td>
      `reset`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **终止**
    </lark-td>
    <lark-td>
      terminated：NaN；truncated：6s/0.025=**240** 步
    </lark-td>
    <lark-td>
      `cfg.py`；`np/env.py`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      **域随机化**
    </lark-td>
    <lark-td>
      **x**：U(−0.15,0.15)，变化宽度 0.30；**y**：U(0.15,0.15)，**恒为 0.15**，宽度 0。每 reset 采样。文档「圆域」与代码不符，以代码为准
    </lark-td>
    <lark-td>
      `reset`
    </lark-td>
  </lark-tr>
</lark-table>

---

## 三.2 关键代码解释
**（1）观测 — 目标如何进入**`_get_obs`：`to_target = target_xy − finger_xy`，与 `qpos`、`qvel` 拼接。目标主要通过这 **2 维相对向量**进入观测；若 qpos 含 target 滑块，绝对位置也会间接出现。
**（2）动作 — 分量对应**`actuator_ctrls = actions`；结合 xml：分量 0→**shoulder**，分量 1→**wrist**。
**（3）奖励 — 距离区间**`dist∈[0, 0.02]` → 奖励 **=1**；`dist≥0.04` → 奖励 **=0**；（0.02,0.04) 线性衰减。
📷 三段代码截图（文件名可见）。
---

## 三.3 思考题
- **判断：** 不能可靠到达每个回合都在变的目标。
- **原因：** 目标在 reset 时重采样（至少 x 变）。策略是观测→动作的映射；观测若与目标无关，无法对「当前目标」条件化，只能学开环/平均行为。
- **代码依据：** 当前观测=`qpos` + `to_target(2)` + `qvel`。① 必须去掉 **to_target 两维**；② 若 `qpos` 含 **target_x/target_y**（xml 有这两个 joint），也须去掉。仅保留手臂关节角/角速度后，才算完全不含目标信息。
---

# 【实操证据】云端已跑通（于鸿伟）
> 机器：云 GPU（RTX 4090）· MotrixLab **v0.3.0** · `uv run` · `skrl` + `torch` · seed=**42**本地完整包：`D:\motrix\第四周\截图\`（含 mp4 / 曲线 / 回放帧）
## 一.1 训练与回放（已完成）
### CartPole
```plaintext
uv run scripts/train.py --env=cartpole --rllib=skrl --seed=42 --train-backend=torch
uv run scripts/play.py --env=cartpole --rllib=skrl --policy=runs/cartpole/skrl/26-10-25_12-21-55-090874_PPO/checkpoints/best_agent.pt

```

模型：`runs/cartpole/skrl/26-10-25_12-21-55-090874_PPO/checkpoints/best_agent.pt`
### Pendulum（兼作第二题 A 组）
```plaintext
uv run scripts/train.py --env=pendulum --rllib=skrl --seed=42 --train-backend=torch

```

模型：`runs/pendulum/skrl/26-10-25_12-22-44-980900_PPO/checkpoints/best_agent.pt`
### Acrobot
```plaintext
uv run scripts/train.py --env=acrobot --rllib=skrl --seed=42 --train-backend=torch

```

模型：`runs/acrobot/skrl/26-10-25_12-23-29-008041_PPO/checkpoints/best_agent.pt`
（曲线图、回放视频见下方插入的媒体 / 本地 `截图` 文件夹。）
## 二.3 B 组模型
B 组修改：`3.0 * upright + 0.0 * energy_reward - ...`模型：`runs/pendulum/skrl/26-10-25_12-27-43-111800_PPO/checkpoints/best_agent.pt`
## 二.4 回放记录（中帧截图辅助；请结合视频最终确认直立 ≤15°）

<lark-table rows="7" cols="5" header-row="true" column-widths="146,146,146,146,146">

  <lark-tr>
    <lark-td>
      组别/回合
    </lark-td>
    <lark-td>
      初始姿态
    </lark-td>
    <lark-td>
      是否曾到达直立范围
    </lark-td>
    <lark-td>
      末帧是否在直立范围内
    </lark-td>
    <lark-td>
      证据
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 0
    </lark-td>
    <lark-td>
      随机底部附近
    </lark-td>
    <lark-td>
      待视频确认
    </lark-td>
    <lark-td>
      中帧接近直立（见截图）
    </lark-td>
    <lark-td>
      `pendulum_A_seed0.mp4`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 1
    </lark-td>
    <lark-td>
      随机
    </lark-td>
    <lark-td>
      待视频确认
    </lark-td>
    <lark-td>
      中帧接近直立
    </lark-td>
    <lark-td>
      `pendulum_A_seed1.mp4`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      A / 2
    </lark-td>
    <lark-td>
      随机
    </lark-td>
    <lark-td>
      待视频确认
    </lark-td>
    <lark-td>
      中帧接近直立
    </lark-td>
    <lark-td>
      `pendulum_A_seed2.mp4`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 0
    </lark-td>
    <lark-td>
      随机
    </lark-td>
    <lark-td>
      待视频确认
    </lark-td>
    <lark-td>
      中帧接近直立
    </lark-td>
    <lark-td>
      `pendulum_B_seed0.mp4`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 1
    </lark-td>
    <lark-td>
      随机
    </lark-td>
    <lark-td>
      待视频确认
    </lark-td>
    <lark-td>
      中帧接近直立
    </lark-td>
    <lark-td>
      `pendulum_B_seed1.mp4`
    </lark-td>
  </lark-tr>
  <lark-tr>
    <lark-td>
      B / 2
    </lark-td>
    <lark-td>
      随机
    </lark-td>
    <lark-td>
      待视频确认
    </lark-td>
    <lark-td>
      中帧接近直立
    </lark-td>
    <lark-td>
      `pendulum_B_seed2.mp4`
    </lark-td>
  </lark-tr>
</lark-table>

> 说明：云端无显示器，用 Xvfb 软件渲染录屏；请打开本地 mp4 按作业判据填「是/否」。不要用总 reward 比 A/B。
## 媒体说明
已插入：CartPole / PendulumA / PendulumB / Acrobot 奖励曲线；CartPole / PendulumA0 / PendulumB0 / Acrobot / dm-reacher 场景截图。视频请从本地 `D:\motrix\第四周\截图\videos\` 上传到作业文档或随 PDF 提交。
<image token="HAUKbs1sjoyVc0xNzLxcIHJDnRf" width="1120" height="630" align="center"/>

<image token="Yo7tbcvK3opMpixTi7wcTzE1nh4" width="1120" height="630" align="center"/>

<image token="QBXlbe1SHoMxZIx5yiWcDyeSnjd" width="1120" height="630" align="center"/>

<image token="PKj4byt86o0zEaxw7IjcYK0In1d" width="1120" height="630" align="center"/>

<image token="LXDqbvvLIoiUzWxuCEncngprnWe" width="1280" height="720" align="center"/>

<image token="FWAqbocUiovN9Kxf8KpciYiFnrh" width="1280" height="720" align="center"/>

<image token="TzKzb4KkNohREExPADIcuFifnPd" width="1280" height="720" align="center"/>

<image token="SllPbtkcPoUv6qxzvUPcZDjtnFU" width="1280" height="720" align="center"/>

<image token="Mjtgb9RdioKGbOxWnHOcXgobnlf" width="1280" height="720" align="center"/>

<view type="1">

  <file token="I8P2bwDZLow51FxQC5hcOdH3nsb" name="cartpole_seed0.mp4"/>

</view>

<view type="1">

  <file token="IfiIbl6BYooxNjxQ2zsctwmdnsc" name="pendulum_A_seed0.mp4"/>

</view>

<view type="1">

  <file token="PZRabPh7ao45lox8zgecA0aRnAc" name="pendulum_A_seed1.mp4"/>

</view>

<view type="1">

  <file token="JcA0bh5mBoyRupxRlLIcWn1QnUp" name="pendulum_A_seed2.mp4"/>

</view>

<view type="1">

  <file token="Z3P2bX8jroUc7xxSEhxcWUT6nfe" name="pendulum_B_seed0.mp4"/>

</view>

<view type="1">

  <file token="Vrd4b5PQ7o2tt9xRo3ScS8ZCnyg" name="pendulum_B_seed1.mp4"/>

</view>

<view type="1">

  <file token="DFoYbU5Q2o0Mx0x5K2PckUL3nWe" name="acrobot_seed0.mp4"/>

</view>

<view type="1">

  <file token="FK2LbnPU6ooGt3xHAGyce2YLnif" name="pendulum_B_seed2.mp4"/>

</view>

