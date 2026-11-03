import os
# -*- coding: utf-8 -*-
"""Train cartpole briefly and collect lecture-7 evidence."""
import paramiko
import time
from pathlib import Path

HOST = "39.145.28.59"
PORT = 32222
USER = "root+vm-LEAjLhYIUQymN0v7"
PASSWORD = os.environ.get("MOTRIX_SSH_PASS", "")
LOCAL = Path(r"D:\motrix\第7讲")
EVIDENCE = LOCAL / "证据"
EVIDENCE.mkdir(parents=True, exist_ok=True)
LOG = LOCAL / "_train_log.txt"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, PORT, USER, PASSWORD, timeout=30, allow_agent=False, look_for_keys=False)


def run(cmd, timeout=120):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode("utf-8", "replace")
    err = e.read().decode("utf-8", "replace")
    code = o.channel.recv_exit_status()
    return code, out, err


def log(msg):
    print(msg.encode("ascii", "replace").decode("ascii"))
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


LOG.write_text("", encoding="utf-8")

# verify env
code, out, err = run(
    "export PATH=$HOME/.local/bin:$PATH; "
    "cd /workspace/MotrixLab && "
    ".venv/bin/python -c \"import torch, motrix_envs, motrix_rl, motrixsim; print('torch', torch.__version__, 'cuda', torch.cuda.is_available()); print('ok')\""
)
log(f"import check code={code}\n{out}\n{err}")

# find cartpole timesteps config and patch to short run if needed
code, out, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; "
    "cd /workspace/MotrixLab && "
    "rg -n 'timesteps|max_env_steps|CartPole' motrix_rl -g '*.py' | head -40"
)
log("config hits:\n" + out)

# Start training in background with fewer envs; default cartpole is 5000 timesteps
run("pkill -f 'scripts/train.py' || true")
_, pid, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; "
    "cd /workspace/MotrixLab && "
    "rm -f /tmp/cartpole_train.log; "
    "nohup bash -lc '"
    "export PATH=$HOME/.local/bin:$PATH; "
    "cd /workspace/MotrixLab && "
    "uv run scripts/train.py --env cartpole --num-envs 256 --train-backend torch "
    "> /tmp/cartpole_train.log 2>&1; "
    "echo TRAIN_EXIT:$? >> /tmp/cartpole_train.log"
    "' >/dev/null 2>&1 & echo $!"
)
log(f"train pid={pid.strip()}")

for i in range(180):
    time.sleep(15)
    _, logtxt, _ = run("tail -c 2500 /tmp/cartpole_train.log 2>/dev/null || echo NOLOG")
    _, ps, _ = run("ps aux | grep 'scripts/train.py' | grep -v grep || true")
    _, runs, _ = run("ls -la /workspace/MotrixLab/runs/cartpole 2>/dev/null; find /workspace/MotrixLab/runs/cartpole -maxdepth 4 -type f 2>/dev/null | head -40")
    msg = f"=== poll {i} ===\nRUNS:\n{runs}\nPS:\n{ps}\nLOG:\n{logtxt}\n"
    log(msg)
    if "TRAIN_EXIT:0" in logtxt:
        log("TRAIN SUCCESS")
        break
    if "TRAIN_EXIT:" in logtxt:
        log("TRAIN FAILED")
        break
else:
    log("TRAIN TIMEOUT")

# capture directory listing
code, out, _ = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "find runs/cartpole -maxdepth 5 -print | head -80; echo '----'; "
    "find runs/cartpole -type f \\( -name 'events.out.tfevents*' -o -name '*.pt' -o -name '*.pickle' -o -name 'best_agent*' \\) | head -40"
)
(EVIDENCE / "01_runs_tree.txt").write_text(out, encoding="utf-8")
log("runs tree saved")

# find checkpoint
_, ckpt, _ = run(
    "cd /workspace/MotrixLab && "
    "python3 - <<'PY'\n"
    "from pathlib import Path\n"
    "root=Path('runs/cartpole')\n"
    "cands=[]\n"
    "for p in root.rglob('*'):\n"
    "  if p.is_file() and (p.name.startswith('best_agent') or p.suffix in {'.pt','.pickle'} and 'checkpoint' in str(p).lower() or p.name.startswith('agent_')):\n"
    "    cands.append(p)\n"
    "  if p.is_file() and p.name.startswith('best_agent'):\n"
    "    cands.append(p)\n"
    "cands=sorted(set(cands), key=lambda x: x.stat().st_mtime, reverse=True)\n"
    "print('\\n'.join(str(x) for x in cands[:20]))\n"
    "PY"
)
log("checkpoints:\n" + ckpt)
(EVIDENCE / "02_checkpoints.txt").write_text(ckpt, encoding="utf-8")

ckpt_path = None
for line in ckpt.splitlines():
    line = line.strip()
    if line and not line.startswith("Traceback"):
        ckpt_path = line
        break

# TensorBoard export via python (no browser)
tb_script = r'''
from pathlib import Path
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import json
root = Path("runs/cartpole")
events = sorted(root.rglob("events.out.tfevents*"), key=lambda p: p.stat().st_mtime, reverse=True)
print("EVENT_FILES", len(events))
summary = {}
for ev in events[:3]:
    ea = EventAccumulator(str(ev.parent), size_guidance={"scalars": 0})
    ea.Reload()
    tags = ea.Tags().get("scalars", [])
    print("DIR", ev.parent)
    print("TAGS", tags[:30])
    picked = {}
    for t in tags:
        low = t.lower()
        if any(k in low for k in ["reward", "return", "loss", "episode"]):
            sc = ea.Scalars(t)
            if sc:
                picked[t] = {"first": sc[0].value, "last": sc[-1].value, "n": len(sc)}
    summary[str(ev.parent)] = picked
    print("PICKED", json.dumps(picked, ensure_ascii=False))
Path("/tmp/tb_summary.json").write_text(json.dumps(summary, indent=2), ensure_ascii=False)
'''
sftp = c.open_sftp()
with sftp.file("/tmp/tb_export.py", "w") as f:
    f.write(tb_script)
sftp.close()

code, out, err = run(
    "export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
    "uv run python /tmp/tb_export.py"
)
(EVIDENCE / "03_tensorboard_summary.txt").write_text(out + "\n" + err, encoding="utf-8")
log(f"tb export code={code}\n{out}\n{err}")

# play
if ckpt_path:
    # detect rllib from path
    rllib = "skrl"
    if "/rslrl/" in ckpt_path.replace("\\", "/"):
        rllib = "rslrl"
    play_cmd = (
        f"export PATH=$HOME/.local/bin:$PATH; cd /workspace/MotrixLab && "
        f"uv run scripts/play.py --env cartpole --rllib {rllib} --policy {ckpt_path} --num-envs 1 "
        f"> /tmp/cartpole_play.log 2>&1; echo PLAY_EXIT:$? >> /tmp/cartpole_play.log"
    )
    # play may block on render; run with timeout and kill
    _, pid, _ = run(
        "rm -f /tmp/cartpole_play.log; "
        "nohup bash -lc '" + play_cmd.replace("'", "'\\''") + "' >/dev/null 2>&1 & echo $!"
    )
    log(f"play pid={pid.strip()} cmd={play_cmd}")
    time.sleep(25)
    _, plog, _ = run("tail -c 4000 /tmp/cartpole_play.log 2>/dev/null || echo NOLOG")
    (EVIDENCE / "04_play_log.txt").write_text(plog, encoding="utf-8")
    log("play log:\n" + plog)
    # kill play if still running (headless render may hang)
    run("pkill -f 'scripts/play.py' || true")
else:
    log("NO CHECKPOINT FOUND")

# directory screenshot substitute: detailed listing
code, out, _ = run(
    "cd /workspace/MotrixLab && "
    "python3 - <<'PY'\n"
    "from pathlib import Path\n"
    "root=Path('runs/cartpole')\n"
    "print('=== runs/cartpole tree ===')\n"
    "if not root.exists():\n"
    "  print('MISSING'); raise SystemExit\n"
    "for p in sorted(root.rglob('*')):\n"
    "  rel=p.relative_to(root)\n"
    "  if p.is_dir():\n"
    "    print(f'[D] {rel}/')\n"
    "  else:\n"
    "    print(f'[F] {rel}  ({p.stat().st_size} bytes)')\n"
    "PY"
)
(EVIDENCE / "01_runs_tree_detailed.txt").write_text(out, encoding="utf-8")
log(out)

c.close()
print("DONE")
