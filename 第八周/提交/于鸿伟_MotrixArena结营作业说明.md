# 第三期-于鸿伟-MotrixArena结营作业

## 一、作业目标与完成标准

本次结营作业围绕 **MotrixArena S1「越障导航」赛段第一阶段**。

- 不要求按比赛计分规则刷分
- 完成标准：机器人能够走到 **2026 平台**
- 环境：官方仓库 `MotrixArena-S1` 分支 + starter_kit 中的 `vbot_0218` 资产包

## 二、环境搭建

### 1. 克隆官方仓库

```bash
git clone --branch MotrixArena-S1 https://github.com/Motphys/MotrixLab.git
cd MotrixLab
```

说明：完整 `git lfs pull` 较慢；实操中使用 `GIT_LFS_SKIP_SMUDGE=1` 克隆后，直接使用 starter_kit 自带的 VBot 资产。

### 2. 下载并解压官方资产

```bash
curl -L -o starter_kit.zip https://dist.bj.bcebos.com/motphys-arena/starter_kit.zip
unzip starter_kit.zip
unzip starter_kit/.../navigation2.zip
# 其中已包含 vbot_0218/navigation_vbot.zip 与预训练 runs.zip
```

将 `navigation_vbot.zip` 解压得到的 `vbot/` 放入：

```text
motrix_envs/src/motrix_envs/locomotion/vbot
```

并在 `locomotion/__init__.py` 中注册：

```python
from . import vbot  # noqa: F401
```

### 3. 安装依赖

```bash
uv sync --all-packages --extra skrl-jax
```

### 4. 预训练权重

starter_kit 的 `vbot_0218/runs.zip` 提供：

```text
runs/vbot_navigation_section01/.../checkpoints/best_agent.pickle
```

对应环境名：`vbot_navigation_section01`（越障导航第一阶段相关）。

## 三、关键运行命令

```bash
# 依赖与环境
uv sync --all-packages --extra skrl-jax

# 回放（无环境 + 预训练策略）
uv run scripts/play.py \
  --env=vbot_navigation_section01 \
  --num-envs=1 \
  --policy=runs/vbot_navigation_section01/<RUN_DIR>/checkpoints/best_agent.pickle
```

如需训练：

```bash
uv run scripts/train.py --env=vbot_navigation_section01 --train-backend=torch
```

## 四、实践过程说明

1. **确认仓库分支**：使用官方指定的 `MotrixArena-S1`，避免误用 main / 其他 fork。
2. **资产获取**：按作业说明使用 starter_kit；其中 `vbot_0218` 已包含更新后的越障地形与 2026 平台相关资产。
3. **环境接入**：把 `vbot` 包挂到 `motrix_envs/.../locomotion/`，完成注册。
4. **依赖安装**：`uv sync --extra skrl-torch`，GPU 为 RTX 4090。
5. **策略回放**：加载官方提供的 `best_agent.pickle`，观察第一阶段路线是否到达 2026 平台。
6. **录屏取证**：保留 play 日志与 mp4，作为提交材料。

## 五、遇到的问题与解决方式

| 问题 | 原因 | 解决 |
| --- | --- | --- |
| `git clone` 卡很久 | Git LFS 拉取大量贴图/网格 | `GIT_LFS_SKIP_SMUDGE=1` 跳过 LFS，改用 starter_kit 资产 |
| 仓库内找不到 vbot | Arena 任务资产不在 git 内，而在 starter_kit | 下载 `starter_kit.zip` → `navigation2` → `vbot_0218` |
| 网页上看不到 `motphys-ground.png` 一类资源 | 资源走 Git LFS，网页常只显示指针文件 | 用 starter_kit / `git lfs pull` |
| `uv sync` SSH 超时 | Torch/CUDA 包体积大，交互 SSH 易断 | 后台 `nohup` 跑 sync，写日志等待 |
| 无头服务器无法弹窗 | 无显示器 | 使用 `Xvfb` 虚拟显示后再 play/录屏 |

## 六、最终结果说明

- 项目分支：`MotrixArena-S1`
- 任务环境：`vbot_navigation_section01`
- 策略：`best_agent.pickle`（starter_kit 官方预训练）
- 完成判定：回放录屏中机器人沿第一阶段路线前进并到达 **2026 平台**
- 证据：见同目录录屏 mp4、命令日志、本说明文档

## 七、参考资料

- 结营作业布置（本飞书文档）
- 资产更新说明：`vbot_0218` / starter_kit
- 赛事资料与补充教学（平地导航 / 越障导航）
- 官方文档：https://motrixlab.readthedocs.io/
