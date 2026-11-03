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
    HOST,
    port=PORT,
    username=USER,
    password=PASSWORD,
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)

def run(cmd, timeout=120):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if out.strip():
        print(out.rstrip())
    if err.strip():
        print("[stderr]", err.rstrip())
    print(f"[exit={code}]")
    return code, out, err

run("pwd; ls -la")
run("ls -la /workspace /data /opt /mnt 2>/dev/null; ls / 2>/dev/null")
run("find /root /workspace /data /home /opt /mnt -maxdepth 4 \\( -name 'train.py' -o -name 'play.py' -o -name 'pyproject.toml' -o -name '.git' \\) 2>/dev/null | head -80")
run("which uv python3 nvidia-smi git; uv --version; python3 --version; nvidia-smi | head -25")
run("ls -la /root/*/ 2>/dev/null | head -80")
run("du -sh /root/* 2>/dev/null | head -40")

client.close()
