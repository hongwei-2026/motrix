"""Headless, pre-reset rollout measurements for the LM Section01 checkpoint.

Runs from a MotrixLab checkout; no environment source or terrain is edited.
All optional overrides are diagnostic and are recorded in the output JSON.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import types

os.environ.setdefault('MOTRIX_HEADLESS', '1')
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')

import numpy as np
import torch
from torch import nn


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', default='/root/autodl-tmp/MotrixLab')
    p.add_argument('--checkpoint', default='runs/vbot_navigation_section01/known_success_PPO/checkpoints/best_agent.pt')
    p.add_argument('--steps', type=int, default=4000)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--num-envs', type=int, default=1)
    p.add_argument('--sim-dt', type=float)
    p.add_argument('--ctrl-dt', type=float)
    p.add_argument('--action-scale', type=float)
    p.add_argument('--alpha', type=float)
    p.add_argument('--final-threshold', type=float)
    p.add_argument('--goal-hold-steps', type=int, default=0)
    p.add_argument('--run-full', action='store_true')
    p.add_argument('--contacts', choices=['native', 'ones', 'zeros', 'proxy'], default='native')
    p.add_argument('--goal-x', type=float)
    p.add_argument('--goal-y', type=float, default=8.0)
    p.add_argument('--spawn-x', type=float)
    p.add_argument('--spawn-y', type=float)
    p.add_argument('--spawn-z', type=float)
    p.add_argument('--sample', action='store_true')
    p.add_argument('--no-arrows', action='store_true')
    p.add_argument('--verify-policy', action='store_true')
    p.add_argument('--render', action='store_true', help='Open the Bevy viewer on a desktop host')
    p.add_argument('--output', default='/root/autodl-tmp/rollout_result.json')
    args = p.parse_args()
    if args.render:
        os.environ['MOTRIX_HEADLESS'] = '0'
    else:
        os.environ['MOTRIX_HEADLESS'] = '1'
        os.environ.pop('DISPLAY', None)
    os.chdir(args.root)
    sys.path[:0] = ['motrix_envs/src', 'motrix_rl/src']
    torch.set_num_threads(1)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    import motrix_envs
    from motrix_envs import registry
    from motrix_envs.navigation.vbot.vbot_section01_np import VBotSection01Env
    if args.no_arrows:
        VBotSection01Env._update_target_marker = lambda *a: None
        VBotSection01Env._update_heading_arrows = lambda *a: None
    env = registry.make('vbot_navigation_section01', 'np', num_envs=args.num_envs)
    for attr in ['sim_dt', 'ctrl_dt']:
        val = getattr(args, attr)
        if val is not None:
            setattr(env.cfg, attr, val)
    env.model.options.timestep = env.cfg.sim_dt
    # Do not let the training episode time limit teleport a successful robot away.
    env.cfg.max_episode_steps = args.steps + 1
    env.cfg.max_episode_seconds = (args.steps + 1) * env.cfg.ctrl_dt
    if args.action_scale is not None:
        env.cfg.control_config.action_scale = args.action_scale
    if args.alpha is not None:
        env.action_filter_alpha = args.alpha
    if args.final_threshold is not None:
        env.final_goal_threshold = args.final_threshold
    for i, key in enumerate(['spawn_x', 'spawn_y', 'spawn_z']):
        if getattr(args, key) is not None:
            env.spawn_center[i] = getattr(args, key)
    if args.goal_x is not None:
        env.waypoint_targets = np.array([[args.goal_x, args.goal_y]], dtype=np.float32)
        env.cfg.commands.waypoint_targets = ((args.goal_x, args.goal_y),)
    if args.contacts in ['ones', 'zeros']:
        val = float(args.contacts == 'ones')
        def contact_obs(self, info, n):
            return np.concatenate([np.full((n, 4), val, dtype=np.float32),
                                   np.zeros((n, 8), dtype=np.float32)], axis=1)
        env._get_feet_proxy_obs = types.MethodType(contact_obs, env)
    elif args.contacts == 'proxy':
        def contacts(self, data):
            pos, quat, _ = self._extract_root_state(data)
            feet = self._estimate_foot_positions_world(pos, quat, self.get_dof_pos(data))
            return self._get_contacts_proxy(feet)
        env._get_foot_contacts = types.MethodType(contacts, env)

    ck = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    weights = ck['policy']
    layers = []
    for idx in [0, 2, 4]:
        w = weights[f'net.{idx}.weight']
        layer = nn.Linear(w.shape[1], w.shape[0])
        layer.weight.data.copy_(w)
        layer.bias.data.copy_(weights[f'net.{idx}.bias'])
        layers.extend([layer, nn.ELU()])
    w = weights['mean_layer.weight']
    layer = nn.Linear(w.shape[1], w.shape[0])
    layer.weight.data.copy_(w)
    layer.bias.data.copy_(weights['mean_layer.bias'])
    layers.append(layer)
    policy = nn.Sequential(*layers).eval()
    mean = ck['state_preprocessor']['running_mean'].float()
    std = ck['state_preprocessor']['running_variance'].float().sqrt()
    action_std = weights['log_std_parameter'].clamp(-20, 2).exp()
    def act(obs):
        ot = torch.as_tensor(obs, dtype=torch.float32)
        ot = ((ot - mean) / (std + 1e-8)).clamp(-5, 5)
        result = policy(ot)
        if args.sample:
            result = result + torch.randn_like(result) * action_std
        return result.numpy()

    summary = {'options': vars(args), 'max_y': [-1e9] * args.num_envs,
               'flips': [0] * args.num_envs, 'resets': [0] * args.num_envs,
               'reached': [False] * args.num_envs, 'goal_events': [], 'rows': []}
    hold = np.zeros(args.num_envs, dtype=np.int32)
    max_hold = np.zeros(args.num_envs, dtype=np.int32)
    update = env.update_state
    step_no = 0
    def measure(state):
        state = update(state)
        # Capture physics before NpEnv auto-reset overwrites pose/observations.
        pose = np.asarray(env._body.get_pose(state.data)).copy()
        gz = env._compute_projected_gravity(pose[:, 3:7])[:, 2]
        finite = np.isfinite(pose).all(axis=1)
        bad = (~finite) | (gz > -0.3) | (pose[:, 2] < 0.18)
        for j in range(args.num_envs):
            if finite[j]:
                summary['max_y'][j] = max(summary['max_y'][j], float(pose[j, 1]))
            summary['flips'][j] += int(bad[j])
            # For the hold check, suppress only successful termination, never falls.
            success_term = bool(state.info.get('goal_done', np.zeros(args.num_envs))[j])
            other_failure = any(bool(state.info.get(k, np.zeros(args.num_envs))[j])
                                for k in ['base_low', 'orientation_bad', 'numeric_bad'])
            if success_term:
                other_failure |= bool(np.any(np.abs(env.get_dof_vel(state.data)[j]) > env.cfg.max_dof_vel))
                _, _, velocity = env._extract_root_state(state.data)
                other_failure |= bool(np.linalg.norm(velocity[j, :2]) > 8.0)
            if args.goal_hold_steps and success_term and not other_failure:
                state.terminated[j] = False
            summary['resets'][j] += int(state.terminated[j])
            # Require platform height and target neighbourhood, not y alone.
            goal = (finite[j] and 7.8 <= pose[j, 1] <= 8.6 and 1.45 < pose[j, 2] < 2.15
                    and gz[j] < -0.8 and abs(pose[j, 0] + 2.7) < 1.0)
            hold[j] = hold[j] + 1 if goal else 0
            max_hold[j] = max(max_hold[j], hold[j])
            if hold[j] >= max(args.goal_hold_steps, 1):
                summary['reached'][j] = True
            if goal and hold[j] == 1:
                event = {'step': step_no, 'env': j, 'pose': pose[j].tolist(), 'gz': float(gz[j])}
                summary['goal_events'].append(event)
                print('GOAL', json.dumps(event), flush=True)
        if step_no % 200 == 0 or np.any(state.terminated):
            row = {'step': step_no, 'pose': pose.tolist(), 'gz': gz.tolist(),
                   'waypoint': state.info['waypoint_index'].tolist(),
                   'contacts': state.info['contacts'].astype(int).tolist(),
                   'resets': list(summary['resets'])}
            summary['rows'].append(row)
            if args.num_envs <= 4:
                print('ROW', json.dumps(row), flush=True)
        return state
    env.update_state = measure
    start = time.monotonic()
    state = env.init_state()
    renderer = None
    if args.render:
        from motrix_envs.np.renderer import NpRenderer
        renderer = NpRenderer(env)
    if args.verify_policy:
        import motrix_rl.cfgs
        from motrix_rl.skrl.torch.train.ppo import Trainer, _get_cfg
        from motrix_rl.skrl.torch.wrap_np import SkrlNpWrapper
        trainer = Trainer('vbot_navigation_section01', 'np', enable_render=False)
        wrapped = SkrlNpWrapper(env, False)
        models = trainer._make_model(wrapped, trainer._rlcfg)
        agent = trainer._make_agent(models, wrapped, _get_cfg(trainer._rlcfg, wrapped))
        agent.load(args.checkpoint)
        with torch.no_grad():
            ref = agent.act(torch.tensor(state.obs), 0, 0)[-1]['mean_actions'].numpy()
            error = float(np.max(np.abs(ref - act(state.obs))))
        print('POLICY_ERROR', error, flush=True)
        if not args.sample:
            assert error < 1e-4, error
    with torch.inference_mode():
        for step_no in range(1, args.steps + 1):
            frame_start = time.monotonic()
            state = env.step(act(state.obs))
            if renderer:
                renderer.render()
                time.sleep(max(0.0, env.cfg.ctrl_dt - (time.monotonic() - frame_start)))
            if all(summary['reached']) and not args.run_full:
                break
    summary['steps'] = step_no
    summary['max_hold_steps'] = max_hold.tolist()
    summary['seconds'] = time.monotonic() - start
    summary['REACH_2026'] = any(summary['reached'])
    pose = np.asarray(env._body.get_pose(state.data)).copy()
    summary['final_pose'] = pose.tolist()
    summary['final_gz'] = env._compute_projected_gravity(pose[:, 3:7])[:, 2].tolist()
    Path(args.output).write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('RESULT', json.dumps({k: v for k, v in summary.items() if k not in ['rows']}), flush=True)


if __name__ == '__main__':
    main()
