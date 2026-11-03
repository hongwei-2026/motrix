const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const DOC_URL = "https://ccnz793r59f8.feishu.cn/wiki/NO7PwbbhZiz2ZRkuXHZclBhwnGf";
const RUNJS = path.join(
  process.env.APPDATA,
  "npm",
  "node_modules",
  "@larksuite",
  "cli",
  "scripts",
  "run.js"
);

function lark(args) {
  const r = spawnSync(process.execPath, [RUNJS, ...args], {
    encoding: "utf8",
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
  return { json, out };
}

function sleep(ms) {
  spawnSync(process.execPath, ["-e", `setTimeout(()=>{},${ms})`], { windowsHide: true });
}

const items = [
  {
    // unique: action screenshot line jammed into section 3
    sel: "**（1）截图位置（3 分）**walk_np.py → apply_action()、_compute_torques()（约 160-174 行）",
    mark: "ZZPIC_ACT",
    img: '<image token="SbyqboMTto22pqxq9jGcMA89nji" width="960" height="440" align="center"/>',
  },
  {
    sel: "**（1）截图位置（2 分）walk_np.py → update_reward()（约 249-264 行）",
    mark: "ZZPIC_RWD",
    img: '<image token="Gu1nb3mrDo4eecxcNzWcIPg9nic" width="1099" height="462" align="center"/>',
  },
  {
    sel: "**截图：失败判定（2 分）**walk_np.py → update_terminated()",
    mark: "ZZPIC_TERM",
    img: '<image token="VgV8bb83YovntrxBjIyc9OkTnYx" width="960" height="330" align="center"/>',
  },
  {
    sel: "**截图：超时截断与自动重置（2 分）**np/env.py → _update_truncate()、_reset_done_envs()、step()",
    mark: "ZZPIC_TRUNC",
    img: '<image token="PeWabAnwHoNM5VxeE3DcUdHQn5f" width="960" height="902" align="center"/>',
  },
];

for (const it of items) {
  let r = lark([
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
    it.mark,
  ]);
  console.log("insert mark", it.mark, r.json?.ok, r.json?.data?.message || r.json?.error?.message);

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
    it.mark,
    "--markdown",
    it.img,
  ]);
  console.log("replace", it.mark, r.json?.ok, JSON.stringify(r.json?.data?.warnings || r.json?.data?.message || r.json?.error?.message));
}

console.log("wait for async...");
sleep(15000);

const fetch = lark(["docs", "+fetch", "--as", "user", "--doc", DOC_URL]);
const md = fetch.json?.data?.markdown || "";
fs.writeFileSync(path.join(__dirname, "_fetch_md.md"), md);

const i = md.indexOf("三、代码阅读");
const sec = md.slice(i);
console.log("marks left", ["ZZPIC_ACT", "ZZPIC_RWD", "ZZPIC_TERM", "ZZPIC_TRUNC"].filter((m) => sec.includes(m)));
console.log("images in sec3", (sec.match(/<image /g) || []).length);

// show snippets
for (const key of ["apply_action()", "update_reward()", "update_terminated()", "_update_truncate()"]) {
  const p = sec.indexOf(key);
  if (p < 0) {
    console.log(key, "missing");
    continue;
  }
  const chunk = sec.slice(p, p + 220);
  console.log("---", key, "img?", chunk.includes("<image"));
  console.log(chunk.replace(/\n/g, " / "));
}

// Delete trailing duplicate images after "reset(data)"
const tailStart = md.lastIndexOf("reset(data)");
const tail = md.slice(tailStart);
console.log("tail images", (tail.match(/<image /g) || []).length);
if ((tail.match(/<image /g) || []).length >= 4) {
  // delete from first trailing image to last
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
    'reset(data)（walk_np.py）。\n<image token="Idx4baQkco3ClixNjoRcwUgInVb"...<image token="PeWabAnwHoNM5VxeE3DcUdHQn5f" width="960" height="902" align="center"/>',
  ]);
  // tokens may have changed - use generic
  console.log("try delete tail", r.json?.ok, r.json?.error?.message || r.json?.data?.message);
}
