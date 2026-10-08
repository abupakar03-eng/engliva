// Verifies the shipped web lookup logic (web/app.js) against the shipped
// glossary, so the browser mirror is held to the same coverage guarantee as
// the Android app. Run: node tools/glossary/check_web.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const appJs = fs.readFileSync(path.join(root, "web", "app.js"), "utf8");
const glossary = JSON.parse(
  fs.readFileSync(path.join(root, "app", "src", "main", "assets", "glossary.json"), "utf8"),
).entries;
const translations = JSON.parse(
  fs.readFileSync(path.join(root, "app", "src", "main", "assets", "translations.json"), "utf8"),
).strings;
const displayStrings = JSON.parse(
  fs.readFileSync(path.join(root, "tools", "glossary", "strings.json"), "utf8"),
);
const words = fs
  .readFileSync(path.join(root, "tools", "glossary", "words.txt"), "utf8")
  .split("\n")
  .filter(Boolean);

// Pull the real functions out of app.js (they are the code that ships) and run
// them with just the globals they need.
const start = appJs.indexOf("function normalizeWord");
const end = appJs.indexOf("let wordPopupEl");
if (start < 0 || end < 0) {
  console.error("FAIL: could not locate the tap-to-translate block in web/app.js");
  process.exit(1);
}
const escapeHtml = s =>
  String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// ttsAvailable lives outside the extracted block, so the sandbox supplies it.
const api = new Function(
  "state",
  "escapeHtml",
  "ttsAvailable",
  appJs.slice(start, end) + "; return { normalizeWord, wordCandidates, lookupWord, linkWords, tamilLine, wordGloss };",
)({ glossary, translations }, escapeHtml, false);

const failures = [];
const check = (name, ok) => { if (!ok) failures.push(name); };

check("normalizeWord strips punctuation", api.normalizeWord('"Morning,"') === "morning");
check("normalizeWord keeps contractions", api.normalizeWord("Don\u2019t!") === "don't");
check("normalizeWord rejects punctuation-only", api.normalizeWord("...") === "");
check("exact hit", api.lookupWord("morning") === glossary["morning"]);
check("unknown word is null", api.lookupWord("helo") === null);

// Deterministic chain checks against a synthetic glossary, mirroring GlossaryTest.kt.
const synthetic = new Function(
  "state",
  "escapeHtml",
  appJs.slice(start, end) + "; return { lookupWord, wordCandidates };",
)({ glossary: { house: "வீடு", student: "மாணவர்", walk: "நட", city: "நகரம்", hello: "வணக்கம்" } }, escapeHtml);
check("base-form fallback covers plurals/tenses",
  synthetic.lookupWord("houses") === "வீடு" &&
  synthetic.lookupWord("students") === "மாணவர்" &&
  synthetic.lookupWord("walking") === "நட" &&
  synthetic.lookupWord("cities") === "நகரம்" &&
  synthetic.lookupWord("hello's") === "வணக்கம்");
check("no similarity guessing", synthetic.lookupWord("helo") === null);
check("candidates are ordered and deduplicated", (() => {
  const c = synthetic.wordCandidates("walking");
  return c[0] === "walking" && new Set(c).size === c.length;
})());

// Exact form beats its base form when both are present.
const both = words.filter(w => w.endsWith("s") && glossary[w] && glossary[w.slice(0, -1)]);
check(`exact form wins over base form (${both.length} pairs in the course)`,
  both.every(w => api.lookupWord(w) === glossary[w]));

const linked = api.linkWords("Good morning");
check("linkWords wraps known words", (linked.match(/class="w"/g) || []).length === 2);
check("linkWords leaves unknown words plain", !api.linkWords("zzzz").includes('class="w"'));
const escaped = api.linkWords('<script>alert("x")</script>');
check("linkWords escapes markup", !escaped.includes("<script>") && escaped.includes("&lt;script&gt;"));

const unresolved = words.filter(w => api.lookupWord(w) === null);
check(`every course word resolves on web (${words.length - unresolved.length}/${words.length})`, unresolved.length === 0);

// ── Tamil translation line ──────────────────────────────────────────────────
const sampleLine = "Good morning Sir / Madam / Raju etc.";
const natural = api.tamilLine(sampleLine);
check("tamilLine uses the generated translation", natural.includes("ta-line") && natural.includes(translations[sampleLine]));
check("tamilLine escapes markup", !api.tamilLine('<script>alert("x")</script>').includes("<script>"));
check("tamilLine is empty for unknown text", api.tamilLine("") === "");

// Every displayed string must produce a Tamil line without tapping.
const noLine = displayStrings.filter(s => !api.tamilLine(s).includes("ta-line"));
check(`every displayed line gets Tamil (${displayStrings.length - noLine.length}/${displayStrings.length})`, noLine.length === 0);

// The word-by-word path still works when no whole-line translation exists.
const glossApi = new Function(
  "state",
  "escapeHtml",
  "ttsAvailable",
  appJs.slice(start, end) + "; return { tamilLine, wordGloss };",
)({ glossary: { good: "நல்ல", morning: "காலை" }, translations: null }, escapeHtml, false);
check("gloss fallback when translations are missing",
  glossApi.tamilLine("Good morning").includes("நல்ல காலை"));

// Turning Tamil off hides every line, and only an explicit false does it.
const offApi = new Function(
  "state",
  "escapeHtml",
  "ttsAvailable",
  appJs.slice(start, end) + "; return { tamilLine };",
)({ glossary, translations, showTamil: false }, escapeHtml, false);
check("Tamil off hides the line", offApi.tamilLine(sampleLine) === "");
check("a state without the flag keeps Tamil on", api.tamilLine(sampleLine).includes("ta-line"));
check("gloss returns nothing when no word is known", glossApi.wordGloss("zzz qqq") === "");

// ── Word-level diff (mirrors AnswerDiffTest.kt) ─────────────────────────────
const diffStart = appJs.indexOf("function compareWords");
const diffEnd = appJs.indexOf("function renderSttRow");
if (diffStart < 0 || diffEnd < 0) {
  console.error("FAIL: could not locate the word-diff block in web/app.js");
  process.exit(1);
}
const diffApi = new Function(
  "state",
  "escapeHtml",
  appJs.slice(diffStart, diffEnd) + "; return { compareWords, wordDiffHtml };",
)({}, escapeHtml);

const exact = diffApi.compareWords("Good morning Sir", "good morning sir");
check("diff: identical text is all heard", exact.missed.length === 0 && exact.words.length === 3);
const missing = diffApi.compareWords("Good morning Sir", "good morning");
check("diff: missing word flagged", missing.missed.join(",") === "sir");
check("diff: trailing word marked not heard", missing.words.map(w => w.heard).join(",") === "true,true,false");
const inserted = diffApi.compareWords("I am fine thank you", "I am um fine thank you");
check("diff: inserted word does not mark the rest wrong", inserted.missed.length === 0);
const different = diffApi.compareWords("Good morning", "good night");
check("diff: different answer misses the word", different.missed.join(",") === "morning");
const diffHtml = diffApi.wordDiffHtml('Good <script>', "good");
check("diff: escapes markup", !diffHtml.includes("<script>") && diffHtml.includes("wd-sum"));

if (failures.length) {
  console.error("FAIL");
  for (const f of failures) console.error("  -", f);
  if (unresolved.length) console.error("  unresolved sample:", unresolved.slice(0, 20).join(", "));
  if (noLine.length) console.error("  lines without Tamil:", noLine.slice(0, 5));
  process.exit(1);
}
console.log(`web OK: ${words.length} words resolve, ${displayStrings.length} lines get Tamil, escaping and fallbacks verified`);
