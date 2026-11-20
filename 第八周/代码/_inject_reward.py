#!/usr/bin/env python3
"""Replace stub reward/termination in vbot_section01 with navigation reward."""
from pathlib import Path

p = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py")
src = p.read_text(encoding="utf-8")
bak = Path("/root/autodl-tmp/evidence_w8/vbot_section01_np.py.before_reward")
if not bak.exists():
    bak.write_text(src, encoding="utf-8")

NEW_TERM = '''    def _compute_terminated(self, state: NpEnvState) -> NpEnvState:
        """Terminate on fall / flip / NaN."""
        data = state.data
        pose = self._body.get_pose(data)
        root_quat = pose[:, 3:7]
        root_z = pose[:, 2]
        proj_g = self._compute_projected_gravity(root_quat)
        gxy = np.linalg.norm(proj_g[:, :2], axis=1)
        gz = proj_g[:, 2]
        tilt_angle = np.arctan2(gxy, np.abs(gz) + 1e-8)
        fallen = (tilt_angle > np.deg2rad(70)) | (root_z < 0.12)
        dof_vel = self.get_dof_vel(data)
        bad = np.isnan(dof_vel).any(axis=1) | np.isinf(dof_vel).any(axis=1)
        terminated = fallen | bad
        return state.replace(terminated=terminated)

    def _compute_reward(self, data: mtx.SceneData, info: dict, velocity_commands: np.ndarray) -> np.ndarray:
        """Navigation reward: approach 2026 target + velocity tracking + stability."""
        num_envs = data.shape[0]
        pose = self._body.get_pose(data)
        root_pos = pose[:, :3]
        root_quat = pose[:, 3:7]

        # penalties
        termination_penalty = np.zeros(num_envs, dtype=np.float32)
        dof_vel = self.get_dof_vel(data)
        vel_max = np.abs(dof_vel).max(axis=1)
        termination_penalty = np.where(vel_max > 80.0, -10.0, termination_penalty)
        proj_g = self._compute_projected_gravity(root_quat)
        gxy = np.linalg.norm(proj_g[:, :2], axis=1)
        gz = proj_g[:, 2]
        tilt_angle = np.arctan2(gxy, np.abs(gz) + 1e-8)
        termination_penalty = np.where(tilt_angle > np.deg2rad(60), -10.0, termination_penalty)
        termination_penalty = np.where(root_pos[:, 2] < 0.15, -10.0, termination_penalty)

        # sensors
        try:
            base_lin_vel = np.asarray(self._model.get_sensor_value(self._cfg.sensor.base_linvel, data), dtype=np.float32)
        except Exception:
            base_lin_vel = np.zeros((num_envs, 3), dtype=np.float32)
        try:
            gyro = np.asarray(self._model.get_sensor_value(self._cfg.sensor.base_gyro, data), dtype=np.float32)
        except Exception:
            gyro = np.zeros((num_envs, 3), dtype=np.float32)
        if base_lin_vel.ndim == 1:
            base_lin_vel = base_lin_vel.reshape(1, -1)
        if gyro.ndim == 1:
            gyro = gyro.reshape(1, -1)

        lin_vel_error = np.sum(np.square(velocity_commands[:, :2] - base_lin_vel[:, :2]), axis=1)
        tracking_lin_vel = np.exp(-lin_vel_error / 0.25)
        ang_vel_error = np.square(velocity_commands[:, 2] - gyro[:, 2])
        tracking_ang_vel = np.exp(-ang_vel_error / 0.25)

        robot_position = root_pos[:, :2]
        robot_heading = self._get_heading_from_quat(root_quat)
        target_position = info["pose_commands"][:, :2]
        target_heading = info["pose_commands"][:, 2]
        position_error = target_position - robot_position
        distance_to_target = np.linalg.norm(position_error, axis=1)
        heading_diff = target_heading - robot_heading
        heading_diff = np.where(heading_diff > np.pi, heading_diff - 2 * np.pi, heading_diff)
        heading_diff = np.where(heading_diff < -np.pi, heading_diff + 2 * np.pi, heading_diff)

        reached_position = distance_to_target < 0.35
        reached_all = reached_position  # stairs-style: position only

        info["ever_reached"] = info.get("ever_reached", np.zeros(num_envs, dtype=bool))
        first_time_reach = np.logical_and(reached_all, ~info["ever_reached"])
        info["ever_reached"] = np.logical_or(info["ever_reached"], reached_all)
        arrival_bonus = np.where(first_time_reach, 20.0, 0.0)

        if "min_distance" not in info:
            info["min_distance"] = distance_to_target.copy()
        distance_improvement = info["min_distance"] - distance_to_target
        info["min_distance"] = np.minimum(info["min_distance"], distance_to_target)
        approach_reward = np.clip(distance_improvement * 6.0, -1.5, 1.5)

        # forward progress along +y toward 2026 platform
        if "last_y" not in info:
            info["last_y"] = robot_position[:, 1].copy()
        dy = robot_position[:, 1] - info["last_y"]
        info["last_y"] = robot_position[:, 1].copy()
        y_progress = np.clip(dy * 8.0, -1.0, 1.0)

        speed_xy = np.linalg.norm(base_lin_vel[:, :2], axis=1)
        stop_base = 2 * (0.8 * np.exp(-((speed_xy / 0.2) ** 2)) + 1.2 * np.exp(-((np.abs(gyro[:, 2]) / 0.1) ** 4)))
        stop_bonus = np.where(reached_all, stop_base + 4.0, 0.0)

        lin_vel_z_penalty = np.square(base_lin_vel[:, 2])
        ang_vel_xy_penalty = np.sum(np.square(gyro[:, :2]), axis=1)
        action_diff = info["current_actions"] - info["last_actions"]
        action_rate_penalty = np.sum(np.square(action_diff), axis=1)
        alive = 0.05

        reward = np.where(
            reached_all,
            (
                stop_bonus
                + arrival_bonus
                + alive
                - 2.0 * lin_vel_z_penalty
                - 0.05 * ang_vel_xy_penalty
                - 0.001 * action_rate_penalty
                + termination_penalty
            ),
            (
                1.2 * tracking_lin_vel
                + 0.25 * tracking_ang_vel
                + approach_reward
                + y_progress
                + alive
                - 2.0 * lin_vel_z_penalty
                - 0.05 * ang_vel_xy_penalty
                - 0.001 * action_rate_penalty
                + termination_penalty
            ),
        )
        return reward.astype(np.float32)

'''

# replace from _compute_terminated through end of stub _compute_reward
start = src.find("    def _compute_terminated(self, state: NpEnvState) -> NpEnvState:")
end = src.find("    def reset(self, data: mtx.SceneData, done: np.ndarray = None)")
if start < 0 or end < 0:
    # maybe already replaced
    if "y_progress" in src and "approach_reward" in src:
        print("reward already injected")
    else:
        raise SystemExit(f"markers missing start={start} end={end}")
else:
    src = src[:start] + NEW_TERM + src[end:]
    p.write_text(src, encoding="utf-8")
    print("injected reward+termination")

# smoke
import numpy as np
import motrix_envs, motrix_rl.cfgs
from motrix_envs import registry as er
env = er.make("vbot_navigation_section01", "np", num_envs=1)
st = env.init_state()
rng = np.random.default_rng(0)
rs = []
for i in range(20):
    st = env.step(rng.uniform(-0.2, 0.2, (1, 12)).astype(np.float32))
    rs.append(float(st.reward[0]))
print("reward sample", rs[:5], "... mean", float(np.mean(rs)))
print("REWARD_OK")
