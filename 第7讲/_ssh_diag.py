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
    print("$", cmd)
    _, o, e = c.exec_command(cmd, timeout=60)
    print(o.read().decode("utf-8", "replace"))
    err = e.read().decode("utf-8", "replace")
    if err.strip():
        print("[err]", err)

r("ls -lah /proc/4902/fd 2>/dev/null | head -40")
r("ls -lah ~/.cache/uv/ 2>/dev/null | head; du -sh ~/.cache/uv 2>/dev/null")
r("find ~/.cache/uv -iname '*motrix*' 2>/dev/null | head; find /tmp -iname '*motrixsim*' 2>/dev/null | head")
r("cat /proc/4902/status | head -20; cat /proc/4902/wchan; ls -l /proc/4902/cwd")
r("ss -tp | grep 4902 || netstat -tp 2>/dev/null | grep 4902 || true")
c.close()
