import paramiko
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "connect.cqa1.seetacloud.com",
    port=31748,
    username="root",
    password="IBH0VOb08eXI",
    timeout=60,
    banner_timeout=60,
    auth_timeout=60,
)


def r(cmd, t=300):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


print(r("pkill -f 'scripts/train.py' || true; pkill -f '_long_play' || true; pkill -f '_kit_zf' || true; sleep 2; echo CLEARED"))

sftp = c.open_sftp()
local = Path(r"D:\motrix\_w8\_inject_waypoints.py")
with sftp.file("/tmp/_inject_waypoints.py", "w") as f:
    f.write(local.read_text(encoding="utf-8"))
# also ensure dim67 boost base exists
sftp.close()

print("=== inject ===")
print(r("cd /root/autodl-tmp/MotrixLab && .venv/bin/python /tmp/_inject_waypoints.py"))

sh = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/root/miniconda3/envs/motrix/bin:/root/.local/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
OUT=/root/autodl-tmp/evidence_w8
cd /root/autodl-tmp/MotrixLab
source /root/miniconda3/etc/profile.d/conda.sh
conda activate motrix
source .venv/bin/activate
exec > >(tee "$OUT/train_waypoint.log") 2>&1
set -eux
# bump train horizon
python - <<'PY'
from pathlib import Path
import re
pp = Path("motrix_rl/src/motrix_rl/cfgs.py")
t = pp.read_text(encoding="utf-8")
t2 = re.sub(
    r"(class VBotNavigationSection01PPOConfig\(PPOCfg\):.*?max_env_steps: int = )[^\n]+",
    r"\g<1>8000000",
    t,
    count=1,
    flags=re.S,
)
t2 = re.sub(
    r"(class VBotNavigationSection01PPOConfig\(PPOCfg\):.*?check_point_interval: int = )\d+",
    r"\g<1>500",
    t2,
    count=1,
    flags=re.S,
)
pp.write_text(t2, encoding="utf-8")
print("PPO_CFG_OK")
PY
.venv/bin/python scripts/train.py --env=vbot_navigation_section01 --num-envs=1024 --train-backend=jax
echo TRAIN_WAYPOINT_DONE
'''
sftp = c.open_sftp()
with sftp.file("/tmp/_train_waypoint.sh", "w") as f:
    f.write(sh)
sftp.close()
print(r("chmod +x /tmp/_train_waypoint.sh; nohup bash /tmp/_train_waypoint.sh >/root/autodl-tmp/evidence_w8/wp_nohup.out 2>&1 & echo PID=$!"))
c.close()
