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
    timeout=60,
    banner_timeout=60,
    auth_timeout=60,
)


def r(cmd, t=1200):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


sh = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/root/.local/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
OUT=/root/autodl-tmp/evidence_w8
LAB=/root/autodl-tmp/MotrixLab
cd "$LAB"
exec > >(tee -a "$OUT/finish_known.log") 2>&1
set -eux

# ensure known env deployed
cp -f "$OUT/known_policy/vbot_section01_np.py" motrix_envs/src/motrix_envs/navigation/vbot/vbot_section01_np.py
cp -f "$OUT/known_policy/cfg.py" motrix_envs/src/motrix_envs/navigation/vbot/cfg.py
mkdir -p runs/vbot_navigation_section01/known_success_PPO/checkpoints
cp -f "$OUT/known_policy/best_agent.pt" runs/vbot_navigation_section01/known_success_PPO/checkpoints/best_agent.pt

# Install torch via uv into project venv
if ! .venv/bin/python -c "import torch" 2>/dev/null; then
  # ensure pip
  .venv/bin/python -m ensurepip --upgrade || true
  uv pip install --python .venv/bin/python torch --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    || uv pip install --python .venv/bin/python torch
fi
.venv/bin/python -c "import torch; print('TORCH', torch.__version__, torch.cuda.is_available())"

# skrl torch side may need nothing extra if torch present
.venv/bin/python /tmp/_known_play_only.py
echo UV_TORCH_PLAY_DONE
'''
sftp = c.open_sftp()
with sftp.file("/tmp/_uv_torch_play.sh", "w") as f:
    f.write(sh)
sftp.close()
print(r("chmod +x /tmp/_uv_torch_play.sh; nohup bash /tmp/_uv_torch_play.sh >/root/autodl-tmp/evidence_w8/uv_torch_nohup.out 2>&1 & echo PID=$!"))
c.close()
