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
  return { status: r.status, out, json };
}

const mapping = [
  {
    mark: "IMGPIC_OBS",
    md: '<image token="V6hpbuRQooLRacx777OcnStxn1b" width="973" height="968" align="center"/>',
  },
  {
    mark: "IMGPIC_ACT",
    md: '<image token="BgG2bwZn0okiSQxo1Ffc4obhnef" width="960" height="440" align="center"/>',
  },
  {
    mark: "IMGPIC_RWD",
    md: '<image token="Bzb0b2IczoYNZCxdM36c4tugnkf" width="1099" height="462" align="center"/>',
  },
  {
    mark: "IMGPIC_TERM",
    md: '<image token="Fx4AbUp7roA5zqxyALccBvBonPg" width="960" height="330" align="center"/>',
  },
  {
    mark: "IMGPIC_TRUNC",
    md: '<image token="IhEKbCGJXo66MUxxZEkcwlIWnsb" width="960" height="902" align="center"/>',
  },
];

for (const m of mapping) {
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
    m.mark,
    "--markdown",
    m.md,
  ]);
  console.log(
    m.mark,
    r.json?.ok,
    JSON.stringify(r.json?.data?.warnings || r.json?.data?.message || r.json?.error?.message)
  );
}

const fetch = lark(["docs", "+fetch", "--as", "user", "--doc", DOC_URL]);
const md = fetch.json?.data?.markdown || "";
fs.writeFileSync(path.join(__dirname, "_fetch_md.md"), md);

// Check: placeholders gone? images near section content?
for (const m of mapping) {
  const idxMark = md.indexOf(m.mark);
  const tok = m.md.match(/token="([^"]+)"/)[1];
  const positions = [];
  let p = 0;
  while (true) {
    const i = md.indexOf(tok, p);
    if (i < 0) break;
    positions.push(i);
    p = i + 1;
  }
  console.log(m.mark, "left?", idxMark >= 0, "token positions", positions);
}

// If duplicates at end, delete trailing image cluster by delete_range from last IMGPIC-area
// Find if images appear both mid and end
const lastReset = md.lastIndexOf("reset(data)");
const after = md.slice(lastReset);
console.log("after reset count images", (after.match(/<image /g) || []).length);
console.log("total images", (md.match(/<image /g) || []).length);
