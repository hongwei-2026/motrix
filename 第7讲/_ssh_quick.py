import os
# -*- coding: utf-8 -*-
import paramiko

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

def r(cmd):
    _, o, e = c.exec_command(cmd, timeout=60)
    print(o.read().decode("utf-8", "replace"))
    err = e.read().decode("utf-8", "replace")
    if err.strip():
        print("[err]", err)

r("ps aux | grep -E 'uv sync|uv python' | grep -v grep || echo none")
r("du -sh /workspace/MotrixLab/.venv")
r("tail -c 1500 /tmp/uv_sync.log")
c.close()
