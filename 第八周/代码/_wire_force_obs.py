#!/usr/bin/env python3
"""Wire 12-dim foot force + 1 pad into 54-dim base obs -> 67 total."""
from pathlib import Path

p = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py")
src = p.read_text(encoding="utf-8")
bak = Path("/root/autodl-tmp/evidence_w8/vbot_section01_np.py.before_wire")
if not bak.exists():
    bak.write_text(src, encoding="utf-8")

# observation_space must be 67
src = src.replace(
    "shape=(54,), dtype=np.float32)",
    "shape=(67,), dtype=np.float32)",
)

OLD_ASSERT_A = "        assert obs.shape == (data.shape[0], 54)  # 54 + 1 = 55维"
OLD_ASSERT_B = "        assert obs.shape == (num_envs, 54)  # 54 + 1 = 55维"

# After building 54-dim base obs in update_state, append forces
INJECT_A = '''        assert obs.shape == (data.shape[0], 54)  # base 54
        foot_force = self._get_foot_contact_force(data, root_quat)
        pad = np.zeros((data.shape[0], 1), dtype=np.float32)
        obs = np.concatenate([obs, foot_force, pad], axis=-1)
        assert obs.shape == (data.shape[0], 67)
'''

INJECT_B = '''        assert obs.shape == (num_envs, 54)  # base 54
        foot_force = self._get_foot_contact_force(data, root_quat)
        pad = np.zeros((num_envs, 1), dtype=np.float32)
        obs = np.concatenate([obs, foot_force, pad], axis=-1)
        assert obs.shape == (num_envs, 67)
'''

if "_get_foot_contact_force" not in src:
    raise SystemExit("force helpers missing — run patch first")

if "obs, foot_force, pad], axis=-1)" in src:
    print("already wired")
else:
    if OLD_ASSERT_A not in src or OLD_ASSERT_B not in src:
        raise SystemExit("assert markers missing")
    src = src.replace(OLD_ASSERT_A, INJECT_A.rstrip("\n"), 1)
    src = src.replace(OLD_ASSERT_B, INJECT_B.rstrip("\n"), 1)
    # drop old print that confuses
    src = src.replace('        print(f"obs.shape:{obs.shape}")\n', "")
    p.write_text(src, encoding="utf-8")
    print("wired force into both obs paths")

print("force helper calls", src.count("_get_foot_contact_force("))
print("67 asserts", src.count("assert obs.shape == (") )
print("obs space 67", "shape=(67,), dtype=np.float32)" in src)
