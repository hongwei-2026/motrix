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
  const fileToken = ([...out.matchAll(/"file_token"\s*:\s*"([^"]+)"/g)].pop() || [])[1] || null;
  const ok = ([...out.matchAll(/"ok"\s*:\s*(true|false)/g)].pop() || [])[1] === "true";
  return { out, fileToken, ok };
}

function sleep(ms) {
  const end = Date.now() + ms;
  while (Date.now() < end) {}
}

function fetchMd() {
  const r = spawnSync(process.execPath, [RUNJS, "docs", "+fetch", "--as", "user", "--doc", DOC_URL], {
    encoding: "utf8",
    maxBuffer: 40 * 1024 * 1024,
    windowsHide: true,
  });
  try {
    const j = JSON.parse(r.stdout || "{}");
    fs.writeFileSync(path.join(__dirname, "_fetch_md.md"), j.data?.markdown || "");
    return j.data?.markdown || "";
  } catch {
    return "";
  }
}

const items = [
  {
    sel: "walk_np.py → apply_action()、_compute_torques()（约 160-174 行）",
    place: "PLACE_ACT_HERE",
    file: "02_动作_apply_action.png",
    key: "apply_action()",
  },
  {
    sel: "walk_np.py → update_reward()（约 249-264 行）",
    place: "PLACE_RWD_HERE",
    file: "03_奖励_update_reward.png",
    key: "update_reward()",
  },
  {
    sel: "walk_np.py → update_terminated()",
    place: "PLACE_TERM_HERE",
    file: "04_失败终止_update_terminated.png",
    key: "update_terminated()",
  },
  {
    sel: "np/env.py → _update_truncate()、_reset_done_envs()、step()",
    place: "PLACE_TRUNC_HERE",
    file: "05_截断与重置_env.png",
    key: "_update_truncate()",
  },
];

let md = fetchMd();

for (const it of items) {
  if (!md.includes(it.place)) {
    // make selection more unique by including heading context via longer string already unique in sec3
    const r = lark([
      "docs",
      "+update",
      "--as",
      "user",
      "--doc",
      DOC_URL,
      "--mode",
      "insert_after",
      "--selection-with-ellipsis",
      it.sel,
      "--markdown",
      it.place,
    ]);
    console.log("insert", it.place, r.ok, r.out.includes("更精确") ? "ambiguous" : "ok");
    if (!r.ok) {
      // try with more context from section headers
      const alt = {
        PLACE_ACT_HERE: "### 2. 动作（10 分）\n**（1）截图位置（3 分）**\n\nwalk_np.py → apply_action()、_compute_torques()（约 160-174 行）",
        PLACE_RWD_HERE: "### 3. 奖励（10 分）\n**（1）截图位置（2 分）**\n\nwalk_np.py → update_reward()（约 249-264 行）",
        PLACE_TERM_HERE: "**截图：失败判定（2 分）**\n\nwalk_np.py → update_terminated()",
        PLACE_TRUNC_HERE: "**截图：超时截断与自动重置（2 分）**\n\nnp/env.py → _update_truncate()、_reset_done_envs()、step()",
      }[it.place];
      const r2 = lark([
        "docs",
        "+update",
        "--as",
        "user",
        "--doc",
        DOC_URL,
        "--mode",
        "insert_after",
        "--selection-with-ellipsis",
        alt,
        "--markdown",
        it.place,
      ]);
      console.log("insert alt", it.place, r2.ok);
    }
    sleep(1000);
  } else {
    console.log("already has", it.place);
  }

  // upload
  let tok = null;
  for (let i = 0; i < 3 && !tok; i++) {
    const r = lark(
      ["docs", "+media-insert", "--as", "user", "--doc", DOC, "--file", `./${it.file}`, "--align", "center", "--caption", it.place],
      SHOTS
    );
    tok = r.fileToken;
    console.log("up", it.place, i, tok);
    if (!tok) sleep(4000);
  }
  if (!tok) continue;

  const r = lark([
    "docs",
    "+update",
    "--as",
    "user",
    "--doc",
    DOC_URL,
    "--mode",
    "replace_all",
    "--selection-with-ellipsis",
    it.place,
    "--markdown",
    `<image token="${tok}" align="center"/>`,
  ]);
  console.log("replace", it.place, r.ok, r.out.includes("background") ? "async" : "");
  sleep(2500);
  md = fetchMd();
}

console.log("wait 20s");
sleep(20000);
md = fetchMd();

const sec = md.slice(md.indexOf("三、代码阅读"));
console.log("images", (sec.match(/<image /g) || []).length);
for (const it of items) {
  const p = sec.indexOf(it.key);
  const chunk = p >= 0 ? sec.slice(p, p + 300) : "";
  console.log(it.place, "img near?", chunk.includes("<image"), "place left?", sec.includes(it.place));
}

// Carefully delete ONLY images that appear after the last sentence, if count > expected mid-doc images
const anchor = "再调用子类 reset(data)。";
const ai = md.lastIndexOf(anchor);
const before = md.slice(0, ai + anchor.length);
const after = md.slice(ai + anchor.length);
const midImgs = (before.slice(before.indexOf("三、代码阅读")).match(/<image /g) || []).length;
const tailImgs = [...after.matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
console.log("mid images before anchor", midImgs, "tail", tailImgs.length);

// Only delete tail if we already have >=4 images in the section body before anchor
if (midImgs >= 4 && tailImgs.length) {
  for (const tag of tailImgs) {
    const r = lark([
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
    console.log("del tail", r.ok);
    sleep(700);
  }
}

md = fetchMd();
const sec2 = md.slice(md.indexOf("三、代码阅读"));
console.log("FINAL", (sec2.match(/<image /g) || []).length);
for (const m of sec2.matchAll(/<image token="([^"]+)"[^/]*\/>/g)) {
  const idx = m.index;
  console.log("IMG before:", JSON.stringify(sec2.slice(Math.max(0, idx - 80), idx)));
}
