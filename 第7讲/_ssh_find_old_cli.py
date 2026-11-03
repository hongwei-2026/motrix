import os
# -*- coding: utf-8 -*-
import paramiko
import sys
from pathlib import Path

HOST = "39.145.28.59"
PORT = 32222
USER = "root+vm-LEAjLhYIUQymN0v7"
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")
LOG = Path(r"D:\motrix\第7讲\_remote_log.txt")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    HOST, port=PORT, username=USER, password=PASSWORD,
    timeout=30, allow_agent=False, look_for_keys=False,
)

def run(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    err_part = ("[stderr]\n" + err) if err.strip() else ""
    text = f"$ {cmd}\n{out}{err_part}[exit={code}]\n"
    print(text)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(text + "\n")
    return code, out, err

LOG.write_text("", encoding="utf-8")
run("ps aux | grep -E 'uv sync|install.sh|git lfs' | grep -v grep")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && git tag --sort=-v:refname | head -40")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && git log --all --oneline -- scripts/train.py | head -20")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && git log --all --diff-filter=A --summary -- scripts/train.py | head -40")
run("export PATH=$HOME/.local/bin:$PATH; which mxlab; ls /workspace/MotrixLab/.venv/bin 2>/dev/null | head")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && cat configs/task/cartpole/skrl.ppo.yaml")
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && grep -R \"train.py\" -n README.md docs 2>/dev/null | head -20")
run("ls -la /workspace/MotrixLab/.venv 2>/dev/null; du -sh /workspace/MotrixLab/.venv 2>/dev/null")

client.close()
