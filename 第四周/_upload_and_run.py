#!/usr/bin/env python3
import sys
from pathlib import Path

import paramiko

HOST, PORT = "223.72.199.245", 32222
USER = "root+vm-gWWaKumLC2l4FJhf"
PWD = "***REDACTED***"


def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=45, allow_agent=False, look_for_keys=False)
    return c


def upload(local: Path, remote: str, mode: int = 0o755):
    c = connect()
    sftp = c.open_sftp()
    text = local.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    with sftp.file(remote, "w") as f:
        f.write(text)
    sftp.chmod(remote, mode)
    sftp.close()
    c.close()
    print("uploaded", remote)


def run(cmd: str, timeout: int = 600):
    c = connect()
    print("$", cmd)
    i, o, e = c.exec_command(cmd, timeout=timeout, get_pty=True)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    print(out[-8000:] if len(out) > 8000 else out)
    if err.strip():
        print(err[-2000:], file=sys.stderr)
    print("[exit", code, "]")
    c.close()
    return code


def download(remote: str, local: Path):
    local.parent.mkdir(parents=True, exist_ok=True)
    c = connect()
    sftp = c.open_sftp()
    sftp.get(remote, str(local))
    sftp.close()
    c.close()
    print("downloaded", local, local.stat().st_size)


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "upload":
        upload(Path(sys.argv[2]), sys.argv[3])
    elif action == "run":
        run(sys.argv[2], timeout=int(sys.argv[3]) if len(sys.argv) > 3 else 600)
    elif action == "get":
        download(sys.argv[2], Path(sys.argv[3]))
    else:
        raise SystemExit("upload|run|get")
