# 第3题 · terminated 与 truncated（四足 / GO1）

姓名：于鸿伟  
对应：第三周作业第 3 题（共 4 分）  
环境参考：MotrixLab `go1-flat-terrain-walk`（Unitree GO1）

---

## 可直接交的答案

### 1. terminated（含义 1 分 + 例子 1 分）

**含义：**  
表示回合因**任务失败 / 环境判定失败**而自然结束。失败后当前轨迹不再继续，需要 `reset` 开新回合。

**GO1 例子：**  
机器人**躯干（身体）与地面发生非预期碰撞**（摔倒、趴地），`terminated = True`。

---

### 2. truncated（含义 1 分 + 例子 1 分）

**含义：**  
表示回合因**时间到上限**被截断结束，不是因为失败，而是达到了最大步数 / 最大时长。

**GO1 例子：**  
机器人一直正常走、没有摔倒，但已经跑满配置的最大时长（本环境约 **20 秒**，`max_episode_seconds = 20.0`），`truncated = True`。

---

## 对照表（方便记忆）

| 标志 | 一句话 | GO1 典型触发 |
| ---- | ------ | ------------ |
| `terminated` | 失败结束 | 躯干撞地摔倒 |
| `truncated` | 超时截断 | 跑满 20 秒仍未失败 |

两者任一为真，都算本回合结束，都会触发重新 `reset`。

---

## 依据（作业自查，可不交）

- 终止条件说明：`docs/source/zh_CN/user_guide/demo/locomotion_unitree_go1.md` →「Episode 终止条件」
- 失败判定代码：`motrix_envs/.../locomotion/go1/walk_np.py` → `update_terminated`
- 超时截断代码：`motrix_envs/src/motrix_envs/np/env.py` → `_update_truncate`
- 超时配置：`motrix_envs/.../locomotion/go1/cfg.py` → `max_episode_seconds: float = 20.0`
