"""After current kit eval, retry kit with foot forces zeroed (obs still 67)."""
import paramiko
import sys
import time

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


def r(cmd, t=120):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


script = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/root/miniconda3/envs/motrix/bin:/root/.local/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
OUT=/root/autodl-tmp/evidence_w8
cd /root/autodl-tmp/MotrixLab
source /root/miniconda3/etc/profile.d/conda.sh
conda activate motrix
source .venv/bin/activate
exec > >(tee "$OUT/kit_zeroforce.log") 2>&1
set -eux

# Wait until kit_pipeline finished (or kill stuck evals after timeout handled outside)
while pgrep -f '_kit_pipeline.sh' >/dev/null; do
  echo "waiting kit_pipeline..."; sleep 30
done
# kill leftover long_play if any
pkill -f '_long_play_autodl.py' || true
sleep 2

# Monkeypatch: zero foot forces in get method via sitecustomize-like inject in long play env
python - <<'PY'
from pathlib import Path
p = Path("motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py")
t = p.read_text(encoding="utf-8")
bak = Path("/root/autodl-tmp/evidence_w8/vbot_section01_np.py.before_zeroforce")
if not bak.exists():
    bak.write_text(t, encoding="utf-8")

# Force _get_foot_contact_force to return zeros (keep 67-dim layout kit expects)
needle = "def _get_foot_contact_force(self, data: mtx.SceneData, root_quat: np.ndarray) -> np.ndarray:"
if "ZERO_FORCE_FOR_KIT" not in t:
    # insert early return after docstring/first line of body
    idx = t.find(needle)
    assert idx > 0
    # find end of def line and insert
    nl = t.find("\n", idx)
    # skip possible docstring
    rest = t[nl+1:]
    insert = "\n        # ZERO_FORCE_FOR_KIT\n        num_envs = data.shape[0]\n        return np.zeros((num_envs, 12), dtype=np.float32)\n"
    # find first real indent line of function body after docstring
    # simpler: replace function start with early return version marker after def
    t2 = t[:nl+1] + insert + t[nl+1:]
    p.write_text(t2, encoding="utf-8")
    print("ZERO_FORCE_PATCHED")
else:
    print("ALREADY_ZERO")
PY

export PLAY_POLICY=runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints/best_agent.pickle
export PLAY_STEPS=25000
python /tmp/_long_play_autodl.py
cp -f "$OUT/rollout_xy_long.csv" "$OUT/rollout_kit_zeroforce.csv" || true
cp -f "$OUT/play_2026.mp4" "$OUT/play_kit_zeroforce.mp4" || true
grep -E 'max_y|LONG_PLAY|REACH' "$OUT/kit_zeroforce.log" | tail -20 || true

# Also try agent_10000
export PLAY_POLICY=runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints/agent_10000.pickle
python /tmp/_long_play_autodl.py 2>&1 | tee -a "$OUT/kit_zeroforce.log"
cp -f "$OUT/rollout_xy_long.csv" "$OUT/rollout_kit10000_zf.csv" || true
grep -E 'max_y|LONG_PLAY|REACH' "$OUT/kit_zeroforce.log" | tail -30 || true

# Restore real forces from bak for continued training
cp -f /root/autodl-tmp/evidence_w8/vbot_section01_np.py.before_zeroforce \
  motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py
# re-apply reward boost if needed — bak is pre-zeroforce which should still have boost
echo RESTORED_ENV
grep -n 'y_progress = np.clip' motrix_envs/src/motrix_envs/locomotion/vbot/vbot_section01_np.py | head

echo ZERO_FORCE_PIPELINE_DONE
'''

sftp = c.open_sftp()
with sftp.file("/tmp/_kit_zeroforce.sh", "w") as f:
    f.write(script)
sftp.close()
print(r("chmod +x /tmp/_kit_zeroforce.sh; nohup bash /tmp/_kit_zeroforce.sh >/root/autodl-tmp/evidence_w8/kit_zf_nohup.out 2>&1 & echo ZF_PID=$!"))
c.close()
