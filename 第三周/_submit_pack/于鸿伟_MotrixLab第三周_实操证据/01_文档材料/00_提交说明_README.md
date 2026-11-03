# 于鸿伟 · MotrixLab 第三周实操证据包

- **课程周次**：第三周（环境八要素 · Unitree GO1 平地行走）
- **环境**：`go1-flat-terrain-walk`
- **代码版本**：MotrixLab **v0.3.0**
- **说明**：本周以读代码 / 填表 / 流程图为主，**不要求训练录屏**；证据以文档 + 代码截图为主。
- **飞书作业**：https://ccnz793r59f8.feishu.cn/wiki/NO7PwbbhZiz2ZRkuXHZclBhwnGf

## 目录对照提交渠道

| 文件夹 | 对应提交项 | 格式 |
|--------|------------|------|
| `01_文档材料` | Word/文档材料 | `.md` / `.html`（可另存 PDF/DOCX） |
| `02_代码与运行截图` | 运行截图 | `.png`（均 < 10MB） |
| `03_小红书素材` | 可选补充图文 | `.md` / `.png` |

> 本周无仿真训练 mp4；若平台必传视频项，可用飞书文档内已贴图说明「本周不要求训练」，或上传小红书配图作过程记录。

## 关键数值（可粘贴到文本框）

```text
env = go1-flat-terrain-walk
MotrixLab = v0.3.0
obs_dim = 48 = linvel3 + gyro3 + gravity3 + joint_pos12 + joint_vel12 + last_action12 + cmd3
action_dim = 12
action_scale = 0.05
PD: kp=80, kd=1
motor ctrlrange = [-23.7, 23.7]
terminated: trunk contact floor
truncated: max_episode_seconds=20.0 / ctrl_dt=0.01 = 2000 steps
commands resample on reset: vx[-1,2], vy[-1,1], vyaw[-1,1]
文档有、平地未实现: 关节重置噪声±0.125; 观测 NoiseConfig; 超速终止>1e8
```

## 文档索引

1. `01_一回合交互流程图.md` — 第2题流程图 + 四条关系
2. `02_八要素表_GO1.md` — 第2题八要素表
3. `03_terminated与truncated.md` — 第3题
4. `04_代码阅读_GO1.md` — 第3部分代码阅读

## 截图索引

1. 观测 `_get_obs`
2. 动作 `apply_action` / PD
3. 奖励 `update_reward`
4. 失败终止 `update_terminated`
5. 截断与重置 `np/env.py`

## 在线链接

- 飞书：https://ccnz793r59f8.feishu.cn/wiki/NO7PwbbhZiz2ZRkuXHZclBhwnGf
- 上游：https://github.com/Motphys/MotrixLab（tag v0.3.0）
