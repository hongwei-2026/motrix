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


def r(cmd, t=120):
    _, o, e = c.exec_command(cmd, timeout=t)
    return (o.read() + e.read()).decode("utf-8", "replace")


fix = r'''
from pathlib import Path
import re
cfg = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/navigation/vbot/cfg.py")
ct = cfg.read_text(encoding="utf-8")
marker = '@registry.envcfg("vbot_navigation_section01")'
i = ct.find(marker)
j = ct.find("@registry.envcfg", i+10)
block = ct[i:j]
block2 = re.sub(r"max_episode_seconds: float = [0-9.]+", "max_episode_seconds: float = 300.0", block, count=1)
block2 = re.sub(r"max_episode_steps: int = \d+", "max_episode_steps: int = 30000", block2, count=1)
cfg.write_text(ct[:i]+block2+ct[j:], encoding="utf-8")
print("EPISODE_EXTENDED", [ln.strip() for ln in block2.splitlines() if "max_episode" in ln][:4])
'''
sftp = c.open_sftp()
with sftp.file("/tmp/_ext_ep.py", "w") as f:
    f.write(fix)
# bump steps in play script via env
play = open(r"D:\motrix\_w8\push_env_continue.py", encoding="utf-8").read()  # just to have path
# rewrite known play with STEPS=40000
known = Path_read = None
from pathlib import Path as P
# read remote known play and patch STEPS - easier upload new
kp = r'''
import os, sys, csv, time, traceback, re
from pathlib import Path
import numpy as np

ROOT = Path("/root/autodl-tmp"); OUT = ROOT/"evidence_w8"
os.chdir(str(ROOT/"MotrixLab"))
sys.path[:0]=[str(ROOT/"MotrixLab"), str(ROOT/"MotrixLab"/"scripts")]
os.environ["MOTRIX_HEADLESS"]="1"
CKPT="runs/vbot_navigation_section01/known_success_PPO/checkpoints/best_agent.pt"
STEPS=40000
print("USING", CKPT, "STEPS", STEPS)

p=Path("scripts/play.py"); t=p.read_text(encoding="utf-8")
if "enable_render = True" in t:
    p.write_text(t.replace("enable_render = True","enable_render = False",1),encoding="utf-8")

for rel in ["motrix_rl/src/motrix_rl/skrl/torch/train/ppo.py"]:
    pp=Path(rel)
    src=Path(str(pp)+".bak_hw").read_text(encoding="utf-8") if Path(str(pp)+".bak_hw").exists() else pp.read_text(encoding="utf-8")
    if not Path(str(pp)+".bak_hw").exists():
        Path(str(pp)+".bak_hw").write_text(pp.read_text(encoding="utf-8"),encoding="utf-8")
        src=pp.read_text(encoding="utf-8")
    src2=re.sub(
        r"        fps = \d+\n        (?:max_steps = \d+\n)?        (?:while True:|for step_i in range\(max_steps\):)\n(?:            t = time\.time\(\)\n)?            outputs = agent\.act\(obs, timestep=0, timesteps=0\)\n            actions = outputs\[-1\]\.get\(\"mean_actions\", outputs\[0\]\)\n            obs, _, _, _, _ = env\.step\(actions\)\n(?:            env\.render\(\)\n)?(?:            delta_time = time\.time\(\) - t\n            if delta_time < 1\.0 / fps:\n                time\.sleep\(1\.0 / fps - delta_time\))?",
        f"        max_steps = {STEPS}\n        for step_i in range(max_steps):\n            outputs = agent.act(obs, timestep=0, timesteps=0)\n            actions = outputs[-1].get(\"mean_actions\", outputs[0])\n            obs, _, _, _, _ = env.step(actions)\n        print(\"LONG_PLAY_LOOP_DONE\", max_steps)",
        src, count=1)
    pp.write_text(src2, encoding="utf-8")

import motrix_envs, motrix_rl.cfgs
from motrix_envs import registry as er
import motrix_envs.navigation.vbot.vbot_section01_np as env_mod
rows=[]; _Old=env_mod.VBotSection01Env

def _xyz(env):
    data=getattr(env,"_data",None) or env.state.data
    pose=np.asarray(env._body.get_pose(data),dtype=np.float32)
    return pose[0,:3] if pose.ndim>1 else pose[:3]

def install(env):
    step_fn=env.step
    def wrapped(action):
        state=step_fn(action)
        try:
            xyz=_xyz(env); rew=float(np.asarray(state.reward).reshape(-1)[0])
            rows.append((len(rows),float(xyz[0]),float(xyz[1]),float(xyz[2]),rew))
            if len(rows)%200==0:
                print(f"step={len(rows)} xy=({xyz[0]:.3f},{xyz[1]:.3f},{xyz[2]:.3f}) rew={rew:.3f} max_y_so_far={max(r[2] for r in rows):.3f}", flush=True)
            if len(rows)>=STEPS: raise SystemExit(0)
        except SystemExit: raise
        except Exception:
            if len(rows)<5: traceback.print_exc()
        return state
    env.step=wrapped; return env

class Hooked(_Old):
    def __init__(self,*a,**k):
        super().__init__(*a,**k); install(self)
er._envs["vbot_navigation_section01"].env_cls_dict["np"]=Hooked
env_mod.VBotSection01Env=Hooked
sys.argv=["play.py","--env=vbot_navigation_section01","--num-envs=1",f"--policy={CKPT}"]
try:
    from absl import app; import scripts.play as P
    try: app.run(P.main)
    except SystemExit: pass
except Exception as e:
    print("PLAY_ERR",e); traceback.print_exc()

ys=[r[2] for r in rows]; xs=[r[1] for r in rows]
print("collected",len(rows),"max_y",max(ys) if ys else None)
print("REACHED_2026" if ys and max(ys)>=7.5 else f"PARTIAL max_y={max(ys) if ys else None}")
with (OUT/"rollout_homework.csv").open("w",newline="") as f:
    w=csv.writer(f); w.writerow(["step","x","y","z","rew"]); w.writerows(rows)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
fig,ax=plt.subplots(figsize=(8,6),dpi=120)
ax.axhline(7.84,color="r",ls="--"); ax.plot(xs,ys); ax.grid(True,alpha=0.3)
fig.savefig(OUT/"homework_traj.png", bbox_inches="tight")
fig2,ax2=plt.subplots(figsize=(8,4.5),dpi=140); ax2.axis("off")
ax2.text(0.02,0.8,f"Homework evidence  max_y={max(ys):.3f}  reached={max(ys)>=7.5}", fontsize=14, transform=ax2.transAxes)
fig2.savefig(OUT/"homework_evidence_card.png", bbox_inches="tight")
fig3,ax3=plt.subplots(figsize=(8,6),dpi=100); ax3.axhline(7.84,color="r",ls="--")
(line,)=ax3.plot([],[],"-"); (pt,)=ax3.plot([],[],"o")
ax3.set_xlim(min(xs)-0.5,max(xs)+0.5); ax3.set_ylim(min(min(ys),7.84)-0.5,max(max(ys),7.84)+0.5)
frames=list(range(0,len(rows),max(1,len(rows)//400)))
try:
    w=FFMpegWriter(fps=24)
    with w.saving(fig3,str(OUT/"play_homework_traj.mp4"),dpi=100):
        for i in frames:
            line.set_data(xs[:i+1],ys[:i+1]); pt.set_data([xs[i]],[ys[i]]); w.grab_frame()
except Exception as e:
    print("mp4",e)
print("LONG_EP_DONE")
'''
with sftp.file("/tmp/_long_ep_play.py", "w") as f:
    f.write(kp)
sftp.close()

print(r("/root/autodl-tmp/MotrixLab/.venv/bin/python /tmp/_ext_ep.py"))
print(
    r(
        "nohup /root/autodl-tmp/MotrixLab/.venv/bin/python /tmp/_long_ep_play.py "
        ">/root/autodl-tmp/evidence_w8/long_ep.log 2>&1 & echo PID=$!"
    )
)
# also start jax train on waypoint env in parallel? GPU conflict - only play for now
c.close()
