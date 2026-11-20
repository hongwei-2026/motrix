#!/usr/bin/env python3
"""Curriculum: closer targets while learning to walk +y."""
from pathlib import Path

p = Path("/root/autodl-tmp/MotrixLab/motrix_envs/src/motrix_envs/locomotion/vbot/cfg.py")
t = p.read_text(encoding="utf-8")
# VBotSection01EnvCfg pose range — make reachable during short train
old = "        pose_command_range = [0.0, 10.2, 0.0, 0.0, 10.2, 0.0]"
# first occurrence may be section001; replace only inside section01 class by unique context
marker = '@registry.envcfg("vbot_navigation_section01")'
i = t.find(marker)
if i < 0:
    raise SystemExit("section01 cfg missing")
j = t.find("pose_command_range = [0.0, 10.2, 0.0, 0.0, 10.2, 0.0]", i)
if j < 0:
    # maybe already changed
    if "pose_command_range = [0.0, 2.5" in t[i:i+2500]:
        print("already curriculum")
    else:
        raise SystemExit("pose range not found in section01")
else:
    t = t[:j] + "        pose_command_range = [0.0, 2.5, 0.0, 0.0, 4.0, 0.0]" + t[j + len(old) :]
    p.write_text(t, encoding="utf-8")
    print("curriculum pose range set for section01")
