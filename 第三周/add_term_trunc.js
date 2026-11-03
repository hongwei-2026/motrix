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

function place(sel, place, file) {
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
    sel,
    "--markdown",
    place,
  ]);
  console.log("insert", place, r.ok);

  let tok = null;
  for (let i = 0; i < 4 && !tok; i++) {
    const up = lark(
      ["docs", "+media-insert", "--as", "user", "--doc", DOC, "--file", `./${file}`, "--align", "center", "--caption", place],
      SHOTS
    );
    tok = up.fileToken;
    console.log("up", place, i, tok);
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
    place,
    "--markdown",
    `<image token="${tok}" align="center"/>`,
  ]);
  console.log("replace", place, r.ok);
  sleep(2000);
}

place("**截图：失败判定（2 分）**", "MARK_TERM_ONLY", "04_失败终止_update_terminated.png");
place("**截图：超时截断与自动重置（2 分）**", "MARK_TRUNC_ONLY", "05_截断与重置_env.png");

console.log("wait 25s");
sleep(25000);
const md = fetchMd();
const sec = md.slice(md.indexOf("三、代码阅读"));
console.log("images", (sec.match(/<image /g) || []).length);
for (const m of sec.matchAll(/<image token="([^"]+)"[^/]*\/>/g)) {
  console.log("BEFORE", JSON.stringify(sec.slice(Math.max(0, m.index - 50), m.index)));
}
console.log("marks left", ["MARK_TERM_ONLY", "MARK_TRUNC_ONLY"].filter((x) => sec.includes(x)));

// delete ONLY pure trailing duplicates: images after MARK replaced content that appear after reset AND are not the only image after 失败判定/超时
// Safer: list images; if >5, delete extras from the end
const imgs = [...sec.matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
if (imgs.length > 5) {
  for (const tag of imgs.slice(5)) {
    console.log(
      "del extra",
      lark(["docs", "+update", "--as", "user", "--doc", DOC_URL, "--mode", "delete_range", "--selection-with-ellipsis", tag]).ok
    );
    sleep(700);
  }
}

const md2 = fetchMd();
const sec2 = md2.slice(md2.indexOf("三、代码阅读"));
console.log("FINAL", (sec2.match(/<image /g) || []).length);
for (const m of sec2.matchAll(/<image token="([^"]+)"[^/]*\/>/g)) {
  console.log("BEFORE", JSON.stringify(sec2.slice(Math.max(0, m.index - 50), m.index)));
}
