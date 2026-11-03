const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const DOC = "NO7PwbbhZiz2ZRkuXHZclBhwnGf";
const SHOTS = path.join(__dirname, "截图");

function run(args, opts = {}) {
  const r = spawnSync("lark-cli.cmd", args, {
    encoding: "utf8",
    shell: true,
    cwd: opts.cwd || __dirname,
    maxBuffer: 30 * 1024 * 1024,
  });
  const out = (r.stdout || "") + (r.stderr || "");
  let json = null;
  try {
    const start = out.indexOf("{");
    if (start >= 0) json = JSON.parse(out.slice(start));
  } catch (_) {}
  return { code: r.status, out, json };
}

function api(method, apiPath, { params, data } = {}) {
  const args = ["api", method, apiPath, "--as", "user"];
  if (params) {
    const f = path.join(os.tmpdir(), `lark-params-${Date.now()}-${Math.random()}.json`);
    fs.writeFileSync(f, JSON.stringify(params));
    // pass via env file content through --params with file read by node, write escaped
    args.push("--params", JSON.stringify(params));
  }
  if (data) {
    args.push("--data", JSON.stringify(data));
  }
  // Avoid shell eating quotes: write a .cmd response file approach — use spawn without shell
  const r = spawnSync(
    path.join(process.env.APPDATA, "npm", "node_modules", "@larksuite", "cli", "scripts", "run.js"),
    args,
    {
      encoding: "utf8",
      shell: false,
      maxBuffer: 30 * 1024 * 1024,
    }
  );
  // fallback
  if (r.error || r.status === null) {
    const r2 = spawnSync("node", [path.join(process.env.APPDATA, "npm", "node_modules", "@larksuite", "cli", "scripts", "run.js"), ...args], {
      encoding: "utf8",
      shell: false,
      maxBuffer: 30 * 1024 * 1024,
    });
    const out = (r2.stdout || "") + (r2.stderr || "");
    let json = null;
    try {
      const start = out.indexOf("{");
      if (start >= 0) json = JSON.parse(out.slice(start));
    } catch (_) {}
    return { code: r2.status, out, json };
  }
  const out = (r.stdout || "") + (r.stderr || "");
  let json = null;
  try {
    const start = out.indexOf("{");
    if (start >= 0) json = JSON.parse(out.slice(start));
  } catch (_) {}
  return { code: r.status, out, json };
}

const markers = [
  {
    sel: "函数：`_init_obs_space()`（约 48–59 行）、`_get_obs()`（约 188–213 行）",
    mark: "[[SHOT_OBS]]",
    file: "01_观测_get_obs.png",
  },
  {
    sel: "`walk_np.py` → `apply_action()`、`_compute_torques()`（约 160–174 行）",
    mark: "[[SHOT_ACT]]",
    file: "02_动作_apply_action.png",
  },
  {
    sel: "`walk_np.py` → `update_reward()`（约 249–264 行）",
    mark: "[[SHOT_RWD]]",
    file: "03_奖励_update_reward.png",
  },
  {
    sel: "`walk_np.py` → `update_terminated()`",
    mark: "[[SHOT_TERM]]",
    file: "04_失败终止_update_terminated.png",
  },
  {
    sel: "`np/env.py` → `_update_truncate()`、`_reset_done_envs()`、`step()`",
    mark: "[[SHOT_TRUNC]]",
    file: "05_截断与重置_env.png",
  },
];

console.log("=== insert markers ===");
for (const m of markers) {
  const r = run([
    "docs",
    "+update",
    "--as",
    "user",
    "--doc",
    `https://ccnz793r59f8.feishu.cn/wiki/${DOC}`,
    "--mode",
    "insert_after",
    "--selection-with-ellipsis",
    m.sel,
    "--markdown",
    m.mark,
  ]);
  console.log(m.mark, r.json?.ok, r.json?.error?.message || r.json?.data?.message);
}

console.log("=== upload images ===");
const tokens = {};
for (const m of markers) {
  const r = run(
    ["docs", "+media-insert", "--as", "user", "--doc", DOC, "--file", `./${m.file}`, "--align", "center", "--caption", m.mark],
    { cwd: SHOTS }
  );
  tokens[m.mark] = r.json?.data?.file_token || null;
  console.log(m.file, tokens[m.mark], r.json?.ok, r.json?.error?.message);
}
fs.writeFileSync(path.join(__dirname, "_img_tokens.json"), JSON.stringify(tokens, null, 2));

console.log("=== fetch markdown check markers ===");
const fetch = run(["docs", "+fetch", "--as", "user", "--doc", `https://ccnz793r59f8.feishu.cn/wiki/${DOC}`]);
const md = fetch.json?.data?.markdown || "";
fs.writeFileSync(path.join(__dirname, "_fetch_md.md"), md);
for (const m of markers) {
  console.log(m.mark, "in doc?", md.includes(m.mark), "img count near end", (md.match(/<image /g) || []).length);
}

// Delete trailing uploaded images by replacing caption markers at end? 
// Instead: replace_all [[SHOT_x]] with image using token — test if works when image already in doc
console.log("=== replace markers with image tokens ===");
for (const m of markers) {
  const tok = tokens[m.mark];
  if (!tok) continue;
  const r = run([
    "docs",
    "+update",
    "--as",
    "user",
    "--doc",
    `https://ccnz793r59f8.feishu.cn/wiki/${DOC}`,
    "--mode",
    "replace_all",
    "--selection-with-ellipsis",
    m.mark,
    "--markdown",
    `<image token="${tok}" width="900" align="center"/>`,
  ]);
  console.log(
    m.mark,
    r.json?.ok,
    JSON.stringify(r.json?.data?.warnings || r.json?.error?.message || r.json?.data?.message)
  );
}
