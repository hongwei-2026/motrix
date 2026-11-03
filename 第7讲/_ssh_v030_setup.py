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

def run(cmd, timeout=300):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err

def log(msg):
    safe = msg.encode("ascii", "replace").decode("ascii")
    print(safe)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")

OUT.write_text("", encoding="utf-8")
_, out, _ = run("ls -la /workspace/MotrixLab | head -60")
log(out)
_, out, _ = run("ls /workspace/MotrixLab/*.toml /workspace/MotrixLab/*.md /workspace/MotrixLab/*.sh /workspace/MotrixLab/*.ps1 2>/dev/null")
log(out)
_, out, _ = run("sed -n '1,200p' /workspace/MotrixLab/README.md")
log(out)
_, out, _ = run("sed -n '1,120p' /workspace/MotrixLab/pyproject.toml")
log(out)
_, out, _ = run("ls /tmp/lfs_pull.log 2>/dev/null; tail -20 /tmp/lfs_pull.log 2>/dev/null")
log(out)

client.close()
