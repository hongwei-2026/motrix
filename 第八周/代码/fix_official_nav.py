"""Redeploy official navigation package from vbot_0218 and play kit policy."""
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


print("=== find zips ===")
print(
    r(
        "find /root/autodl-tmp/nav2 /root/autodl-tmp/starter_kit -type f \\( -name '*.zip' -o -name '*navigation*' \\) 2>/dev/null | head -60; "
        "ls -la /root/autodl-tmp/nav2/navigation2/navigation/vbot_0218/"
    )
)

sh = r'''#!/bin/bash
export PATH=/root/autodl-tmp/MotrixLab/.venv/bin:/root/miniconda3/envs/motrix/bin:/root/.local/bin:/usr/bin:/bin
export PYTHONUNBUFFERED=1
OUT=/root/autodl-tmp/evidence_w8
ROOT=/root/autodl-tmp
LAB=$ROOT/MotrixLab
cd "$LAB"
source /root/miniconda3/etc/profile.d/conda.sh
conda activate motrix
source .venv/bin/activate
exec > >(tee "$OUT/official_play.log") 2>&1
set -eux

VBOT=/root/autodl-tmp/nav2/navigation2/navigation/vbot_0218
ls -la "$VBOT"

# Prefer official navigation zip
NAV_ZIP=""
for z in "$VBOT"/vbot_navigation.zip "$VBOT"/*navigation*.zip "$VBOT"/*.zip; do
  if [ -f "$z" ]; then echo "CAND $z"; NAV_ZIP="$z"; fi
done
# nested
find "$VBOT" -name '*.zip' | tee "$OUT/vbot0218_zips.txt"

# unpack navigation into motrix_envs if zip found
python - <<'PY'
import zipfile, os, shutil
from pathlib import Path
vbot = Path("/root/autodl-tmp/nav2/navigation2/navigation/vbot_0218")
lab = Path("/root/autodl-tmp/MotrixLab")
envs = lab / "motrix_envs/src/motrix_envs"
out = Path("/root/autodl-tmp/evidence_w8")

zips = list(vbot.rglob("*.zip"))
print("zips", zips)
nav_zip = None
runs_zip = None
for z in zips:
    name = z.name.lower()
    if "run" in name:
        runs_zip = z
    if "navigation" in name or "vbot_navigation" in name or name == "navigation_vbot.zip":
        nav_zip = z
# also check common names
for cand in ["vbot_navigation.zip", "navigation_vbot.zip", "navigation.zip"]:
    p = vbot / cand
    if p.exists():
        nav_zip = p

print("nav_zip", nav_zip, "runs_zip", runs_zip)

# Inspect zip contents without full extract first
def list_zip(z, n=40):
    if not z: return
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        print(z.name, "count", len(names))
        for x in names[:n]:
            print(" ", x)

list_zip(nav_zip)
list_zip(runs_zip)

# Extract navigation package
if nav_zip:
    tmp = out / "_nav_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    with zipfile.ZipFile(nav_zip) as zf:
        zf.extractall(tmp)
    # find navigation folder
    nav_dirs = list(tmp.rglob("navigation"))
    nav_dirs = [d for d in nav_dirs if d.is_dir() and (d / "vbot").exists() or (d.name == "vbot")]
    print("nav_dirs", nav_dirs[:10])
    # also look for vbot folder with section01
    vbot_dirs = [p for p in tmp.rglob("vbot") if p.is_dir() and (p / "vbot_section01_np.py").exists()]
    print("vbot_dirs", vbot_dirs)

    # Install as navigation package (official way)
    target_nav = envs / "navigation"
    if vbot_dirs:
        # create navigation/vbot structure
        if target_nav.exists():
            shutil.rmtree(target_nav)
        target_nav.mkdir(parents=True)
        (target_nav / "__init__.py").write_text("from . import vbot  # noqa: F401\n", encoding="utf-8")
        dest = target_nav / "vbot"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(vbot_dirs[0], dest)
        print("INSTALLED navigation/vbot from", vbot_dirs[0])
    elif nav_dirs:
        src = None
        for d in nav_dirs:
            if d.name == "navigation":
                src = d
                break
        if src:
            if target_nav.exists():
                shutil.rmtree(target_nav)
            shutil.copytree(src, target_nav)
            print("INSTALLED navigation from", src)

# Patch motrix_envs __init__.py to import navigation
init_p = envs / "__init__.py"
t = init_p.read_text(encoding="utf-8")
if "navigation" not in t:
    t = t.replace(
        "from . import basic, locomotion, manipulation",
        "from . import basic, locomotion, manipulation, navigation",
    )
    if "navigation" not in t:
        t = t.replace(
            "from . import basic, locomotion, manipulation  # noqa: F401",
            "from . import basic, locomotion, manipulation, navigation  # noqa: F401",
        )
    init_p.write_text(t, encoding="utf-8")
    print("patched envs __init__", t.strip())
else:
    print("envs init already has navigation")

# Prefer NOT registering locomotion vbot section01 to avoid conflict — rename registry in locomotion copy
loc_env = envs / "locomotion/vbot/vbot_section01_np.py"
if loc_env.exists():
    lt = loc_env.read_text(encoding="utf-8")
    if '@registry.env("vbot_navigation_section01"' in lt:
        lt = lt.replace(
            '@registry.env("vbot_navigation_section01"',
            '@registry.env("vbot_navigation_section01_locomotion_bak"',
        )
        loc_env.write_text(lt, encoding="utf-8")
        print("disabled locomotion section01 registry")
loc_cfg = envs / "locomotion/vbot/cfg.py"
if loc_cfg.exists():
    ct = loc_cfg.read_text(encoding="utf-8")
    if '@registry.envcfg("vbot_navigation_section01")' in ct:
        ct = ct.replace(
            '@registry.envcfg("vbot_navigation_section01")',
            '@registry.envcfg("vbot_navigation_section01_locomotion_bak")',
        )
        loc_cfg.write_text(ct, encoding="utf-8")
        print("disabled locomotion section01 envcfg")

# Replace rl cfgs if provided in zip extract
for p in Path("/root/autodl-tmp/evidence_w8/_nav_extract").rglob("cfgs.py"):
    if "motrix_rl" in str(p) or p.parent.name in ("", "vbot", "_nav_extract") or "rl" in str(p).lower():
        print("found cfgs", p)
    # copy if looks like rl cfg
    txt = p.read_text(encoding="utf-8", errors="replace")
    if "VBotNavigationSection01" in txt or "vbot_navigation_section01" in txt:
        dest = lab / "motrix_rl/src/motrix_rl/cfgs.py"
        shutil.copy2(dest, out / "cfgs.py.before_official")
        shutil.copy2(p, dest)
        print("REPLACED rl cfgs from", p)
        break

# Ensure official runs from runs.zip
if runs_zip is None:
    rz = vbot / "runs.zip"
    if rz.exists():
        runs_zip = rz
if runs_zip and runs_zip.exists():
    tmp_r = out / "_runs_extract"
    if tmp_r.exists():
        shutil.rmtree(tmp_r)
    tmp_r.mkdir()
    with zipfile.ZipFile(runs_zip) as zf:
        zf.extractall(tmp_r)
    # find checkpoints
    bests = list(tmp_r.rglob("best_agent.pickle")) + list(tmp_r.rglob("best_agent.pt"))
    print("bests in runs.zip", bests[:5])
    # copy runs/vbot_navigation_section01 if present
    for runs_dir in tmp_r.rglob("vbot_navigation_section01"):
        if runs_dir.is_dir() and (runs_dir / ".." ).exists():
            dest = lab / "runs" / "vbot_navigation_section01"
            # keep our trained runs aside
            bak = lab / "runs" / "vbot_navigation_section01_selftrain_bak"
            if dest.exists() and not bak.exists():
                dest.rename(bak)
            elif dest.exists():
                shutil.rmtree(dest)
            # copy parent structure
            parent = runs_dir.parent  # runs/
            if parent.name == "runs":
                shutil.copytree(runs_dir, dest)
                print("INSTALLED official runs", dest)
            else:
                shutil.copytree(runs_dir, dest)
                print("INSTALLED official runs alt", dest)
            break

print("DONE_SETUP")
# show navigation env obs dim
nav_py = envs / "navigation/vbot/vbot_section01_np.py"
if nav_py.exists():
    t = nav_py.read_text(encoding="utf-8")
    print("nav env exists", "shape=(67" in t, "shape=(54" in t, "shape=(68" in t)
else:
    print("NO nav env py")
    print("tree", list((envs/"navigation").rglob("*.py"))[:20] if (envs/"navigation").exists() else None)
PY

# Smoke import
.venv/bin/python - <<'PY'
import motrix_envs
from motrix_envs import registry as er
print("envs", [k for k in er._envs.keys() if "section01" in k])
# make
env = er.make("vbot_navigation_section01", "np", num_envs=1)
st = env.init_state()
print("obs", st.obs.shape, "cfg", type(env._cfg).__name__)
print("SMOKE_OK")
PY

# Play official kit
KIT=$(ls -t runs/vbot_navigation_section01/*/checkpoints/best_agent.pickle runs/vbot_navigation_section01/*/checkpoints/best_agent.pt 2>/dev/null | head -1)
# prefer Feb official if present
if [ -f runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints/best_agent.pickle ]; then
  KIT=runs/vbot_navigation_section01/26-02-05_13-04-38-452638_PPO/checkpoints/best_agent.pickle
fi
echo "KIT=$KIT"
export PLAY_POLICY="$KIT"
export PLAY_STEPS=25000
# use long play but don't force locomotion patches
python /tmp/_long_play_autodl.py
cp -f "$OUT/rollout_xy_long.csv" "$OUT/rollout_official.csv" || true
cp -f "$OUT/play_2026.mp4" "$OUT/play_official_2026.mp4" || true
cp -f "$OUT/play_trajectory_2026.mp4" "$OUT/play_official_traj.mp4" || true
grep -E 'max_y|LONG_PLAY|dy |Error|ValueError|obs_dim' "$OUT/official_play.log" | tail -40 || true
echo OFFICIAL_PLAY_DONE
'''

sftp = c.open_sftp()
with sftp.file("/tmp/_official_play.sh", "w") as f:
    f.write(sh)
sftp.close()
print(r("chmod +x /tmp/_official_play.sh; nohup bash /tmp/_official_play.sh >/root/autodl-tmp/evidence_w8/official_nohup.out 2>&1 & echo PID=$!"))
c.close()
