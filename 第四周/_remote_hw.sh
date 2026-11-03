#!/usr/bin/env bash
# Week-4 homework runner on cloud GPU
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd /root/work/MotrixLab

echo "=== sync deps ==="
# Prefer torch + skrl; use Chinese mirrors when needed
if [[ ! -f .venv/bin/python ]]; then
  # inject tuna index if missing
  if ! grep -q 'tuna' uv.toml 2>/dev/null; then
    cat >> uv.toml <<'EOF'

[[index]]
name = "mirror"
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
default = true
EOF
  fi
  uv sync --all-packages --extra skrl-torch --index-strategy unsafe-best-match
fi

mkdir -p /root/work/week4_artifacts/{logs,plots,videos,code_shots}
OUT=/root/work/week4_artifacts

run_train () {
  local env="$1"
  local seed="${2:-42}"
  local tag="${3:-}"
  echo "=== train $env seed=$seed $tag ==="
  uv run scripts/train.py --env="$env" --rllib=skrl --seed="$seed" --train-backend=torch 2>&1 | tee "$OUT/logs/train_${env}${tag:+_$tag}.log"
}

find_policy () {
  local env="$1"
  # newest best_agent under runs/<env>
  find "runs/$env" -type f \( -name 'best_agent.pt' -o -name 'best_agent.pickle' \) 2>/dev/null | sort | tail -1
}

# ----- A: cartpole / pendulum / acrobot -----
run_train cartpole 42
run_train pendulum 42 A
run_train acrobot 42

# ----- B: pendulum without energy reward -----
NP=motrix_envs/src/motrix_envs/basic/pendulum/pendulum_np.py
cp "$NP" "$OUT/code_shots/pendulum_np.py.A.bak"
# zero energy contribution
python - <<'PY'
from pathlib import Path
p = Path("motrix_envs/src/motrix_envs/basic/pendulum/pendulum_np.py")
t = p.read_text()
old = "3.0 * upright + energy_reward -"
new = "3.0 * upright + 0.0 * energy_reward -"
if old not in t:
    raise SystemExit("pattern not found for B-group edit")
p.write_text(t.replace(old, new, 1))
print("B-group edit ok")
PY
cp "$NP" "$OUT/code_shots/pendulum_np.py.B"
run_train pendulum 42 B
# restore A
cp "$OUT/code_shots/pendulum_np.py.A.bak" "$NP"

# ----- plot TB curves -----
uv run python - <<'PY'
import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

out = Path("/root/work/week4_artifacts/plots")
out.mkdir(parents=True, exist_ok=True)

def plot_reward(run_dir: Path, title: str, outfile: Path):
    # find event files recursively
    events = list(run_dir.rglob("events.out.tfevents.*"))
    if not events:
        print("no events in", run_dir)
        return
    # use newest parent that has scalars
    ea = EventAccumulator(str(events[-1].parent))
    ea.Reload()
    tags = ea.Tags().get("scalars", [])
    # pick a reward-like tag
    prefer = [t for t in tags if "reward" in t.lower() or "Reward" in t]
    if not prefer:
        prefer = tags[:1]
    if not prefer:
        print("no scalars", run_dir, tags)
        return
    tag = prefer[0]
    for t in prefer:
        if "mean" in t.lower() or "Instantaneous" in t or "Reward" in t:
            tag = t
            break
    sc = ea.Scalars(tag)
    xs = [s.step for s in sc]
    ys = [s.value for s in sc]
    plt.figure(figsize=(8, 4.5))
    plt.plot(xs, ys)
    plt.title(f"{title}\n{tag}")
    plt.xlabel("step")
    plt.ylabel(tag)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(outfile, dpi=140)
    plt.close()
    print("wrote", outfile, "n=", len(xs))

runs = Path("runs")
# cartpole / acrobot: latest skrl run
for env in ["cartpole", "acrobot"]:
    base = runs / env
    if not base.exists():
        continue
    # prefer skrl subdir
    cands = sorted(base.rglob("events.out.tfevents.*"), key=lambda p: p.stat().st_mtime)
    if cands:
        plot_reward(cands[-1].parent, env, out / f"{env}_reward.png")

# pendulum: two newest distinct run dirs (A then B by mtime)
pend = runs / "pendulum"
if pend.exists():
    event_files = sorted(pend.rglob("events.out.tfevents.*"), key=lambda p: p.stat().st_mtime)
    # unique parent dirs by mtime
    dirs = []
    seen = set()
    for e in event_files:
        d = e.parent
        key = str(d)
        if key in seen:
            continue
        seen.add(key)
        dirs.append(d)
    # last two
    if len(dirs) >= 1:
        plot_reward(dirs[-1] if len(dirs) == 1 else dirs[-2], "pendulum A (energy ON)", out / "pendulum_A_reward.png")
    if len(dirs) >= 2:
        plot_reward(dirs[-1], "pendulum B (energy OFF)", out / "pendulum_B_reward.png")

print("plot done")
PY

# ----- play episodes (headless) -----
# Capture terminal + try xvfb screenshots if available
apt-get update -qq && apt-get install -y -qq xvfb ffmpeg >/dev/null 2>&1 || true

play_one () {
  local env="$1"
  local seed="$2"
  local label="$3"
  local policy
  policy=$(find_policy "$env")
  if [[ -z "$policy" ]]; then
    echo "NO POLICY for $env"
    return 0
  fi
  echo "policy=$policy"
  echo "$policy" > "$OUT/logs/policy_${label}.txt"
  # short play; MotrixLab play loops — kill after ~25s
  timeout 25s xvfb-run -a uv run scripts/play.py --env="$env" --rllib=skrl --policy="$policy" --seed="$seed" --num-envs=1 \
    > "$OUT/logs/play_${label}_seed${seed}.log" 2>&1 || true
}

play_one cartpole 0 cartpole
play_one acrobot 0 acrobot

# pendulum A = older? we restored code; policies: find by log timestamps
# Use two newest pendulum policies
mapfile -t PENDS < <(find runs/pendulum -type f \( -name 'best_agent.pt' -o -name 'best_agent.pickle' \) 2>/dev/null | xargs -r ls -1t)
if [[ ${#PENDS[@]} -ge 1 ]]; then
  echo "${PENDS[-1]:-${PENDS[0]}}" > "$OUT/logs/policy_pendulum_A.txt" || true
fi
# A is earlier, B is later when sorted by time
if [[ ${#PENDS[@]} -ge 2 ]]; then
  A_POL="${PENDS[1]}"  # second newest = A if B is newest
  B_POL="${PENDS[0]}"
else
  A_POL="${PENDS[0]:-}"
  B_POL="${PENDS[0]:-}"
fi
echo "A_POL=$A_POL"
echo "B_POL=$B_POL"
echo "$A_POL" > "$OUT/logs/policy_pendulum_A.txt"
echo "$B_POL" > "$OUT/logs/policy_pendulum_B.txt"

for seed in 0 1 2; do
  timeout 25s xvfb-run -a uv run scripts/play.py --env=pendulum --rllib=skrl --policy="$A_POL" --seed="$seed" --num-envs=1 \
    > "$OUT/logs/play_pendulum_A_seed${seed}.log" 2>&1 || true
  timeout 25s xvfb-run -a uv run scripts/play.py --env=pendulum --rllib=skrl --policy="$B_POL" --seed="$seed" --num-envs=1 \
    > "$OUT/logs/play_pendulum_B_seed${seed}.log" 2>&1 || true
done

# view dm-reacher screenshot via xvfb + import if available
apt-get install -y -qq imagemagick >/dev/null 2>&1 || true
timeout 15s xvfb-run -a bash -c 'uv run scripts/view.py --env=dm-reacher & sleep 8; import -window root /root/work/week4_artifacts/plots/dm_reacher_view.png' \
  > "$OUT/logs/view_reacher.log" 2>&1 || true

# save code excerpts as text for screenshots later
sed -n '70,100p' motrix_envs/src/motrix_envs/basic/pendulum/pendulum_np.py > "$OUT/code_shots/pendulum_reward_A.txt"
sed -n '60,90p' motrix_envs/src/motrix_envs/basic/reacher/reacher_np.py > "$OUT/code_shots/reacher_obs_action_reward.txt"
sed -n '45,55p' motrix_envs/src/motrix_envs/basic/acrobot/acrobot.xml > "$OUT/code_shots/acrobot_actuator.xml.txt"

# summary
echo "=== SUMMARY ===" | tee "$OUT/SUMMARY.txt"
find runs -name 'best_agent.*' | tee -a "$OUT/SUMMARY.txt"
ls -la "$OUT/plots" | tee -a "$OUT/SUMMARY.txt"
ls -la "$OUT/logs" | tee -a "$OUT/SUMMARY.txt"
echo DONE
