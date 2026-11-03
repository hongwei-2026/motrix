const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const DOC = "NO7PwbbhZiz2ZRkuXHZclBhwnGf";
const DOC_URL = `https://ccnz793r59f8.feishu.cn/wiki/${DOC}`;
const SHOTS = path.join(__dirname, "截图");
const RUNJS = path.join(
  process.env.APPDATA,
  "npm",
  "node_modules",
  "@larksuite",
  "cli",
  "scripts",
  "run.js"
);

function lark(args, cwd) {
  const r = spawnSync(process.execPath, [RUNJS, ...args], {
    encoding: "utf8",
    cwd: cwd || __dirname,
    maxBuffer: 40 * 1024 * 1024,
    windowsHide: true,
  });
  const out = `${r.stdout || ""}${r.stderr || ""}`;
  let json = null;
  const i = out.indexOf("{");
  if (i >= 0) {
    try {
      json = JSON.parse(out.slice(i));
    } catch (_) {}
  }
  return { json, out, status: r.status };
}

function sleep(ms) {
  spawnSync(process.execPath, ["-e", `require('child_process').spawnSync(process.execPath,['-e','1'],{timeout:${ms}})`], {
    windowsHide: true,
  });
  // fallback busy wait
  const end = Date.now() + ms;
  while (Date.now() < end) {
    /* spin */
  }
}

function fetchMd() {
  const r = lark(["docs", "+fetch", "--as", "user", "--doc", DOC_URL]);
  const md = r.json?.data?.markdown || "";
  fs.writeFileSync(path.join(__dirname, "_fetch_md.md"), md);
  return md;
}

const sectionMd = `## 三、代码阅读（40 分，每小题 10 分）

> 作答环境：go1-flat-terrain-walk（题目模板写 CartPole，本题按实际四足代码作答）。

### 1. 观测（10 分）

**（1）截图位置（3 分）**

文件：motrix_envs/.../go1/walk_np.py
函数：_init_obs_space()（约 48-59 行）、_get_obs()（约 188-213 行）

PLACE_OBS_HERE

**（2）各分量实际顺序（2 分）**

| 顺序 | 分量 | 维数 |
| --- | --- | ---: |
| 1 | noisy_linvel 局部线速度 | 3 |
| 2 | noisy_gyro 角速度 | 3 |
| 3 | local_gravity 局部重力方向 | 3 |
| 4 | noisy_joint_angle 关节角相对默认站姿偏差 | 12 |
| 5 | noisy_joint_vel 关节角速度 | 12 |
| 6 | last_actions 上一帧动作 | 12 |
| 7 | command 速度命令 [vx, vy, vyaw] | 3 |
| | 合计 | 48 |

**（3）物理含义与单位（3 分）**

| 分量 | 含义 | 单位（缩放前） |
| --- | --- | --- |
| 线速度 | 机体坐标系下基座线速度，再乘 normalization.lin_vel=2 | m/s |
| 角速度 | 陀螺仪角速度，再乘 ang_vel=0.25 | rad/s |
| 局部重力 | 重力方向转到机体坐标，反映姿态倾斜 | 无量纲方向向量 |
| 关节角偏差 | 当前关节角减去默认站姿角，乘 dof_pos=1 | rad |
| 关节速度 | 12 关节角速度，乘 dof_vel=0.05 | rad/s |
| 上一动作 | 上一步策略输出的 12 维动作 | 与动作同量纲 |
| 速度命令 | 期望 [vx,vy,vyaw]，再乘 commands_scale | m/s、rad/s |

**（4）维度核对（2 分）**

3+3+3+12+12+12+3 = 48，与 observation_space 的 48 维一致。

### 2. 动作（10 分）

**（1）截图位置（3 分）**

walk_np.py → apply_action()、_compute_torques()（约 160-174 行）

PLACE_ACT_HERE

**（2）控制部件与物理量（3 分）**

控制 12 个腿关节（FR/FL/RR/RL 的 hip、thigh、calf）。策略输出是相对默认角的位置偏移；经 PD 后写入的物理量是关节力矩（N·m），赋给 state.data.actuator_ctrls。

**（3）完整路径与裁剪/缩放（4 分）**

策略输出 a (12维)
→ 训练 clip_actions：无（skrl/config.py 默认 False）
→ apply_action：有缩放 action_scale=0.05，再 PD（kp=80, kd=1）得力矩
→ XML：ctrlrange 为 -23.7 到 23.7，无 gear
→ 执行器施加关节力矩

### 3. 奖励（10 分）

**（1）截图位置（2 分）**

walk_np.py → update_reward()（约 249-264 行）

PLACE_RWD_HERE

**（2）设每步奖励为 1、无折扣的累计奖励（各 2 分）**

- 持续 20 步：累计奖励 = 20
- 持续 80 步：累计奖励 = 80

**（3）为何能鼓励不倒/稳定（4 分）**

活得越久累计回报越大。GO1 躯干触地会 terminated 且该步奖励置 0，因此策略会被激励保持稳定、推迟失败。

### 4. 终止与截断（10 分）

| 题目情形 | 归类 | GO1 平地判据 |
| --- | --- | --- |
| 1 杆角度越界 | 失败终止 | 等价：躯干 trunk 触地 → terminated=True |
| 2 小车位置越界 | 失败终止 | 平地代码未实现 |
| 3 状态正常但超时 | 时间截断 | steps>=2000（20.0/0.01）→ truncated=True |

**截图：失败判定（2 分）**

walk_np.py → update_terminated()

PLACE_TERM_HERE

**截图：超时截断与自动重置（2 分）**

np/env.py → _update_truncate()、_reset_done_envs()、step()

PLACE_TRUNC_HERE

**回合结束后谁重置（2 分）**

step() 末尾调用 _reset_done_envs()，再调用子类 reset(data)。
`;

console.log("A) rewrite clean section 3 with placeholders");
let r = lark([
  "docs",
  "+update",
  "--as",
  "user",
  "--doc",
  DOC_URL,
  "--mode",
  "replace_range",
  "--selection-by-title",
  "## 三、代码阅读（40 分，每小题 10 分）",
  "--markdown",
  sectionMd,
]);
console.log(r.json?.ok, r.json?.data?.message || r.json?.error?.message);

sleep(2000);
let md = fetchMd();
console.log("placeholders", ["PLACE_OBS_HERE", "PLACE_ACT_HERE", "PLACE_RWD_HERE", "PLACE_TERM_HERE", "PLACE_TRUNC_HERE"].map((k) => [k, md.includes(k)]));

// Delete every image currently in doc
console.log("B) delete all existing images");
md = fetchMd();
const imgs = [...md.matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
console.log("found images", imgs.length);
for (const tag of imgs) {
  r = lark([
    "docs",
    "+update",
    "--as",
    "user",
    "--doc",
    DOC_URL,
    "--mode",
    "delete_range",
    "--selection-with-ellipsis",
    tag,
  ]);
  console.log("del", tag.slice(0, 40), r.json?.ok, r.json?.error?.message || "");
  sleep(800);
}

sleep(2000);

// Upload in order and capture tokens
console.log("C) upload 5 images");
const shots = [
  { place: "PLACE_OBS_HERE", file: "01_观测_get_obs.png" },
  { place: "PLACE_ACT_HERE", file: "02_动作_apply_action.png" },
  { place: "PLACE_RWD_HERE", file: "03_奖励_update_reward.png" },
  { place: "PLACE_TERM_HERE", file: "04_失败终止_update_terminated.png" },
  { place: "PLACE_TRUNC_HERE", file: "05_截断与重置_env.png" },
];
const tokens = {};
for (const s of shots) {
  for (let attempt = 0; attempt < 3; attempt++) {
    r = lark(
      ["docs", "+media-insert", "--as", "user", "--doc", DOC, "--file", `./${s.file}`, "--align", "center", "--caption", s.place],
      SHOTS
    );
    const tok = r.json?.data?.file_token;
    if (tok) {
      tokens[s.place] = tok;
      console.log("up", s.place, tok);
      break;
    }
    console.log("up fail", s.place, attempt, r.json?.error?.message || r.out.slice(0, 200));
    sleep(3000);
  }
  sleep(1000);
}

fs.writeFileSync(path.join(__dirname, "_img_tokens.json"), JSON.stringify(tokens, null, 2));

console.log("D) replace placeholders with images");
for (const s of shots) {
  const tok = tokens[s.place];
  if (!tok) continue;
  r = lark([
    "docs",
    "+update",
    "--as",
    "user",
    "--doc",
    DOC_URL,
    "--mode",
    "replace_all",
    "--selection-with-ellipsis",
    s.place,
    "--markdown",
    `<image token="${tok}" align="center"/>`,
  ]);
  console.log("place", s.place, r.json?.ok, JSON.stringify(r.json?.data?.message || r.json?.data?.warnings || r.json?.error?.message));
  sleep(1500);
}

console.log("E) wait async 20s");
sleep(20000);
md = fetchMd();

for (const s of shots) {
  const i = md.indexOf(s.place);
  const tok = tokens[s.place];
  const around = (() => {
    // find context labels
    const keys = {
      PLACE_OBS_HERE: "_get_obs()",
      PLACE_ACT_HERE: "apply_action()",
      PLACE_RWD_HERE: "update_reward()",
      PLACE_TERM_HERE: "update_terminated()",
      PLACE_TRUNC_HERE: "_update_truncate()",
    };
    const k = keys[s.place];
    const p = md.indexOf(k);
    return p >= 0 ? md.slice(p, p + 250) : "";
  })();
  console.log(s.place, "mark?", i >= 0, "img near key?", around.includes("<image"), "tok in doc?", tok ? md.includes(tok) : false);
}

// Delete any remaining trailing duplicate images after last PLACE/重置 paragraph
md = fetchMd();
const tailAnchor = "step() 末尾调用 _reset_done_envs()，再调用子类 reset(data)。";
const t = md.indexOf(tailAnchor);
if (t >= 0) {
  const after = md.slice(t + tailAnchor.length);
  const trailing = [...after.matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
  console.log("trailing after anchor", trailing.length);
  for (const tag of trailing) {
    r = lark([
      "docs",
      "+update",
      "--as",
      "user",
      "--doc",
      DOC_URL,
      "--mode",
      "delete_range",
      "--selection-with-ellipsis",
      tag,
    ]);
    console.log("del trailing", r.json?.ok, r.json?.error?.message || "");
    sleep(800);
  }
}

md = fetchMd();
const sec = md.slice(md.indexOf("三、代码阅读"));
console.log("FINAL images in sec3", (sec.match(/<image /g) || []).length);
console.log("FINAL placeholders left", shots.filter((s) => sec.includes(s.place)).map((s) => s.place));
