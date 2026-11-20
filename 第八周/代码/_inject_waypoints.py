#!/usr/bin/env python3
"""Inject waypoint curriculum + anti-stall into section01 (keep 67-dim force obs)."""
from pathlib import Path
import re

ENV = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py")
CFG = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/cfg.py")
OUT = Path("/root/autodl-tmp/evidence_w8")

t = ENV.read_text(encoding="utf-8")
bak = OUT / "vbot_section01_np.py.before_waypoint"
if not bak.exists():
    bak.write_text(t, encoding="utf-8")

# 1) Ensure waypoint list on env after spawn_center init
if "self.waypoint_targets" not in t:
    needle = "self.spawn_center = np.array(cfg.init_state.pos, dtype=np.float32)"
    i = t.find(needle)
    assert i > 0
    # insert after spawn_range line
    j = t.find("\n", t.find("spawn_range", i))
    inject = '''
        # Waypoint curriculum toward 2026 platform (-2.7, 8.0)
        self.waypoint_targets = np.asarray([
            [0.0, -0.60],
            [0.0, 1.20],
            [0.0, 2.25],
            [-0.7, 3.8],
            [-1.7, 5.8],
            [-2.7, 8.0],
        ], dtype=np.float32)
        self.waypoint_threshold = 0.45
'''
    t = t[: j + 1] + inject + t[j + 1 :]
    print("waypoint attrs added")

# 2) Helper method before _compute_reward
HELPER = '''
    def _advance_waypoints(self, info: dict, robot_xy: np.ndarray) -> dict:
        """Advance pose_commands along waypoint list when close / past in +y."""
        num_envs = robot_xy.shape[0]
        wps = self.waypoint_targets
        idx = info.get("waypoint_index")
        if idx is None:
            idx = np.zeros(num_envs, dtype=np.int32)
        idx = np.asarray(idx, dtype=np.int32).reshape(num_envs)
        idx = np.clip(idx, 0, len(wps) - 1)
        target = wps[idx]
        dist = np.linalg.norm(target - robot_xy, axis=1)
        y = robot_xy[:, 1]
        # forced advance if past waypoint y (avoids stuck circling)
        forced = (
            ((idx == 1) & (y > 1.05))
            | ((idx == 2) & (y > 2.05))
            | ((idx == 3) & (y > 3.5))
            | ((idx == 4) & (y > 5.5))
        )
        reached = (dist < self.waypoint_threshold) | forced
        is_last = idx >= (len(wps) - 1)
        advance = reached & (~is_last)
        idx = np.where(advance, np.minimum(idx + 1, len(wps) - 1), idx)
        target = wps[idx]
        pose = info.get("pose_commands")
        if pose is None:
            pose = np.zeros((num_envs, 3), dtype=np.float32)
        else:
            pose = np.asarray(pose, dtype=np.float32).copy()
        pose[:, 0] = target[:, 0]
        pose[:, 1] = target[:, 1]
        pose[:, 2] = 0.0
        info["pose_commands"] = pose
        info["waypoint_index"] = idx
        info["waypoint_reached"] = advance
        info["ever_reached_2026"] = info.get("ever_reached_2026", np.zeros(num_envs, dtype=bool))
        at_final = is_last & (dist < self.waypoint_threshold)
        # also count y>=7.5 near platform as success
        at_final = at_final | ((y >= 7.5) & (np.abs(robot_xy[:, 0] + 2.7) < 1.5))
        info["ever_reached_2026"] = np.logical_or(info["ever_reached_2026"], at_final)
        return info

'''

if "def _advance_waypoints" not in t:
    mark = "    def _compute_reward(self, data: mtx.SceneData, info: dict, velocity_commands: np.ndarray) -> np.ndarray:"
    i = t.find(mark)
    assert i > 0, "reward method missing"
    t = t[:i] + HELPER + t[i:]
    print("helper inserted")

# 3) Call advance at start of _compute_reward (after root_pos)
old_anchor = "        robot_position = root_pos[:, :2]\n        robot_heading = self._get_heading_from_quat(root_quat)\n        target_position = info[\"pose_commands\"][:, :2]"
new_anchor = """        robot_position = root_pos[:, :2]
        info = self._advance_waypoints(info, robot_position)
        robot_heading = self._get_heading_from_quat(root_quat)
        target_position = info["pose_commands"][:, :2]"""
if "self._advance_waypoints(info, robot_position)" not in t:
    if old_anchor in t:
        t = t.replace(old_anchor, new_anchor, 1)
        print("advance hooked in reward")
    else:
        # try looser
        alt = "        robot_position = root_pos[:, :2]\n        robot_heading = self._get_heading_from_quat(root_quat)"
        if alt in t and "self._advance_waypoints" not in t.split("def _compute_reward")[1][:800]:
            t = t.replace(
                alt,
                "        robot_position = root_pos[:, :2]\n        info = self._advance_waypoints(info, robot_position)\n        robot_heading = self._get_heading_from_quat(root_quat)",
                1,
            )
            print("advance hooked (alt)")
        else:
            print("WARN: could not hook advance precisely")

# 4) Strengthen reward: anti-stall + bigger reach + y progress already boosted
# Add anti_stall into non-reached branch if missing
if "anti_stall" not in t:
    # insert before reward = np.where
    stall_code = """
        # anti-stall: commanded move but body barely moves
        speed_xy = np.linalg.norm(base_lin_vel[:, :2], axis=1)
        cmd_speed = np.linalg.norm(velocity_commands[:, :2], axis=1)
        anti_stall = np.clip(cmd_speed - speed_xy, 0.0, 1.0) * (cmd_speed > 0.15).astype(np.float32)
        wp_bonus = np.where(info.get("waypoint_reached", np.zeros(num_envs, dtype=bool)), 8.0, 0.0)
        final_bonus = np.where(
            np.logical_and(info.get("ever_reached_2026", np.zeros(num_envs, dtype=bool)),
                           ~info.get("final_bonus_given", np.zeros(num_envs, dtype=bool))),
            300.0, 0.0)
        info["final_bonus_given"] = np.logical_or(
            info.get("final_bonus_given", np.zeros(num_envs, dtype=bool)),
            info.get("ever_reached_2026", np.zeros(num_envs, dtype=bool)),
        )
"""
    anchor = "        alive = 0.05\n\n        reward = np.where("
    if anchor in t:
        t = t.replace(anchor, stall_code + "\n        alive = 0.05\n\n        reward = np.where(", 1)
        # add terms into non-reached branch
        t = t.replace(
            "+ approach_reward\n                + y_progress\n                + alive",
            "+ approach_reward\n                + y_progress\n                + wp_bonus\n                + final_bonus\n                - 0.8 * anti_stall\n                + alive",
            1,
        )
        t = t.replace(
            "+ arrival_bonus\n                + alive",
            "+ arrival_bonus\n                + wp_bonus\n                + final_bonus\n                + alive",
            1,
        )
        print("anti_stall + wp bonuses added")
    else:
        print("WARN: stall insert failed")

# 5) Reset: init waypoint_index and first pose
# Find where pose_commands assigned in reset
if '"waypoint_index"' not in t.split("def reset")[-1] if "def reset" in t else True:
    # after pose_commands = np.concatenate
    pat = "pose_commands = np.concatenate([target_positions, target_headings], axis=1)"
    if pat in t and "waypoint_index" not in t[t.find(pat) : t.find(pat) + 400]:
        t = t.replace(
            pat,
            pat
            + """
        # start at first waypoint on path to 2026
        waypoint_index = np.zeros(num_envs, dtype=np.int32)
        pose_commands[:, :2] = self.waypoint_targets[waypoint_index]
        pose_commands[:, 2] = 0.0
""",
            1,
        )
        # add to info dict in reset
        if '"pose_commands": pose_commands,' in t and '"waypoint_index"' not in t:
            t = t.replace(
                '"pose_commands": pose_commands,',
                '"pose_commands": pose_commands,\n            "waypoint_index": waypoint_index,\n            "waypoint_reached": np.zeros(num_envs, dtype=bool),\n            "ever_reached_2026": np.zeros(num_envs, dtype=bool),\n            "final_bonus_given": np.zeros(num_envs, dtype=bool),',
                1,
            )
        print("reset waypoint init")
    else:
        print("reset already has waypoint or pattern missing")

ENV.write_text(t, encoding="utf-8")
print("ENV written", ENV.stat().st_size)

# 6) cfg: action_scale 0.45 + long episode + pose at final for fallback
ct = CFG.read_text(encoding="utf-8")
marker = '@registry.envcfg("vbot_navigation_section01")'
i = ct.find(marker)
j = ct.find("@registry.envcfg", i + 10)
block = ct[i:j]
block2 = re.sub(r"max_episode_seconds: float = [0-9.]+", "max_episode_seconds: float = 100.0", block, count=1)
block2 = re.sub(r"max_episode_steps: int = \\d+", "max_episode_steps: int = 10000", block2, count=1)
block2 = re.sub(r"max_episode_steps: int = \d+", "max_episode_steps: int = 10000", block2, count=1)
block2 = re.sub(
    r"pose_command_range = \[[^\]]+\]",
    "pose_command_range = [-2.7, 8.0, 0.0, -2.7, 8.0, 0.0]",
    block2,
    count=1,
)
# action_scale in ControlConfig of this block
block2 = re.sub(r"action_scale = 0\.25", "action_scale = 0.45", block2, count=1)
CFG.write_text(ct[:i] + block2 + ct[j:], encoding="utf-8")
print("CFG patched")
print([ln for ln in block2.splitlines() if "action_scale" in ln or "pose_command" in ln or "max_episode" in ln])

# syntax check
compile(ENV.read_text(encoding="utf-8"), str(ENV), "exec")
print("WAYPOINT_INJECT_OK")
