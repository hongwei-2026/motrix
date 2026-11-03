# 于鸿伟 · MotrixLab 第四周实操证据包

- **课程周次**：第四周（经典控制对比 + Pendulum 能量奖励消融 + dm-reacher）
- **代码版本**：MotrixLab **v0.3.0**
- **训练后端**：`skrl` + `torch`，默认 `seed=42`，`num_envs=2048`
- **飞书作业**：https://ccnz793r59f8.feishu.cn/wiki/CTb6wEgzxipc8LkQqIZcOzgPnie

## 目录对照提交渠道

| 文件夹 | 对应提交项 | 格式 |
|--------|------------|------|
| `01_文档材料` | Word/文档材料 | `.md` / `.html`（可另存 PDF/DOCX） |
| `02_曲线图` | 运行截图/曲线图 | `.png`（均 < 10MB） |
| `03_运行截图` | 运行截图 | `.png` |
| `04_仿真录屏` | 仿真录屏视频 | `.mp4` |
| `05_日志与代码摘录` | 工程源码/日志 | `.log` / `.txt` / 代码备份 |
| `06_模型权重_best` | 工程产物（best checkpoint） | `.pt` |

## 关键命令与模型路径（可粘贴到文本框）

```text
# 训练
uv run scripts/train.py --env=cartpole --rllib=skrl --seed=42 --train-backend=torch
uv run scripts/train.py --env=pendulum --rllib=skrl --seed=42 --train-backend=torch
uv run scripts/train.py --env=acrobot --rllib=skrl --seed=42 --train-backend=torch
# Pendulum B：pendulum_np.py 中 + energy_reward 改为 + 0.0 * energy_reward 后重训

# 回放示例
uv run scripts/play.py --env=pendulum --rllib=skrl --policy=runs/pendulum/skrl/26-10-25_12-22-44-980900_PPO/checkpoints/best_agent.pt --seed=0
uv run scripts/view.py --env=dm-reacher
```

### best_agent 路径

```text
runs/cartpole/skrl/26-10-25_12-21-55-090874_PPO/checkpoints/best_agent.pt
runs/pendulum/skrl/26-10-25_12-22-44-980900_PPO/checkpoints/best_agent.pt   # A 组
runs/pendulum/skrl/26-10-25_12-27-43-111800_PPO/checkpoints/best_agent.pt   # B 组
runs/acrobot/skrl/26-10-25_12-23-29-008041_PPO/checkpoints/best_agent.pt
```

### 关键超参（Pendulum A/B 一致，仅能量项系数不同）

```text
MotrixLab=v0.3.0
rllib=skrl
train_backend=torch
seed=42
num_envs=2048
trainer.timesteps=5000
learning_rate=3e-4
policy/value hiddens=[64,64]
max_episode_seconds=10
ctrl_dt=0.025
max_episode_steps=400
A: energy_reward 系数 = 1
B: energy_reward 系数 = 0
```

### Reacher 关键数值（代码）

```text
target_size=0.02
reward=1 当 dist in [0, 0.02]
reward=0 当 dist >= 0.04
target_x ~ Uniform(-0.15, 0.15)
target_y = 0.15  (Uniform(0.15,0.15)，实际固定)
max_episode_steps = 6.0/0.025 = 240
```

## 视频清单（二.4 回放）

- `cartpole_seed0.mp4` / `acrobot_seed0.mp4`
- Pendulum A：`pendulum_A_seed{0,1,2}.mp4`
- Pendulum B：`pendulum_B_seed{0,1,2}.mp4`

## 在线链接

- 飞书作业文档：https://ccnz793r59f8.feishu.cn/wiki/CTb6wEgzxipc8LkQqIZcOzgPnie
- 上游仓库：https://github.com/Motphys/MotrixLab（tag v0.3.0）
