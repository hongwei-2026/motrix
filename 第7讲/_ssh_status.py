import os
# -*- coding: utf-8 -*-
import paramiko

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

def run(cmd, timeout=60):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    print(out)
    if err.strip():
        print("[stderr]", err)
    print(f"[exit={code}]")
    return code, out, err

run("ps aux | grep -E 'git|clone|lfs' | grep -v grep")
run("ls -la /workspace; du -sh /workspace/MotrixLab 2>/dev/null; ls /workspace/MotrixLab 2>/dev/null | head")
run("df -h /workspace /tmp /root | head")

client.close()
