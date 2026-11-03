import os
# -*- coding: utf-8 -*-
"""Install uv, clone MotrixLab, inspect train/play CLI."""
import paramiko
import time

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


def run(cmd, timeout=600):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
    out_chunks = []
    err_chunks = []
    while True:
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(4096).decode("utf-8", errors="replace")
            out_chunks.append(chunk)
            print(chunk, end="")
        if stdout.channel.recv_stderr_ready():
            chunk = stdout.channel.recv_stderr(4096).decode("utf-8", errors="replace")
            err_chunks.append(chunk)
            print("[stderr]", chunk, end="")
        if stdout.channel.exit_status_ready():
            # drain
            while stdout.channel.recv_ready():
                chunk = stdout.channel.recv(4096).decode("utf-8", errors="replace")
                out_chunks.append(chunk)
                print(chunk, end="")
            break
        time.sleep(0.05)
    code = stdout.channel.recv_exit_status()
    print(f"\n[exit={code}]")
    return code, "".join(out_chunks), "".join(err_chunks)


# install uv
run("curl -LsSf https://astral.sh/uv/install.sh | sh")
run('export PATH="$HOME/.local/bin:$PATH"; which uv; uv --version')

# clone MotrixLab
run("cd /workspace && git clone --depth 1 https://github.com/Motphys/MotrixLab.git")
run("cd /workspace/MotrixLab && git lfs install && git lfs pull")
run("cd /workspace/MotrixLab && ls -la && ls scripts 2>/dev/null; ls install* 2>/dev/null")
run("cd /workspace/MotrixLab && head -80 scripts/train.py 2>/dev/null || echo NO_TRAIN")
run("cd /workspace/MotrixLab && ls scripts/; rg -n 'add_argument|--env|env=' scripts/train.py scripts/play.py 2>/dev/null | head -40")
run("cd /workspace/MotrixLab && git tag | tail -30; git branch -a | head -20; git log -1 --oneline")

client.close()
