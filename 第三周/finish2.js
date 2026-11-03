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
  const j = JSON.parse(r.stdout || "{}");
  fs.writeFileSync(path.join(__dirname, "_fetch_md.md"), j.data?.markdown || "");
  return j.data?.markdown || "";
}

let md = fetchMd();
const anchor = "再调用子类 reset(data)。";
const ai = md.lastIndexOf(anchor);
const tags = [...md.slice(ai + anchor.length).matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
console.log("trailing", tags.length);
for (const tag of tags) {
  console.log("del", lark(["docs", "+update", "--as", "user", "--doc", DOC_URL, "--mode", "delete_range", "--selection-with-ellipsis", tag]).ok);
  sleep(800);
}

sleep(2000);
md = fetchMd();

// Also delete the image immediately after reset if it's before nothing useful - check body images
function report(md) {
  const sec = md.slice(md.indexOf("三、代码阅读"));
  console.log("images", (sec.match(/<image /g) || []).length);
  for (const m of sec.matchAll(/<image token="([^"]+)"[^/]*\/>/g)) {
    console.log("BEFORE", JSON.stringify(sec.slice(Math.max(0, m.index - 60), m.index)));
  }
}
report(md);

const jobs = [
  {
    sel: "**截图：失败判定（2 分）**",
    place: "ZZ_TERM",
    file: "04_失败终止_update_terminated.png",
  },
  {
    sel: "**截图：超时截断与自动重置（2 分）**",
    place: "ZZ_TRUNC",
    file: "05_截断与重置_env.png",
  },
];

for (const it of jobs) {
  // if heading already followed by image within next block, skip
  const p = md.indexOf(it.sel.replace(/\*\*/g, ""));
  // sel may not match without stars in plain - use indexOf of chinese
  const label = it.sel.replace(/\*\*/g, "");
  const lp = md.indexOf(label);
  const chunk = lp >= 0 ? md.slice(lp, lp + 200) : "";
  if (chunk.includes("<image")) {
    console.log(it.place, "already ok");
    continue;
  }

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
    `\n${it.place}\n`,
  ]);
  console.log("insert", it.place, r.ok, r.out.includes("更精确") ? "ambig" : r.out.slice(0, 120));

  let tok = null;
  for (let i = 0; i < 3 && !tok; i++) {
    const up = lark(
      ["docs", "+media-insert", "--as", "user", "--doc", DOC, "--file", `./${it.file}`, "--align", "center", "--caption", it.place],
      SHOTS
    );
    tok = up.fileToken;
    console.log("up", tok);
    if (!tok) sleep(4000);
  }
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
    it.place,
    "--markdown",
    `<image token="${tok}" align="center"/>`,
  ]);
  console.log("replace", r.ok);
  sleep(3000);
  md = fetchMd();
}

sleep(12000);
md = fetchMd();

// final trailing cleanup
const ai2 = md.lastIndexOf(anchor);
const mid = (md.slice(md.indexOf("三、代码阅读"), ai2).match(/<image /g) || []).length;
const tail = [...md.slice(ai2 + anchor.length).matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
console.log("mid", mid, "tail", tail.length);
if (tail.length) {
  for (const tag of tail) {
    console.log("del tail", lark(["docs", "+update", "--as", "user", "--doc", DOC_URL, "--mode", "delete_range", "--selection-with-ellipsis", tag]).ok);
    sleep(700);
  }
}

md = fetchMd();
report(md);
