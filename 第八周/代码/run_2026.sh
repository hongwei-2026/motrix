#!/usr/bin/env bash
# Replay the existing LM checkpoint on its original simulator, without terrain edits.
set -euo pipefail
task_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="${MOTRIX_REPO:-/root/autodl-tmp/MotrixLab}"
python_bin="${MOTRIX_PYTHON:-/root/miniconda3/bin/python}"
runtime_dir="$task_dir/runtime050b2"
wheel="$task_dir/motrixsim-0.5.0b2-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
runner="$task_dir/rollout.py"
if [[ ! -f "$runner" ]]; then runner="$task_dir/section01_rollout.py"; fi
if [[ ! -f "$runtime_dir/motrixsim/__init__.py" ]]; then
    if [[ -f "$wheel" ]]; then
        "$python_bin" -m pip install --no-deps --no-index --target "$runtime_dir" "$wheel"
    else
        "$python_bin" -m pip install --no-deps --index-url https://pypi.org/simple \
            --target "$runtime_dir" motrixsim==0.5.0b2
    fi
fi
export PYTHONPATH="$runtime_dir:$repo_dir/motrix_envs/src:$repo_dir/motrix_rl/src:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
"$python_bin" - <<'PY'
import importlib.metadata as md
version = md.version('motrixsim')
assert version == '0.5.0b2', f'Expected motrixsim 0.5.0b2, got {version}'
print('MOTRIXSIM_VERSION=' + version, flush=True)
PY
result="$task_dir/latest_result.json"
"$python_bin" -u "$runner" --root "$repo_dir" --steps 8000 --seed 42 \
    --final-threshold 0.1 --goal-hold-steps 200 --run-full --output "$result" "$@"
"$python_bin" - "$result" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
last = d['final_pose'][0]
gz = d['final_gz'][0]
on_platform = -3.7 < last[0] < -1.7 and 7.8 <= last[1] <= 8.6 and 1.45 < last[2] < 2.15 and gz < -0.8
passed = d['REACH_2026'] and d['flips'][0] == 0 and d['resets'][0] == 0 and on_platform
print('REACH_2026=' + str(d['REACH_2026']))
print('FLIPPED_STEPS=' + str(d['flips'][0]))
print('FALL_RESETS=' + str(d['resets'][0]))
print('FINAL_POSITION=' + str(last[:3]))
print('FINAL_UPRIGHT_GZ=' + str(gz))
print('ACCEPTANCE_PASS=' + str(passed))
sys.exit(0 if passed else 1)
PY
