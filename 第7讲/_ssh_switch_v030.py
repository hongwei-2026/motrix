import os
# -*- coding: utf-8 -*-
import paramiko
import time
from pathlib import Path

HOST = "39.145.28.59"
PORT = 32222
USER = "root+vm-LEAjLhYIUQymN0v7"
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")
OUT = Path(r"D:\motrix\第7讲\_install_status.txt")

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
    print(f"$ {cmd}\n{out}")
    if err.strip():
        print("[stderr]", err)
    print(f"[exit={code}]")
    return code, out, err

# stop ongoing install
run("pkill -f 'uv sync' || true; pkill -f install.sh || true; sleep 2; ps aux | grep -E 'uv sync|install.sh' | grep -v grep || echo no_install")

# replace repo with v0.3.0
run("rm -rf /workspace/MotrixLab")
run(
    "export PATH=$HOME/.local/bin:$PATH; "
    "cd /workspace && "
    "GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --branch v0.3.0 https://github.com/Motphys/MotrixLab.git"
)
run("export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && git lfs install && git lfs pull")
run("ls /workspace/MotrixLab/scripts; head -60 /workspace/MotrixLab/scripts/train.py")
run("head -40 /workspace/MotrixLab/README.md; ls /workspace/MotrixLab/install*")

# start install background
cmd = (
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "rm -f /tmp/motrix_install.log; "
    "nohup bash -lc 'bash install.sh > /tmp/motrix_install.log 2>&1; echo EXIT:$? >> /tmp/motrix_install.log' "
    ">/dev/null 2>&1 & echo $!"
)
_, pid, _ = run(cmd)
print("install pid", pid.strip())
OUT.write_text(f"v0.3.0 install pid={pid.strip()}\n", encoding="utf-8")

for i in range(180):
    time.sleep(20)
    _, log, _ = run("tail -n 40 /tmp/motrix_install.log 2>/dev/null || echo NOLOG")
    _, ps, _ = run("ps aux | grep -E 'uv sync|install.sh' | grep -v grep || true")
    _, ready, _ = run(
        "du -sh /workspace/MotrixLab/.venv 2>/dev/null; "
        "test -x /workspace/MotrixLab/.venv/bin/python && echo HAS_PY || echo NO_PY; "
        "ls /workspace/MotrixLab/.venv/bin 2>/dev/null | head"
    )
    status = f"\n=== poll {i} ===\n{ready}\nPS:{ps}\nLOG:\n{log}\n"
    print(status)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(status)
    if "EXIT:0" in log:
        print("SUCCESS")
        break
    if "EXIT:" in log and "EXIT:0" not in log:
        print("FAILED")
        break
else:
    print("TIMEOUT")

client.close()
