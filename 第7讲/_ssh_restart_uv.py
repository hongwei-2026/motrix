import os
# -*- coding: utf-8 -*-
"""Kill hung sync and retry with China-friendly index if needed."""
import paramiko
import time
from pathlib import Path

OUT = Path(r"D:\motrix\第7讲\_install_status.txt")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "39.145.28.59",
    32222,
    "root+vm-LEAjLhYIUQymN0v7",
    os.environ.get("MOTRIX_SSH_PASS", ""),
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)

def run(cmd, timeout=120):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode("utf-8", "replace")
    err = e.read().decode("utf-8", "replace")
    code = o.channel.recv_exit_status()
    return code, out, err

def log(msg):
    print(msg.encode("ascii", "replace").decode("ascii"))
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

_, out, _ = run("ls -lah /root/.cache/uv/.tmpaLkY0A/motrixsim/motrixsim*.so 2>/dev/null; du -sh /root/.cache/uv/.tmpaLkY0A 2>/dev/null")
log("before kill:\n" + out)

# kill hung
run("pkill -9 -f 'uv sync' || true; sleep 2")
run("rm -rf /root/.cache/uv/.tmpaLkY0A /workspace/MotrixLab/.venv")

# retry with default + longer; also set UV_HTTP_TIMEOUT
_, pid, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; "
    "rm -f /tmp/uv_sync.log; "
    "nohup bash -lc '"
    "export PATH=$HOME/.local/bin:$PATH; "
    "export UV_HTTP_TIMEOUT=300; "
    "cd /workspace/MotrixLab && "
    "uv sync --python 3.10 --all-packages --extra skrl-torch --reinstall-package motrixsim "
    "> /tmp/uv_sync.log 2>&1; "
    "echo EXIT:$? >> /tmp/uv_sync.log"
    "' >/dev/null 2>&1 & echo $!"
)
log(f"restart pid={pid.strip()}")

for i in range(180):
    time.sleep(20)
    _, logtxt, _ = run("tail -c 2500 /tmp/uv_sync.log 2>/dev/null || echo NOLOG")
    _, ps, _ = run("ps aux | grep 'uv sync' | grep -v grep || true")
    _, so, _ = run("ls -lah /root/.cache/uv/.tmp*/motrixsim/*.so 2>/dev/null | tail -3; du -sh /workspace/MotrixLab/.venv 2>/dev/null")
    msg = f"=== poll {i} ===\n{so}\nPS:\n{ps}\nLOG:\n{logtxt}\n"
    log(msg)
    if "EXIT:0" in logtxt:
        log("UV SYNC SUCCESS")
        break
    if "EXIT:" in logtxt:
        log("UV SYNC FAILED")
        break
else:
    log("TIMEOUT")

c.close()
