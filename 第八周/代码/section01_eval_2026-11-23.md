# VBot Section01 云端回放记录（2026-11-23）

> 2026-11-24 更新：已在云端完成到达 2026 平台的验收，11 个随机种子全部通过。修复与命令见 [section01_2026_success.md](section01_2026_success.md)。下文保留为修复前的诊断记录。

## 目标与结果

目标是让 `vbot_navigation_section01` 使用 LM 导航阶段的 `best_agent.pt` 走到 2026 平台。当前没有通过验收，不能把已有演示视频或画面里可见的 GO 斜面当作本次运行已到达。

## 本次实测

- 云端项目：`/root/autodl-tmp/MotrixLab`
- 权重：`runs/vbot_navigation_section01/known_success_PPO/checkpoints/best_agent.pt`
- 策略输入：68 维
- section01 控制参数：`action_scale = 0.45`（与 LM README 记录一致）
- 坐标读取：从 `env_np.state.data` 调用 `_body.get_pose(...)`；此前从错误的 `_data` 取值会得到 NaN。
- 固定种子 42，2000 步：`max_y = -0.847`，结束时 `y = -0.906`，无 reset；最后观测的 projected gravity z 为 `-0.855`，姿态倾斜明显。距离验收 `y >= 7.8` 很远。
- `action_scale = 0.25` 的对照试跑 600 步：出现 4 次 reset，说明降低比例会更早摔倒；测试后已恢复 `0.45`。
- 地形碰撞开关试验导致出生区反复 reset，测试后已恢复原 XML，没有保留这项修改。

## 截图定位

用户此前的几张倒地截图中，机器狗仍在 START 圆盘旁、黄色粗糙地形入口。GO 标识和斜面出现在前景深处；透视让目标显得接近，但狗尚未到达 GO 斜面。LM 仓库里的 `vbot_section01_success.mp4` 是单独保存的演示素材，不是本次云端验收录像。

## 目前判断

场景的黄色 hfield 从约 `y = -1.5` 延伸到 `y = 1.5`。固定种子实测只能深入黄色区域约 0.6 m 后停在 `y≈-0.9`；当前主要阻塞是策略在粗糙地形上的持续前进/姿态稳定，不是“到 2026 前只差一小段”。策略没有经过跳跃控制训练，直接加关节脉冲或传送位置还没有验证，不能作为已解决方案。

接下来先复核 checkpoint 对应的训练环境与 68 维观测各字段，再做完整 8000 步坐标验收。验收仍以 `max_y >= 7.8` 且翻滚率低为准。
