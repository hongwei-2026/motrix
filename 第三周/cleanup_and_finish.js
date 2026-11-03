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

// Delete trailing images: everything after the first image that follows reset(data)。
const anchor = "再调用子类 reset(data)。";
const ai = md.lastIndexOf(anchor);
const after = md.slice(ai + anchor.length);
const tags = [...after.matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
console.log("delete trailing", tags.length);
for (const tag of tags) {
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
  console.log("del", r.ok);
  sleep(800);
}

sleep(2000);
md = fetchMd();

// Ensure TERM and TRUNC markers exist in the right spots
const need = [
  {
    checkKey: "update_terminated()",
    // image should appear within 200 chars after this key, before 超时截断
    place: "NEED_TERM",
    sel: "**截图：失败判定（2 分）**\n\nwalk_np.py → update_terminated()",
    file: "04_失败终止_update_terminated.png",
  },
  {
    checkKey: "_update_truncate()",
    place: "NEED_TRUNC",
    sel: "**截图：超时截断与自动重置（2 分）**\n\nnp/env.py → _update_truncate()、_reset_done_envs()、step()",
    file: "05_截断与重置_env.png",
  },
];

for (const it of need) {
  const p = md.indexOf(it.checkKey);
  const chunk = p >= 0 ? md.slice(p, p + 220) : "";
  const has = chunk.includes("<image");
  console.log(it.place, "already has image near key?", has);
  if (has) continue;

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
    it.place,
  ]);
  console.log("insert", it.place, r.ok, r.out.includes("更精确") ? "ambig" : "");

  if (!r.ok) {
    // fallback shorter unique
    r = lark([
      "docs",
      "+update",
      "--as",
      "user",
      "--doc",
      DOC_URL,
      "--mode",
      "insert_after",
      "--selection-with-ellipsis",
      it.checkKey,
      "--markdown",
      it.place,
    ]);
    console.log("insert short", it.place, r.ok);
  }

  let tok = null;
  for (let i = 0; i < 3 && !tok; i++) {
    const up = lark(
      ["docs", "+media-insert", "--as", "user", "--doc", DOC, "--file", `./${it.file}`, "--align", "center", "--caption", it.place],
      SHOTS
    );
    tok = up.fileToken;
    console.log("up", it.place, tok);
    if (!tok) sleep(4000);
  }
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
    it.place,
    "--markdown",
    `<image token="${tok}" align="center"/>`,
  ]);
  console.log("replace", it.place, r.ok);
  sleep(3000);
}

sleep(15000);
md = fetchMd();

// delete new trailing dups again if any, but keep mid-body images
const ai2 = md.lastIndexOf(anchor);
const before = md.slice(0, ai2 + anchor.length);
const after2 = md.slice(ai2 + anchor.length);
const mid = (before.slice(before.indexOf("三、代码阅读")).match(/<image /g) || []).length;
const tail = [...after2.matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
console.log("mid", mid, "tail", tail.length);
if (mid >= 4) {
  for (const tag of tail) {
    lark(["docs", "+update", "--as", "user", "--doc", DOC_URL, "--mode", "delete_range", "--selection-with-ellipsis", tag]);
    sleep(700);
  }
}

md = fetchMd();
const sec = md.slice(md.indexOf("三、代码阅读"));
console.log("FINAL images", (sec.match(/<image /g) || []).length);
for (const m of sec.matchAll(/<image token="([^"]+)"[^/]*\/>/g)) {
  console.log("BEFORE", JSON.stringify(sec.slice(Math.max(0, m.index - 70), m.index)));
}
