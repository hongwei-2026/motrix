import os
# -*- coding: utf-8 -*-
import paramiko
import time

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
    return o.read().decode("utf-8", "replace")

for i in range(6):
    print("===", i, "===")
    print(r("ls -lah /root/.cache/uv/.tmpaLkY0A/motrixsim/ 2>/dev/null; du -sh /root/.cache/uv/.tmpaLkY0A 2>/dev/null"))
    print(r("ps -p 4902 -o etime,pcpu,state,cmd --no-headers 2>/dev/null || echo dead"))
    time.sleep(10)
c.close()
