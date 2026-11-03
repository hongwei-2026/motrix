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


def run(cmd, timeout=1800):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
    while True:
        if stdout.channel.recv_ready():
            print(stdout.channel.recv(8192).decode("utf-8", errors="replace"), end="")
        if stdout.channel.recv_stderr_ready():
            print(stdout.channel.recv_stderr(8192).decode("utf-8", errors="replace"), end="")
        if stdout.channel.exit_status_ready():
            while stdout.channel.recv_ready():
                print(stdout.channel.recv(8192).decode("utf-8", errors="replace"), end="")
            break
        time.sleep(0.05)
    code = stdout.channel.recv_exit_status()
    print(f"\n[exit={code}]")
    return code


run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && ls scripts && sed -n '1,120p' scripts/train.py")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && sed -n '1,120p' scripts/play.py")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && ls configs/task/cartpole 2>/dev/null; ls configs/task | head")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && bash install.sh --help | head -80")

# install with cuda / default
code = run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && bash install.sh --python 3.12 2>&1")
print("install code", code)

client.close()
