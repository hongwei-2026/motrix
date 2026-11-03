import os
# -*- coding: utf-8 -*-
import paramiko
import time

HOST = "39.145.28.59"
PORT = 32222
USER = "root+vm-LEAjLhYIUQymN0v7"
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    HOST, port=PORT, username=USER, password=PASSWORD,
    timeout=30, allow_agent=False, look_for_keys=False,
)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out

for i in range(60):
    code, out = run("ps -p 1548 -o pid= 2>/dev/null; du -sh /workspace/MotrixLab 2>/dev/null; test -f /workspace/MotrixLab/install.sh && echo HAS_INSTALL || echo NO_INSTALL")
    print(f"[{i}] {out.strip()}")
    if "HAS_INSTALL" in out and "1548" not in out.splitlines()[0] if out.strip() else True:
        # if install.sh exists and clone pid gone
        _, ps = run("ps -p 1548 -o pid= 2>/dev/null || true")
        _, has = run("test -f /workspace/MotrixLab/install.sh && echo YES")
        if "YES" in has and not ps.strip():
            print("CLONE DONE")
            break
    time.sleep(10)
else:
    print("TIMEOUT waiting clone")

_, out = run("ls /workspace/MotrixLab | head -40; ls /workspace/MotrixLab/scripts 2>/dev/null; test -d /workspace/MotrixLab/.git && echo GIT_OK")
print(out)
client.close()
