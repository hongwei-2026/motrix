import os
# -*- coding: utf-8 -*-
import paramiko
import socket

HOST = "39.145.28.59"
PORT = 32222
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")
USERS = [
    "root+vm-LEAjLhYIUQymN0v7",
    "root",
    "vm-LEAjLhYIUQymN0v7",
]

# first check port open
s = socket.create_connection((HOST, PORT), timeout=10)
banner = s.recv(256)
print("banner:", banner)
s.close()

for user in USERS:
    print(f"\n=== try user={user!r} password auth ===")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            HOST,
            port=PORT,
            username=user,
            password=PASSWORD,
            timeout=30,
            allow_agent=False,
            look_for_keys=False,
            banner_timeout=30,
            auth_timeout=30,
        )
        print("OK password auth")
        stdin, stdout, stderr = client.exec_command("whoami; pwd; hostname")
        print(stdout.read().decode())
        print(stderr.read().decode())
        client.close()
        break
    except Exception as e:
        print("FAIL:", type(e).__name__, e)

    print(f"=== try user={user!r} keyboard-interactive ===")
    try:
        transport = paramiko.Transport((HOST, PORT))
        transport.connect()

        def handler(title, instructions, prompt_list):
            print("ki prompts:", prompt_list)
            return [PASSWORD for _ in prompt_list]

        transport.auth_interactive(user, handler)
        print("OK keyboard-interactive")
        chan = transport.open_session()
        chan.exec_command("whoami; pwd; hostname")
        out = b""
        while True:
            if chan.recv_ready():
                out += chan.recv(4096)
            if chan.exit_status_ready() and not chan.recv_ready():
                break
        print(out.decode())
        transport.close()
        break
    except Exception as e:
        print("FAIL:", type(e).__name__, e)
