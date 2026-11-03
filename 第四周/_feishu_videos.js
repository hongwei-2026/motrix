const { spawnSync } = require("child_process");
const cli =
  "C:/Users/yuhon/AppData/Roaming/npm/node_modules/@larksuite/cli/scripts/run.js";
const doc = "CTb6wEgzxipc8LkQqIZcOzgPnie";
const cwd = "D:/motrix/第四周/截图/videos";
const files = [
  "cartpole_seed0.mp4",
  "pendulum_A_seed0.mp4",
  "pendulum_A_seed1.mp4",
  "pendulum_A_seed2.mp4",
  "pendulum_B_seed0.mp4",
  "pendulum_B_seed1.mp4",
  "pendulum_B_seed2.mp4",
  "acrobot_seed0.mp4",
];
for (const f of files) {
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
      "--type",
      "file",
      "--as",
      "user",
    ],
    { encoding: "utf8", maxBuffer: 30 * 1024 * 1024, cwd }
  );
  const ok = (r.stdout || "").includes('"ok": true');
  console.log(f, ok ? "OK" : "FAIL");
  if (!ok) console.log((r.stdout || r.stderr || "").slice(0, 400));
}
