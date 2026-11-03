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

OUT.write_text("", encoding="utf-8")

# check repo
code, out, _ = run("ls /workspace/MotrixLab/scripts/train.py /workspace/MotrixLab/install.sh")
log(out)

# pull LFS if needed (may take time)
log("starting lfs pull...")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && nohup bash -lc 'git lfs pull > /tmp/lfs_pull.log 2>&1; echo LFS_EXIT:$? >> /tmp/lfs_pull.log' >/dev/null 2>&1 & echo $!")

# check install script for v0.3.0
_, helpout, _ = run("head -80 /workspace/MotrixLab/install.sh")
log(helpout[:2000])

# start install
run("pkill -f 'uv sync' || true; pkill -f install.sh || true")
_, pid, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "rm -f /tmp/motrix_install.log; "
    "nohup bash -lc 'bash install.sh > /tmp/motrix_install.log 2>&1; echo EXIT:$? >> /tmp/motrix_install.log' "
    ">/dev/null 2>&1 & echo $!"
)
log(f"install pid={pid.strip()}")

for i in range(200):
    time.sleep(20)
    _, logtxt, _ = run("tail -c 2500 /tmp/motrix_install.log 2>/dev/null || echo NOLOG")
    _, ps, _ = run("ps aux | grep -E 'uv sync|install.sh|git lfs' | grep -v grep || true")
    _, ready, _ = run(
        "du -sh /workspace/MotrixLab/.venv 2>/dev/null; "
        "ls /workspace/MotrixLab/.venv/bin 2>/dev/null | tr '\\n' ' '; echo; "
        "test -f /workspace/MotrixLab/.venv/bin/python && echo HAS_PY || echo NO_PY"
    )
    msg = f"=== poll {i} ===\n{ready}\nPS:\n{ps}\nLOGTAIL:\n{logtxt}\n"
    log(msg)
    if "EXIT:0" in logtxt:
        log("INSTALL SUCCESS")
        break
    if "EXIT:" in logtxt:
        log("INSTALL FAILED")
        break
else:
    log("TIMEOUT")

client.close()
