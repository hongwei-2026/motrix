import os
# -*- coding: utf-8 -*-
import paramiko
import time

HOST = "39.145.28.59"
PORT = 32222
USER = "root+vm-LEAjLhYIUQymN0v7"
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")
CKPT = "runs/cartpole/skrl/26-10-21_11-04-41-419926_PPO/checkpoints/best_agent.pt"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, PORT, USER, PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)


def run(cmd, timeout=60):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode("utf-8", "replace")
    err = e.read().decode("utf-8", "replace")
    code = o.channel.recv_exit_status()
    return code, out, err


# patch play.py to disable render
code, out, err = run(
    "cd /workspace/MotrixLab && python3 - <<'PY'\n"
    "from pathlib import Path\n"
    "p = Path('scripts/play.py')\n"
    "t = p.read_text()\n"
    "if 'enable_render = False  # headless evidence' in t:\n"
    "    print('already_patched')\n"
    "elif 'enable_render = True' in t:\n"
    "    p.write_text(t.replace('enable_render = True', 'enable_render = False  # headless evidence', 1))\n"
    "    print('patched')\n"
    "else:\n"
    "    print('pattern_missing')\n"
    "    print(t[t.find('enable_render')-40:t.find('enable_render')+80] if 'enable_render' in t else 'no')\n"
    "PY"
)
print("patch:", out, err)

# also check wrap_np - if enable_render False, should skip renderer
code, out, _ = run(
    "sed -n '1,80p' /workspace/MotrixLab/motrix_rl/src/motrix_rl/skrl/torch/wrap_np.py"
)
print("wrap_np:\n", out)

run("pkill -f 'scripts/play.py' || true")
_, pid, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "rm -f /tmp/play_headless.log; "
    "nohup bash -lc '"
    "export PATH=$HOME/.local/bin:$PATH; "
    "cd /workspace/MotrixLab && "
    f"uv run scripts/play.py --env cartpole --rllib skrl --policy {CKPT} --num-envs 1 "
    "> /tmp/play_headless.log 2>&1; echo PLAY_EXIT:$? >> /tmp/play_headless.log"
    "' >/dev/null 2>&1 & echo $!"
)
print("pid", pid.strip())

ok = False
for i in range(30):
    time.sleep(2)
    _, log, _ = run("cat /tmp/play_headless.log 2>/dev/null || true")
    print(f"=== {i} ===\n{log[-1200:]}")
    if "Using specified policy" in log and "Seed:" in log and "RenderClosedError" not in log and "panicked" not in log:
        # let it run a bit
        time.sleep(5)
        _, log, _ = run("cat /tmp/play_headless.log 2>/dev/null || true")
        ok = True
        break
    if "PLAY_EXIT:" in log or "RenderClosedError" in log or "panicked" in log:
        break

run("pkill -f 'scripts/play.py' || true; sleep 1; pkill -9 -f 'scripts/play.py' || true")
_, log, _ = run("cat /tmp/play_headless.log; echo; ps aux | grep play.py | grep -v grep || echo stopped")
print("FINAL ok=", ok)
print(log[-2000:])

# leave patched for user to use; print how to restore
print("NOTE: scripts/play.py is patched enable_render=False for headless cloud use")
c.close()
