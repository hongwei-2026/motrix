#!/usr/bin/env python3
"""SSH helper for cloud VM homework runs."""
from __future__ import annotations

import argparse
import sys
import time

import paramiko

HOST = "223.72.199.245"
PORT = 32222
USER = "root+vm-gWWaKumLC2l4FJhf"
PWD = "***REDACTED***"


def connect() -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        HOST,
        port=PORT,
        username=USER,
        password=PWD,
        timeout=45,
        allow_agent=False,
        look_for_keys=False,
        banner_timeout=60,
    )
    return c


def run(c: paramiko.SSHClient, cmd: str, timeout: int = 120) -> tuple[int, str, str]:
    print(f"\n$ {cmd}", flush=True)
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    if out:
        print(out, end="" if out.endswith("\n") else "\n")
    if err.strip():
        print(err, file=sys.stderr)
    print(f"[exit {code}]", flush=True)
    return code, out, err


def run_stream(c: paramiko.SSHClient, cmd: str, timeout: int = 3600) -> int:
    print(f"\n$ {cmd}", flush=True)
    transport = c.get_transport()
    assert transport is not None
    chan = transport.open_session()
    chan.get_pty(width=160, height=40)
    chan.settimeout(timeout)
    chan.exec_command(cmd)
    deadline = time.time() + timeout
    buf = b""
    while True:
        if chan.recv_ready():
            data = chan.recv(4096)
            if not data:
                break
            sys.stdout.write(data.decode(errors="replace"))
            sys.stdout.flush()
            buf += data
        if chan.exit_status_ready():
            # drain
            while chan.recv_ready():
                data = chan.recv(4096)
                sys.stdout.write(data.decode(errors="replace"))
                sys.stdout.flush()
            break
        if time.time() > deadline:
            chan.close()
            print("\n[TIMEOUT]", flush=True)
            return -1
        time.sleep(0.2)
    code = chan.recv_exit_status()
    print(f"\n[exit {code}]", flush=True)
    return code


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", nargs="?", default=None, help="remote shell command")
    p.add_argument("--stream", action="store_true")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--probe", action="store_true")
    args = p.parse_args()

    c = connect()
    try:
        if args.probe:
            for cmd in [
                "whoami; hostname; pwd",
                "ls -la /home/ubuntu",
                "ls -la /home/ubuntu/Desktop 2>/dev/null || true",
                "find /home/ubuntu -maxdepth 6 -type d -iname '*motrix*' 2>/dev/null | head -20",
                "find / -maxdepth 4 -type d -name MotrixLab 2>/dev/null | head -20",
                "python3 --version; which uv || true; ls /home/ubuntu/.local/bin 2>/dev/null || true",
                "nvidia-smi -L 2>/dev/null || true",
            ]:
                run(c, cmd, timeout=90)
            return 0

        if not args.cmd:
            print("need cmd or --probe", file=sys.stderr)
            return 2

        if args.stream:
            return run_stream(c, args.cmd, timeout=args.timeout)
        code, _, _ = run(c, args.cmd, timeout=args.timeout)
        return code
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())
