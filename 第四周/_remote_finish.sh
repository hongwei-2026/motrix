#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd /root/work/MotrixLab
OUT=/root/work/week4_artifacts
mkdir -p "$OUT"/{logs,plots,videos,code_shots}

# ensure A reward restored
if grep -q '0.0 \* energy_reward' motrix_envs/src/motrix_envs/basic/pendulum/pendulum_np.py; then
  if [[ -f "$OUT/code_shots/pendulum_np.py.A.bak" ]]; then
    cp "$OUT/code_shots/pendulum_np.py.A.bak" motrix_envs/src/motrix_envs/basic/pendulum/pendulum_np.py
    echo restored A reward
  else
    sed -i 's/3.0 \* upright + 0.0 \* energy_reward -/3.0 * upright + energy_reward -/' motrix_envs/src/motrix_envs/basic/pendulum/pendulum_np.py
    echo sed restored A
  fi
fi

uv pip install matplotlib tensorboard
apt-get update -qq
apt-get install -y -qq xvfb ffmpeg imagemagick >/dev/null

# plot curves
uv run python <<'PY'
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

out = Path("/root/work/week4_artifacts/plots")
out.mkdir(parents=True, exist_ok=True)

def pick_tag(tags):
    prefer = [t for t in tags if "reward" in t.lower()]
    if not prefer:
        return tags[0] if tags else None
    for t in prefer:
        if "mean" in t.lower() or "Instantaneous" in t:
            return t
    return prefer[0]

def plot_dir(run_dir: Path, title: str, outfile: Path):
    events = sorted(run_dir.rglob("events.out.tfevents.*"), key=lambda p: p.stat().st_mtime)
    if not events:
        print("no events", run_dir)
        return
    ea = EventAccumulator(str(events[-1].parent))
    ea.Reload()
    tags = ea.Tags().get("scalars", [])
    tag = pick_tag(tags)
    if not tag:
        print("no scalars", run_dir)
        return
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
    print("wrote", outfile, "n=", len(xs), "tag=", tag)

runs = Path("runs")
for env in ["cartpole", "acrobot"]:
    base = runs / env
    if base.exists():
        plot_dir(base, env, out / f"{env}_reward.png")

pend = runs / "pendulum"
if pend.exists():
    # collect unique event parents sorted by mtime
    dirs = []
    seen = set()
    for e in sorted(pend.rglob("events.out.tfevents.*"), key=lambda p: p.stat().st_mtime):
        # go up to run folder (parent of events often is Tensorboard or similar)
        d = e.parent
        key = str(d)
        if key in seen:
            continue
        seen.add(key)
        dirs.append(d)
    print("pendulum event dirs:", dirs)
    if len(dirs) >= 2:
        plot_dir(dirs[-2], "pendulum A (energy ON)", out / "pendulum_A_reward.png")
        plot_dir(dirs[-1], "pendulum B (energy OFF)", out / "pendulum_B_reward.png")
    elif len(dirs) == 1:
        plot_dir(dirs[0], "pendulum", out / "pendulum_A_reward.png")
print("plots done")
PY

find_policy () {
  find "runs/$1" -type f \( -name 'best_agent.pt' -o -name 'best_agent.pickle' \) 2>/dev/null | xargs -r ls -1t | head -1
}

# list all pendulum policies by time
mapfile -t PENDS < <(find runs/pendulum -type f \( -name 'best_agent.pt' -o -name 'best_agent.pickle' \) 2>/dev/null | xargs -r ls -1t)
echo "pendulum policies:"; printf '%s\n' "${PENDS[@]:-}"
if [[ ${#PENDS[@]} -ge 2 ]]; then
  B_POL="${PENDS[0]}"
  A_POL="${PENDS[1]}"
else
  A_POL="${PENDS[0]:-}"
  B_POL="${PENDS[0]:-}"
fi
echo "$A_POL" | tee "$OUT/logs/policy_pendulum_A.txt"
echo "$B_POL" | tee "$OUT/logs/policy_pendulum_B.txt"
CPOL=$(find_policy cartpole); echo "$CPOL" | tee "$OUT/logs/policy_cartpole.txt"
APOL=$(find_policy acrobot); echo "$APOL" | tee "$OUT/logs/policy_acrobot.txt"

play () {
  local env="$1" pol="$2" seed="$3" label="$4"
  [[ -z "$pol" || ! -f "$pol" ]] && { echo "skip $label"; return 0; }
  timeout 30s xvfb-run -a uv run scripts/play.py --env="$env" --rllib=skrl --policy="$pol" --seed="$seed" --num-envs=1 \
    > "$OUT/logs/play_${label}_seed${seed}.log" 2>&1 || true
  echo "played $label seed=$seed"
}

play cartpole "$CPOL" 0 cartpole
play acrobot "$APOL" 0 acrobot
for s in 0 1 2; do
  play pendulum "$A_POL" "$s" pendulum_A
  play pendulum "$B_POL" "$s" pendulum_B
done

# dm-reacher view screenshot
timeout 20s xvfb-run -a bash -c 'uv run scripts/view.py --env=dm-reacher >/tmp/view.log 2>&1 & VP=$!; sleep 10; import -window root /root/work/week4_artifacts/plots/dm_reacher_view.png || true; kill $VP 2>/dev/null' || true

# code excerpts
sed -n '70,100p' motrix_envs/src/motrix_envs/basic/pendulum/pendulum_np.py > "$OUT/code_shots/pendulum_reward_A.txt"
sed -n '60,90p' motrix_envs/src/motrix_envs/basic/reacher/reacher_np.py > "$OUT/code_shots/reacher_key.txt"
grep -A5 '<actuator>' motrix_envs/src/motrix_envs/basic/acrobot/acrobot.xml > "$OUT/code_shots/acrobot_actuator.txt" || true
# B version from backup
if [[ -f "$OUT/code_shots/pendulum_np.py.B" ]]; then
  grep -n 'energy_reward\|upright' "$OUT/code_shots/pendulum_np.py.B" | head -20 > "$OUT/code_shots/pendulum_B_lines.txt"
fi

# pack tar
cd /root/work
tar czf week4_artifacts.tar.gz week4_artifacts MotrixLab/runs/cartpole MotrixLab/runs/pendulum MotrixLab/runs/acrobot 2>/dev/null || tar czf week4_artifacts.tar.gz week4_artifacts
ls -lh /root/work/week4_artifacts.tar.gz
ls -la "$OUT/plots"
ls -la "$OUT/logs"
echo FINISH_DONE
