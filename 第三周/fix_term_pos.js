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

function upload(file, caption) {
  for (let i = 0; i < 4; i++) {
    const r = lark(
      ["docs", "+media-insert", "--as", "user", "--doc", DOC, "--file", `./${file}`, "--align", "center", "--caption", caption],
      SHOTS
    );
    if (r.fileToken) return r.fileToken;
    sleep(4000);
  }
  return null;
}

let md = fetchMd();

// Remove the two images currently sitting after reset(data)
const anchor = "再调用子类 reset(data)。";
const ai = md.lastIndexOf(anchor);
const tailTags = [...md.slice(ai + anchor.length).matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
console.log("remove end cluster", tailTags.length);
for (const tag of tailTags) {
  console.log("del", lark(["docs", "+update", "--as", "user", "--doc", DOC_URL, "--mode", "delete_range", "--selection-with-ellipsis", tag]).ok);
  sleep(800);
}

sleep(2000);

const termTok = upload("04_失败终止_update_terminated.png", "term_shot");
const truncTok = upload("05_截断与重置_env.png", "trunc_shot");
console.log("tokens", termTok, truncTok);

// Replace the heading lines to include images right after them
const jobs = [
  {
    old: "**截图：失败判定（2 分）**",
    neu: `**截图：失败判定（2 分）**\n\n<image token="${termTok}" align="center"/>\n`,
  },
  {
    old: "**截图：超时截断与自动重置（2 分）**",
    neu: `**截图：超时截断与自动重置（2 分）**\n\n<image token="${truncTok}" align="center"/>\n`,
  },
];

for (const j of jobs) {
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
    j.old,
    "--markdown",
    j.neu,
  ]);
  console.log("replace heading", r.ok, r.out.includes("IMAGE_MISSING") ? "MISSING" : r.out.includes("background") ? "async" : "ok");
  sleep(2000);
}

sleep(20000);

// delete NEW uploads that landed at document end (caption term_shot/trunc_shot duplicates)
md = fetchMd();
const ai2 = md.lastIndexOf(anchor);
const mid = md.slice(md.indexOf("三、代码阅读"), ai2);
const tail = md.slice(ai2 + anchor.length);
console.log("mid imgs", (mid.match(/<image /g) || []).length, "tail", (tail.match(/<image /g) || []).length);

// If replace put images under headings, mid should be 5. Delete all tail.
for (const tag of [...tail.matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0])) {
  console.log("del tail", lark(["docs", "+update", "--as", "user", "--doc", DOC_URL, "--mode", "delete_range", "--selection-with-ellipsis", tag]).ok);
  sleep(700);
}

md = fetchMd();
const sec = md.slice(md.indexOf("三、代码阅读"));
console.log("FINAL", (sec.match(/<image /g) || []).length);
for (const m of sec.matchAll(/<image token="([^"]+)"[^/]*\/>/g)) {
  console.log("BEFORE", JSON.stringify(sec.slice(Math.max(0, m.index - 40), m.index)));
}
