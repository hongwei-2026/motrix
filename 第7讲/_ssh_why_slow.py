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

r("date; ps -p 22959 -o etime,pcpu,cmd --no-headers 2>/dev/null || echo uv_dead")
r("ls -lah /root/.cache/uv/.tmpUWr6Kh/motrixsim/*.so 2>/dev/null; du -sh /root/.cache/uv/.tmpUWr6Kh 2>/dev/null")
r("tail -n 15 /tmp/uv_sync.log")
r("du -sh /root/.cache/uv /workspace/MotrixLab/.venv 2>/dev/null")
c.close()
