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
  const tokens = [...out.matchAll(/"file_token"\s*:\s*"([^"]+)"/g)].map((m) => m[1]);
  const oks = [...out.matchAll(/"ok"\s*:\s*(true|false)/g)].map((m) => m[1] === "true");
  return { out, fileToken: tokens[tokens.length - 1] || null, ok: oks[oks.length - 1] ?? null };
}

function sleep(ms) {
  const end = Date.now() + ms;
  while (Date.now() < end) {}
}

const shots = [
  { place: "PLACE_OBS_HERE", file: "01_观测_get_obs.png" },
  { place: "PLACE_ACT_HERE", file: "02_动作_apply_action.png" },
  { place: "PLACE_RWD_HERE", file: "03_奖励_update_reward.png" },
  { place: "PLACE_TERM_HERE", file: "04_失败终止_update_terminated.png" },
  { place: "PLACE_TRUNC_HERE", file: "05_截断与重置_env.png" },
];

const tokens = {};
for (const s of shots) {
  let tok = null;
  for (let i = 0; i < 4 && !tok; i++) {
    const r = lark(
      ["docs", "+media-insert", "--as", "user", "--doc", DOC, "--file", `./${s.file}`, "--align", "center", "--caption", s.place],
      SHOTS
    );
    tok = r.fileToken;
    console.log("upload", s.place, "try", i, "tok", tok, "ok", r.ok);
    if (!tok) sleep(4000);
  }
  tokens[s.place] = tok;
  sleep(1500);
}
fs.writeFileSync(path.join(__dirname, "_img_tokens.json"), JSON.stringify(tokens, null, 2));

for (const s of shots) {
  const tok = tokens[s.place];
  if (!tok) {
    console.log("skip", s.place);
    continue;
  }
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
    s.place,
    "--markdown",
    `<image token="${tok}" align="center"/>`,
  ]);
  console.log("replace", s.place, "ok", r.ok, r.out.includes("background") ? "async" : "sync", r.out.includes("IMAGE_MISSING") ? "MISSING" : "okish");
  sleep(2000);
}

console.log("wait 25s for async");
sleep(25000);

const fetch = lark(["docs", "+fetch", "--as", "user", "--doc", DOC_URL]);
const mdMatch = fetch.out.match(/"markdown"\s*:\s*"((?:\\.|[^"\\])*)"/);
let md = "";
if (mdMatch) {
  md = JSON.parse(`"${mdMatch[1]}"`);
} else {
  // fallback write raw
  fs.writeFileSync(path.join(__dirname, "_raw_fetch.txt"), fetch.out.slice(0, 50000));
}
// better: write out and parse via another approach
const fr = spawnSync(
  process.execPath,
  [
    RUNJS,
    "docs",
    "+fetch",
    "--as",
    "user",
    "--doc",
    DOC_URL,
  ],
  { encoding: "utf8", maxBuffer: 40 * 1024 * 1024, windowsHide: true }
);
fs.writeFileSync(path.join(__dirname, "_fetch_raw.json"), fr.stdout || fr.stderr || "");
try {
  const j = JSON.parse(fr.stdout || "{}");
  md = j.data?.markdown || "";
  fs.writeFileSync(path.join(__dirname, "_fetch_md.md"), md);
} catch (e) {
  console.log("parse fetch fail", e.message);
}

const sec = md.slice(md.indexOf("三、代码阅读"));
console.log("images", (sec.match(/<image /g) || []).length);
console.log(
  "placeholders left",
  shots.filter((s) => sec.includes(s.place)).map((s) => s.place)
);

for (const s of shots) {
  const keys = {
    PLACE_OBS_HERE: "_get_obs()",
    PLACE_ACT_HERE: "apply_action()",
    PLACE_RWD_HERE: "update_reward()",
    PLACE_TERM_HERE: "update_terminated()",
    PLACE_TRUNC_HERE: "_update_truncate()",
  };
  const p = sec.indexOf(keys[s.place]);
  const chunk = p >= 0 ? sec.slice(p, p + 280) : "";
  console.log(s.place, "near key has image?", chunk.includes("<image"));
}

// delete trailing images after reset(data) line if duplicates
const anchor = "再调用子类 reset(data)。";
const ai = md.lastIndexOf(anchor);
if (ai >= 0) {
  const after = md.slice(ai + anchor.length);
  const tags = [...after.matchAll(/<image token="[^"]+"[^/]*\/>/g)].map((m) => m[0]);
  console.log("trailing dups", tags.length);
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
    sleep(700);
  }
}

const fr2 = spawnSync(process.execPath, [RUNJS, "docs", "+fetch", "--as", "user", "--doc", DOC_URL], {
  encoding: "utf8",
  maxBuffer: 40 * 1024 * 1024,
  windowsHide: true,
});
try {
  const j = JSON.parse(fr2.stdout || "{}");
  const sec2 = (j.data?.markdown || "").slice((j.data?.markdown || "").indexOf("三、代码阅读"));
  fs.writeFileSync(path.join(__dirname, "_fetch_md.md"), j.data?.markdown || "");
  console.log("FINAL images", (sec2.match(/<image /g) || []).length);
  console.log(
    "FINAL places",
    shots.filter((s) => sec2.includes(s.place)).map((s) => s.place)
  );
} catch (e) {
  console.log(e.message);
}
