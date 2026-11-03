import os
# -*- coding: utf-8 -*-
import paramiko
import time
from pathlib import Path

HOST = "39.145.28.59"
PORT = 32222
USER = "root+vm-LEAjLhYIUQymN0v7"
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")
OUT = Path(r"D:\motrix\第7讲\_install_status.txt")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    HOST, port=PORT, username=USER, password=PASSWORD,
    timeout=30, allow_agent=False, look_for_keys=False,
)

def run(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err

def log(msg):
    print(msg.encode("ascii", "replace").decode("ascii"))
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

OUT.write_text("uv sync start\n", encoding="utf-8")

# ensure python 3.10 available via uv
_, out, _ = run("export PATH=$HOME/.local/bin:$PATH; uv python list 2>/dev/null | head -20; which python3.10 || true")
log(out)

# LFS pull in correct dir
log("lfs pull...")
code, out, err = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && git lfs pull",
    timeout=1800,
)
log(f"lfs exit={code}\n{out[-2000:]}\n{err[-2000:]}")

# start uv sync in background
run("pkill -f 'uv sync' || true")
_, pid, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "rm -f /tmp/uv_sync.log; "
    "nohup bash -lc 'uv sync --all-packages --extra skrl-torch > /tmp/uv_sync.log 2>&1; "
    "echo EXIT:$? >> /tmp/uv_sync.log' >/dev/null 2>&1 & echo $!"
)
log(f"uv sync pid={pid.strip()}")

for i in range(240):
    time.sleep(20)
    _, logtxt, _ = run("tail -c 3000 /tmp/uv_sync.log 2>/dev/null || echo NOLOG")
    _, ps, _ = run("ps aux | grep 'uv sync' | grep -v grep || true")
    _, ready, _ = run(
        "du -sh /workspace/MotrixLab/.venv 2>/dev/null; "
        "ls /workspace/MotrixLab/.venv/bin 2>/dev/null | tr '\\n' ' '; echo; "
        "test -x /workspace/MotrixLab/.venv/bin/python && /workspace/MotrixLab/.venv/bin/python -V"
    )
    msg = f"=== poll {i} ===\n{ready}\nPS:\n{ps}\nLOG:\n{logtxt}\n"
    log(msg)
    if "EXIT:0" in logtxt:
        log("UV SYNC SUCCESS")
        break
    if "EXIT:" in logtxt:
        log("UV SYNC FAILED")
        break
else:
    log("TIMEOUT")

client.close()
