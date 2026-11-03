const { spawnSync } = require("child_process");
const cli =
  "C:/Users/yuhon/AppData/Roaming/npm/node_modules/@larksuite/cli/scripts/run.js";
const doc = "CTb6wEgzxipc8LkQqIZcOzgPnie";
const cwd = "D:/motrix/第四周/截图";
const files = [
  ["A_cartpole_reward.png", "CartPole 奖励曲线"],
  ["A_pendulum_reward.png", "Pendulum A 奖励曲线"],
  ["B_pendulum_reward.png", "Pendulum B 奖励曲线"],
  ["A_acrobot_reward.png", "Acrobot 奖励曲线"],
  ["cartpole_play.png", "CartPole 回放"],
  ["pendulum_A_play_seed0.png", "Pendulum A seed0"],
  ["pendulum_B_play_seed0.png", "Pendulum B seed0"],
  ["acrobot_play.png", "Acrobot 回放"],
  ["dm_reacher_view.png", "dm-reacher view"],
];
for (const [f, cap] of files) {
  const r = spawnSync(
    process.execPath,
    [
      cli,
      "docs",
      "+media-insert",
      "--doc",
      doc,
      "--file",
      f,
      "--caption",
      cap,
      "--as",
      "user",
    ],
    { encoding: "utf8", maxBuffer: 20 * 1024 * 1024, cwd }
  );
  const ok = (r.stdout || "").includes('"ok": true');
  console.log(cap, ok ? "OK" : "FAIL");
  if (!ok) console.log((r.stdout || r.stderr || "").slice(0, 400));
}
