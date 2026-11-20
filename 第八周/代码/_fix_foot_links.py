#!/usr/bin/env python3
"""Fix foot contact force to index link_names (FR_foot etc), not body_names."""
from pathlib import Path

p = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py")
src = p.read_text(encoding="utf-8")
old = '''            if self._foot_body_indices is None:
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
                print("[Info] foot body indices", idxs)'''
new = '''            if self._foot_body_indices is None:
                # Feet are LINKS (not top-level bodies) in scene_section01.
                names = [str(x) for x in self._model.link_names]
                idxs = []
                for key in ["FR_foot", "FL_foot", "RR_foot", "RL_foot"]:
                    idx = None
                    for i, n in enumerate(names):
                        if n == key or n.endswith("/" + key) or n.endswith(key):
                            idx = i
                            break
                    if idx is None:
                        idx = 0
                        print("[Warning] missing link", key)
                    idxs.append(idx)
                self._foot_body_indices = idxs
                print("[Info] foot LINK indices", idxs, "from", len(names), "links")'''
if old not in src:
    if "foot LINK indices" in src:
        print("already fixed")
    else:
        raise SystemExit("pattern missing")
else:
    src = src.replace(old, new, 1)
    p.write_text(src, encoding="utf-8")
    print("fixed foot link indices")

# smoke
import numpy as np
import motrix_envs, motrix_rl.cfgs
from motrix_envs import registry as er
env = er.make("vbot_navigation_section01", "np", num_envs=1)
st = env.init_state()
rng = np.random.default_rng(0)
for _ in range(40):
    st = env.step(rng.uniform(-0.4, 0.4, (1, 12)).astype(np.float32))
print("foot indices attr", getattr(env, "_foot_body_indices", None))
print("obs force", st.obs[0, 54:66])
print("force_norm", float(np.linalg.norm(st.obs[0, 54:66])))
print("rew", st.reward)
