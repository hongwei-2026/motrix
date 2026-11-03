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

OUT.write_text("uv sync2 start\n", encoding="utf-8")

# install python 3.10 via uv if needed, then sync
run("pkill -f 'uv sync' || true")
_, pid, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; "
    "rm -f /tmp/uv_sync.log; "
    "nohup bash -lc '"
    "export PATH=$HOME/.local/bin:$PATH; "
    "cd /workspace/MotrixLab && "
    "uv python install 3.10 && "
    "uv sync --python 3.10 --all-packages --extra skrl-torch "
    "> /tmp/uv_sync.log 2>&1; "
    "echo EXIT:$? >> /tmp/uv_sync.log"
    "' >/dev/null 2>&1 & echo $!"
)
log(f"pid={pid.strip()}")

for i in range(240):
    time.sleep(20)
    _, logtxt, _ = run("tail -c 4000 /tmp/uv_sync.log 2>/dev/null || echo NOLOG")
    _, ps, _ = run("ps aux | grep -E 'uv sync|uv python' | grep -v grep || true")
    _, ready, _ = run(
        "du -sh /workspace/MotrixLab/.venv 2>/dev/null; "
        "ls /workspace/MotrixLab/.venv/bin 2>/dev/null | tr '\\n' ' '; echo; "
        "test -x /workspace/MotrixLab/.venv/bin/python && /workspace/MotrixLab/.venv/bin/python -V || true"
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
