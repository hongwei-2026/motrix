#!/usr/bin/env python3
from pathlib import Path

p = Path("motrix_rl/src/motrix_rl/skrl/jax/train/ppo.py")
bak = Path(str(p) + ".bak_inf")
src = bak.read_text() if bak.exists() else p.read_text()
if not bak.exists():
    bak.write_text(src)

old = """        fps = 60
        while True:
            t = time.time()
            outputs = agent.act(obs, timestep=0, timesteps=0)
            actions = outputs[-1].get("mean_actions", outputs[0])
            obs, _, _, _, _ = env.step(actions)
            env.render()
            delta_time = time.time() - t
            if delta_time < 1.0 / fps:
                time.sleep(1.0 / fps - delta_time)"""

new = """        fps = 60
        max_steps = int(__import__("os").environ.get("PLAY_MAX_STEPS", "2500"))
        import numpy as np
        log_f = open("/root/work/evidence_w8/rollout_xy_long.csv", "w")
        log_f.write("step,x,y,z,rew,force_norm\\n")
        model = env._env._model
        body_names = list(model.body_names)
        body_idx = 0
        for cand in ["base", "trunk", "torso", "pelvis", "VBot", "vbot", "robot"]:
            if cand in body_names:
                body_idx = body_names.index(cand)
                break
        b = getattr(env._env, "_body", None)
        for attr in ("index", "id", "body_index", "name"):
            if b is not None and hasattr(b, attr):
                val = getattr(b, attr)
                print("body attr", attr, val)
                if attr == "name" and val in body_names:
                    body_idx = body_names.index(val)
                elif isinstance(val, int):
                    body_idx = val
        print("using body_idx", body_idx, body_names[body_idx] if body_idx < len(body_names) else "?")
        for step_i in range(max_steps):
            t = time.time()
            outputs = agent.act(obs, timestep=0, timesteps=0)
            actions = outputs[-1].get("mean_actions", outputs[0])
            obs, rewards, _, _, _ = env.step(actions)
            env.render()
            try:
                data = env._env.state.data
                poses = np.asarray(model.get_link_poses(data))
                pos = poses[0, body_idx, :3]
                o = np.asarray(obs).reshape(-1)
                fn = float(np.linalg.norm(o[54:66])) if o.size >= 67 else 0.0
                r = float(np.asarray(rewards).reshape(-1)[0])
                log_f.write(f"{step_i},{float(pos[0])},{float(pos[1])},{float(pos[2])},{r},{fn}\\n")
                if step_i % 50 == 0:
                    print(f"step={step_i} pos={pos} rew={r:.4f} force={fn:.3f}")
            except Exception as e:
                if step_i == 0:
                    print("pos_log_fail", type(e), e)
            delta_time = time.time() - t
            if delta_time < 1.0 / fps:
                time.sleep(1.0 / fps - delta_time)
        log_f.close()
        print("PLAY_FINITE_DONE", max_steps)"""

if old not in src:
    src = bak.read_text()
if old not in src:
    raise SystemExit("ppo loop pattern missing")
p.write_text(src.replace(old, new, 1))
print("ppo patched")
