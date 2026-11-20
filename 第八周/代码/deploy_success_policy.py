"""Deploy known-working waypoint env + best_agent.pt; play to 2026 for homework."""
import paramiko
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "connect.cqa1.seetacloud.com",
    port=31748,
    username="root",
    password="IBH0VOb08eXI",
    timeout=90,
    banner_timeout=90,
    auth_timeout=90,
)


def r(cmd, t=600):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


print("=== vbot_0218 readme ===")
print(r("head -80 /root/autodl-tmp/nav2/navigation2/navigation/vbot_0218/ReadMe.md"))

print("=== torch? ===")
print(
    r(
        "/root/autodl-tmp/MotrixLab/.venv/bin/python -c 'import torch; print(torch.__version__, torch.cuda.is_available())' 2>&1 | tail -5"
    )
)

print("=== play policy load snippet ===")
print(r("sed -n '40,120p' /root/autodl-tmp/MotrixLab/scripts/play.py"))

c.close()
