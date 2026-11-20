#!/usr/bin/env python3
"""Patch foot-contact force obs on SeetaCloud autodl-tmp MotrixLab."""
from pathlib import Path

p = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py")
src = p.read_text(encoding="utf-8")
bak = Path("/root/autodl-tmp/evidence_w8/vbot_section01_np.py.before_force")
bak.parent.mkdir(parents=True, exist_ok=True)
if not bak.exists():
    bak.write_text(src, encoding="utf-8")

src = src.replace("shape=(54,), dtype=np.float32)", "shape=(67,), dtype=np.float32)")

NEW_BLOCK = '''    def _init_foot_contact(self):
        self.foot_contact_check = np.zeros((0, 2), dtype=np.uint32)
        self.num_foot_check = 4
        # ONLY suffix sensors exist in scene_section01.xml — bare names panic in Rust.
        self._foot_contact_sensor_groups = [
            ["FR_foot_contact_1", "FR_foot_contact_2", "FR_foot_contact_3"],
            ["FL_foot_contact_1", "FL_foot_contact_2", "FL_foot_contact_3"],
            ["RR_foot_contact_1", "RR_foot_contact_2", "RR_foot_contact_3"],
            ["RL_foot_contact_1", "RL_foot_contact_2", "RL_foot_contact_3"],
        ]
        self._missing_contact_sensors = set()
        self._foot_body_indices = None
        try:
            if hasattr(self._model, "reports"):
                self._model.reports.contact_forces = True
                print("[Info] enabled model.reports.contact_forces")
        except Exception as e:
            print("[Warning] cannot enable contact_forces report:", e)

    def _safe_get_contact_sensor(self, name: str, data: mtx.SceneData):
        if name in self._missing_contact_sensors:
            return None
        try:
            return self._model.get_sensor_value(name, data)
        except BaseException:
            self._missing_contact_sensors.add(name)
            return None

    def _sensor_value_to_force_vec(self, sensor_value, num_envs: int) -> np.ndarray:
        if sensor_value is None:
            return np.zeros((num_envs, 3), dtype=np.float32)
        value = np.asarray(sensor_value, dtype=np.float32)
        if value.ndim == 0:
            return np.tile(np.array([[0.0, 0.0, float(value)]], dtype=np.float32), (num_envs, 1))
        if value.ndim == 1:
            if value.shape[0] == num_envs:
                return np.stack([np.zeros_like(value), np.zeros_like(value), value], axis=1).astype(np.float32)
            if num_envs == 1 and value.shape[0] >= 3:
                return value[:3].reshape(1, 3).astype(np.float32)
            scalar = float(value.reshape(-1)[0]) if value.size > 0 else 0.0
            return np.tile(np.array([[0.0, 0.0, scalar]], dtype=np.float32), (num_envs, 1))
        if value.shape[0] != num_envs:
            flat = value.reshape(-1)
            sample = np.zeros(3, dtype=np.float32)
            if flat.size >= 3:
                sample = flat[:3].astype(np.float32)
            elif flat.size > 0:
                sample[2] = float(flat[0])
            return np.tile(sample.reshape(1, 3), (num_envs, 1))
        if value.shape[1] >= 3:
            return value[:, :3].astype(np.float32)
        if value.shape[1] == 2:
            return np.concatenate([value, np.zeros((num_envs, 1), dtype=np.float32)], axis=1).astype(np.float32)
        if value.shape[1] == 1:
            return np.concatenate([np.zeros((num_envs, 2), dtype=np.float32), value], axis=1).astype(np.float32)
        return np.zeros((num_envs, 3), dtype=np.float32)

    def _get_foot_contact_force(self, data: mtx.SceneData, root_quat: np.ndarray) -> np.ndarray:
        """Return foot contact force [num_envs, 12] in body frame."""
        num_envs = data.shape[0]
        try:
            forces = np.asarray(self._model.get_link_net_contact_forces(data), dtype=np.float32)
            if self._foot_body_indices is None:
                names = [str(x) for x in self._model.body_names]
                idxs = []
                for key in ["FR_foot", "FL_foot", "RR_foot", "RL_foot"]:
                    idx = None
                    for i, n in enumerate(names):
                        if n == key or n.endswith("/" + key) or key in n:
                            idx = i
                            break
                    idxs.append(0 if idx is None else idx)
                self._foot_body_indices = idxs
                print("[Info] foot body indices", idxs)
            if forces.ndim == 3:
                parts = [forces[:, i, :3] for i in self._foot_body_indices]
                world = np.concatenate(parts, axis=1).astype(np.float32)
                if float(np.linalg.norm(world)) > 1e-8:
                    reshaped = world.reshape(num_envs, 4, 3)
                    rotated = [Quaternion.rotate_inverse(root_quat, reshaped[:, i, :]) for i in range(4)]
                    return np.concatenate(rotated, axis=1).astype(np.float32)
        except BaseException:
            pass

        force_list = []
        for sensor_group in self._foot_contact_sensor_groups:
            group_force = np.zeros((num_envs, 3), dtype=np.float32)
            group_force_norm = np.zeros((num_envs,), dtype=np.float32)
            for sensor_name in sensor_group:
                sensor_value = self._safe_get_contact_sensor(sensor_name, data)
                force_vec = self._sensor_value_to_force_vec(sensor_value, num_envs)
                force_norm = np.linalg.norm(force_vec, axis=1)
                take_mask = force_norm > group_force_norm
                if np.any(take_mask):
                    group_force[take_mask] = force_vec[take_mask]
                    group_force_norm[take_mask] = force_norm[take_mask]
            force_list.append(group_force)
        while len(force_list) < 4:
            force_list.append(np.zeros((num_envs, 3), dtype=np.float32))
        force_list = force_list[:4]
        contact_force_world = np.concatenate(force_list, axis=1).astype(np.float32)
        reshaped = contact_force_world.reshape(num_envs, 4, 3)
        rotated = [Quaternion.rotate_inverse(root_quat, reshaped[:, i, :]) for i in range(4)]
        return np.concatenate(rotated, axis=1).astype(np.float32)

'''

start = src.find("    def _init_foot_contact(self):")
end = src.find("    def get_dof_pos(self, data: mtx.SceneData):")
if start < 0 or end < 0 or end <= start:
    raise SystemExit(f"markers missing start={start} end={end}")
src = src[:start] + NEW_BLOCK + src[end:]

src = src.replace(
    "        contact_force = np.zeros((base_obs.shape[0], 12), dtype=np.float32)\n"
    "        pad = np.zeros((base_obs.shape[0], 1), dtype=np.float32)\n"
    "        obs = np.concatenate([base_obs, contact_force, pad], axis=-1)",
    "        foot_force = self._get_foot_contact_force(data, root_quat)\n"
    "        pad = np.zeros((base_obs.shape[0], 1), dtype=np.float32)\n"
    "        obs = np.concatenate([base_obs, foot_force, pad], axis=-1)",
)
src = src.replace(
    "        contact_force = np.zeros((num_envs, 12), dtype=np.float32)\n"
    "        pad = np.zeros((num_envs, 1), dtype=np.float32)\n"
    "        obs = np.concatenate([base_obs, contact_force, pad], axis=-1)",
    "        foot_force = self._get_foot_contact_force(data, root_quat)\n"
    "        pad = np.zeros((num_envs, 1), dtype=np.float32)\n"
    "        obs = np.concatenate([base_obs, foot_force, pad], axis=-1)",
)

p.write_text(src, encoding="utf-8")
print("patched", p)
print("force calls", src.count("_get_foot_contact_force"))
print("has bare FR_foot_contact quote", '"FR_foot_contact"' in src)
