const { spawnSync } = require("child_process");
const fs = require("fs");
const cli =
  "C:/Users/yuhon/AppData/Roaming/npm/node_modules/@larksuite/cli/scripts/run.js";
const doc = "https://ccnz793r59f8.feishu.cn/wiki/CTb6wEgzxipc8LkQqIZcOzgPnie";
const docId = "CTb6wEgzxipc8LkQqIZcOzgPnie";
const imgCwd = "D:/motrix/第四周/截图";
const vidCwd = "D:/motrix/第四周/截图/videos";

function run(args, cwd) {
  const r = spawnSync(process.execPath, [cli, ...args], {
    encoding: "utf8",
    maxBuffer: 30 * 1024 * 1024,
    cwd,
  });
  const out = r.stdout || "";
  const ok = out.includes('"ok": true') || out.includes('"success": true');
  if (!ok) {
    console.log("FAIL", args.slice(0, 4).join(" "), (out || r.stderr || "").slice(0, 300));
  }
  return ok;
}

function append(md) {
  return run(
    ["docs", "+update", "--doc", doc, "--mode", "append", "--markdown", md, "--as", "user"],
    process.cwd()
  );
}

function img(file, caption) {
  return run(
    [
      "docs",
      "+media-insert",
      "--doc",
      docId,
      "--file",
      file,
      "--caption",
      caption,
      "--as",
      "user",
    ],
    imgCwd
  );
}

function vid(file) {
  return run(
    [
      "docs",
      "+media-insert",
      "--doc",
      docId,
      "--file",
      file,
      "--type",
      "file",
      "--as",
      "user",
    ],
    vidCwd
  );
}

const sections = [
  {
    title: "### 附图 · 一.1 CartPole",
    images: [
      ["A_cartpole_reward.png", "CartPole 奖励曲线"],
      ["cartpole_play.png", "CartPole 回放帧"],
    ],
    videos: ["cartpole_seed0.mp4"],
  },
  {
    title: "### 附图 · 一.1 Pendulum（A 组）",
    images: [
      ["A_pendulum_reward.png", "Pendulum A 奖励曲线"],
      ["pendulum_A_play_seed0.png", "Pendulum A seed0 中帧"],
    ],
    videos: [
      "pendulum_A_seed0.mp4",
      "pendulum_A_seed1.mp4",
      "pendulum_A_seed2.mp4",
    ],
  },
  {
    title: "### 附图 · 一.1 Acrobot",
    images: [
      ["A_acrobot_reward.png", "Acrobot 奖励曲线"],
      ["acrobot_play.png", "Acrobot 回放帧"],
    ],
    videos: ["acrobot_seed0.mp4"],
  },
  {
    title: "### 附图 · 二.3–2.4 Pendulum B 与对照回放",
    images: [
      ["B_pendulum_reward.png", "Pendulum B 奖励曲线"],
      ["pendulum_B_play_seed0.png", "Pendulum B seed0 中帧"],
      ["pendulum_A_play_seed1.png", "Pendulum A seed1"],
      ["pendulum_A_play_seed2.png", "Pendulum A seed2"],
      ["pendulum_B_play_seed1.png", "Pendulum B seed1"],
      ["pendulum_B_play_seed2.png", "Pendulum B seed2"],
    ],
    videos: [
      "pendulum_B_seed0.mp4",
      "pendulum_B_seed1.mp4",
      "pendulum_B_seed2.mp4",
    ],
  },
  {
    title: "### 附图 · 三 dm-reacher",
    images: [["dm_reacher_view.png", "dm-reacher view 场景"]],
    videos: [],
  },
];

for (const s of sections) {
  console.log(">>", s.title);
  append(s.title + "\n");
  for (const [f, c] of s.images) {
    console.log("  img", f, img(f, c) ? "OK" : "FAIL");
  }
  for (const f of s.videos) {
    console.log("  vid", f, vid(f) ? "OK" : "FAIL");
  }
}
console.log("ALL DONE");
