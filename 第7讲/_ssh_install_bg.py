import os
# -*- coding: utf-8 -*-
"""Start install.sh in background on remote, logging to file."""
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

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err

# kill leftover incomplete venv lock if any
run("pkill -f 'uv sync' || true; pkill -f install.sh || true")

# start install in background via nohup
cmd = (
    "export PATH=$HOME/.local/bin:$PATH; "
    "cd /workspace/MotrixLab && "
    "nohup bash -lc 'bash install.sh --python 3.12 > /tmp/motrix_install.log 2>&1; "
    "echo EXIT:$? >> /tmp/motrix_install.log' >/dev/null 2>&1 & echo $!"
)
code, out, err = run(cmd)
print("started pid:", out.strip())
OUT.write_text(f"started {out.strip()}\n", encoding="utf-8")

# poll
for i in range(120):
    time.sleep(15)
    _, log, _ = run("tail -n 30 /tmp/motrix_install.log 2>/dev/null || echo NOLOG")
    _, ps, _ = run("ps aux | grep -E 'uv sync|install.sh' | grep -v grep || true")
    _, venv, _ = run("du -sh /workspace/MotrixLab/.venv 2>/dev/null; test -x /workspace/MotrixLab/.venv/bin/mxlab && echo HAS_MXLAB || echo NO_MXLAB")
    status = f"\n=== poll {i} ===\nPS:\n{ps}\nVENV:\n{venv}\nLOG:\n{log}\n"
    print(status)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(status)
    if "EXIT:" in log:
        print("INSTALL FINISHED")
        break
    if "HAS_MXLAB" in venv and not ps.strip():
        print("MXLAB READY")
        break
else:
    print("TIMEOUT")

_, final, _ = run("tail -n 80 /tmp/motrix_install.log; ls /workspace/MotrixLab/.venv/bin | head -40")
print(final)
OUT.write_text(OUT.read_text(encoding="utf-8") + "\nFINAL\n" + final, encoding="utf-8")
client.close()
