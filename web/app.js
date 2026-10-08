// ═════════════════════════════════════════════════════════════════════════════
// Englive Web — a browser-based mirror of the Android app.
// Same content.json + course.json, same LMS flow, same lesson engine logic.
// Uses Web Speech API for TTS/STT (Chrome/Edge/Safari support varies).
// ═════════════════════════════════════════════════════════════════════════════

const CONTENT_URL = "../app/src/main/assets/content.json";
const COURSE_URL  = "../app/src/main/assets/course.json";
const GLOSSARY_URL = "../app/src/main/assets/glossary.json";
const TRANSLATIONS_URL = "../app/src/main/assets/translations.json";
const NOT_COUNTED = new Set(["feedback", "retry_or_progress", "completion"]);
const VERBATIM_MAX = 200;

const state = {
  course: null,
  content: null,
  glossary: null,               // English -> spoken Tamil meaning; null = unavailable
  translations: null,           // English line -> natural Tamil translation
  sectionCache: new Map(),
  progress: JSON.parse(localStorage.getItem("englive_progress") || "{}"),
  ttsSpeed: parseFloat(localStorage.getItem("englive_speed") || "0.9"),
  muted: localStorage.getItem("englive_muted") === "1",
  // Students can hide the Tamil line to test themselves; on by default.
  showTamil: localStorage.getItem("englive_tamil") !== "0",
  route: { name: "home", params: {} },
  session: null,
  sttState: { kind: "idle" },   // idle | listening | result | error | unavailable
  voice: { kind: "idle" },      // idle | recording | recorded | playing | error
};

// ── Persistence ─────────────────────────────────────────────────────────────
function saveProgress() { localStorage.setItem("englive_progress", JSON.stringify(state.progress)); }
function getProgress(day) { return state.progress[day] || null; }
function setProgress(entry) { state.progress[entry.day] = entry; saveProgress(); }

// ── Data loading ────────────────────────────────────────────────────────────
async function loadData() {
  // Cache-bust so iteration on content.json / course.json is instant on reload.
  const bust = Date.now();
  const [c, t, g, tr] = await Promise.all([
    fetch(COURSE_URL + '?v=' + bust).then(r => r.json()),
    fetch(CONTENT_URL + '?v=' + bust).then(r => r.json()),
    // The glossary is optional: a missing/broken file only disables
    // tap-to-translate, it must never block the course from loading.
    fetch(GLOSSARY_URL + '?v=' + bust).then(r => r.json()).catch(() => null),
    // Likewise for whole-line translations; without them the word-by-word
    // gloss still produces a Tamil line.
    fetch(TRANSLATIONS_URL + '?v=' + bust).then(r => r.json()).catch(() => null),
  ]);
  state.course = c;
  state.content = t;
  state.glossary = g && g.entries ? g.entries : null;
  state.translations = tr && tr.strings ? tr.strings : null;
  precomputeSections();
}

// Sections whose long text is meta-commentary rather than teachable content.
// Long text (>200 chars) here is filtered out of lessons and shown as intro
// cards on the module screen instead — keeping the course generator + runtime
// aligned across all modules.
const META_INTRO_SECTIONS = new Set([
  // M1 phrase / prompt sections (short phrases with opening commentary)
  "m1_greetings", "m1_gratitude", "m1_wishes_festive", "m1_wishes_exams",
  "m1_condolences", "m1_farewell", "m1_expressions", "m1_common_q",
  "m1_profession", "m1_casual_talk", "m1_games", "m1_holidays",
  "m1_impression", "m1_political",
  // Pure-orientation sections — all content is intro
  "m2_introduction", "m3_pos_intro", "m5_reading_intro", "m5_letters",
]);

// Only ACTUAL pedagogical commentary counts as intro — phrase blobs like
// "Congratulations! Wish you a happy married life…" or "How do you do? I am
// fine, thank you?" must stay as lessons, not intro-card material.
const _META_MARKERS = [
  "learners","students","this course","necessary that","essential ",
  "imperative that","vocabulary is","pronunciation is","while speaking",
  "in the course of","should not","must be","normally face","formal british",
];
function isMetaIntro(text) {
  if (text.length < 200) return false;
  const low = text.toLowerCase();
  if ((text.match(/\?/g) || []).length >= 3) return false;
  if ((text.match(/!/g) || []).length >= 2) return false;
  if ((low.match(/i am /g) || []).length >= 3) return false;
  if ((low.match(/congratulations/g) || []).length >= 2) return false;
  if ((text.match(/–/g) || []).length >= 5) return false;
  if ((text.match(/—/g) || []).length >= 5) return false;
  return _META_MARKERS.some(m => low.includes(m));
}

function precomputeSections() {
  for (const it of state.content.canonical_items) {
    if (it.type === "heading") continue;
    const arr = state.sectionCache.get(it.section_id) || [];
    arr.push(it);
    state.sectionCache.set(it.section_id, arr);
  }
  for (const [sid, arr] of state.sectionCache) {
    let list = arr.sort((a, b) => a.source_order - b.source_order);
    if (sid === "m1_dialogues") list = list.filter(it => it.type === "dialogue");
    if (META_INTRO_SECTIONS.has(sid)) {
      list = list.filter(it => !(it.type === "text" && isMetaIntro(it.text)));
    }
    state.sectionCache.set(sid, list);
  }
}

function sectionContent(sectionId) { return state.sectionCache.get(sectionId) || []; }

// Intro paragraphs — the meta commentary the phrase sections open with.
// Not lessons; shown as an overview card on the module screen so students
// still get the "why we teach this" context from the book.
function sectionIntros(sectionId) {
  if (!META_INTRO_SECTIONS.has(sectionId)) return [];
  return state.content.canonical_items
    .filter(it => it.section_id === sectionId && it.type === "text" && isMetaIntro(it.text))
    .sort((a, b) => a.source_order - b.source_order);
}

// ── Plan builder (mirrors CourseRepository.plan) ────────────────────────────
function planForDay(dayNumber) {
  const day = state.course.days.find(d => d.day === dayNumber);
  if (!day) return { error: `Lesson day ${dayNumber} is missing` };
  if (day.is_exam) return buildExamPlan(day);
  const source = sectionContent(day.section_id);
  if (!source.length) return { error: `No content for section '${day.section_id}'` };

  const startIdx = state.course.days.filter(d => d.section_id === day.section_id && d.day < day.day).length;
  const item = source[Math.min(startIdx, source.length - 1)];

  const activities = [];
  for (const wire of day.activity_sequence) {
    if (NOT_COUNTED.has(wire)) continue;
    if (wire === "discussion") {
      if (item.turns && item.turns.length) {
        activities.push({ type: "role_play", content: item.title || item.text.split("\n")[0], contentId: item.content_id, turns: item.turns, title: item.title });
      } else {
        activities.push({ type: "discussion", content: item.text, contentId: item.content_id, lines: item.text.split("\n").filter(x => x.trim()) });
      }
      continue;
    }
    activities.push(buildActivity(wire, item));
  }

  return {
    courseId: state.course.course_id,
    day,
    activities,
    requiredScore: state.course.lesson_engine.completion.default_required_score_percent,
  };
}

// Deterministic seeded shuffle for reproducible exam samples.
function seededShuffle(arr, seed) {
  const out = arr.slice();
  let s = seed;
  for (let i = out.length - 1; i > 0; i--) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    const j = s % (i + 1);
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function buildExamPlan(day) {
  const moduleId = day.content_selection.module_id;
  const sampleSize = day.content_selection.sample_size || 10;
  const module = state.content.modules.find(m => m.module_id === moduleId);
  if (!module) return { error: `Module ${moduleId} missing for exam` };
  const pool = module.sections
    .flatMap(s => sectionContent(s.section_id))
    .filter(it => it.text.length >= 20 && it.text.length <= 300 && it.type !== 'dialogue');
  if (!pool.length) return { error: `No exam-eligible items in module ${moduleId}` };
  const questions = seededShuffle(pool, day.day).slice(0, sampleSize);
  const activities = questions.map(it => ({
    type: 'assessment',
    content: it.text,
    contentId: it.content_id,
    expected: it.text,
    threshold: 0.5,       // lenient for rapid recall
  }));
  return {
    courseId: state.course.course_id,
    day,
    activities,
    requiredScore: 60,
  };
}

function buildActivity(wire, item) {
  const short = item.text.length <= VERBATIM_MAX;
  // Always set expected so we can grade against similarity; long content just
  // gets a more forgiving threshold (partial phrasing still passes).
  const expected = item.text;
  const threshold = short ? 0.7 : 0.4;
  const base = { content: item.text, contentId: item.content_id, expected, threshold, parts: item.parts };
  switch (wire) {
    case "teacher_intro":
    case "teach":            return { ...base, type: "read_aloud" };
    case "example":
    case "listen":           return { ...base, type: "listen", expected: null, threshold: null };
    case "guided_practice":
    case "writing":          return { ...base, type: "writing" };
    case "student_response":
    case "speak":            return { ...base, type: "speak" };
    case "listen_repeat":    return { ...base, type: "listen_repeat" };
    case "read_aloud":       return { ...base, type: "read_aloud" };
    case "assessment":       return { ...base, type: "assessment" };
    default:                 return { ...base, type: wire };
  }
}

// ── Lesson engine (mirrors LessonEngine.kt) ─────────────────────────────────
function startSession(dayNumber) {
  const plan = planForDay(dayNumber);
  if (plan.error) { alert(plan.error); return; }
  // A finished lesson is never resumed: retrying restarts from the first
  // activity with a clean score sheet, otherwise one good answer at the end
  // re-passes the whole lesson. Mirrors CourseEngine.start in Kotlin.
  const saved = getProgress(dayNumber);
  const prev = saved && !saved.completed ? saved : null;
  const idx = Math.min(prev?.activityIndex || 0, plan.activities.length - 1);
  state.session = {
    plan,
    activityIndex: Math.max(0, idx),
    attempts: prev?.attempts || 0,
    // Marks already earned are restored so a resumed lesson is not scored only
    // on the activities answered after the resume.
    scores: Array.isArray(saved?.scores) && !saved.completed ? saved.scores.slice() : [],
    status: statusFor(plan.activities[idx]),
    feedback: null,
    recognized: "",
  };
  persistSession();
  render();
}

function statusFor(activity) {
  if (!activity) return "error";
  if (["speak", "listen_repeat", "read_aloud", "role_play", "assessment"].includes(activity.type)) return "waiting";
  return "teaching";
}

function submitAnswer(text) {
  const s = state.session; if (!s) return;
  const a = s.plan.activities[s.activityIndex]; if (!a) return;
  s.attempts++;
  const eval_ = evaluate(text, a.expected, a.threshold);
  // Score = actual similarity (0–100), penalised for retries.
  // Complete gibberish → low score. Perfect match → 100.
  const baseScore = Math.round(eval_.similarity * 100);
  const scr = Math.max(0, baseScore - (s.attempts - 1) * 15);
  s.recognized = eval_.normalized;
  s.feedback = `${eval_.feedback} (${baseScore}% match)`;
  if (eval_.correct) {
    s.scores.push(scr);
    s.status = "correct";
    s._revealed = true;
  } else if (s.attempts < 3) {
    s.status = "retry";
  } else {
    s.scores.push(scr);   // keep partial credit for effort
    s.status = "incorrect";
    s._revealed = true;
  }
  persistSession();
  render();
}

function continueLesson() {
  const s = state.session; if (!s) return;
  if (s.status === "retry") {
    s.status = statusFor(s.plan.activities[s.activityIndex]);
    s.feedback = null;
    s.recognized = "";
  } else {
    advance();
  }
  persistSession();
  render();
}

function previousActivity() {
  stopTTS(); cancelSTT();
  const s = state.session; if (!s) return;
  const target = Math.max(0, s.activityIndex - 1);
  // Drop the scores of the activities we are stepping back over, so answering
  // them again replaces the old mark instead of adding a second entry.
  s.scores = s.scores.slice(0, target);
  s.activityIndex = target;
  s.attempts = 0; s.feedback = null; s.recognized = "";
  s.status = statusFor(s.plan.activities[s.activityIndex]);
  persistSession();
  render();
}

function advance() {
  const s = state.session;
  const next = s.activityIndex + 1;
  if (next >= s.plan.activities.length) {
    const total = s.scores.length ? Math.round(s.scores.reduce((a, b) => a + b, 0) / s.scores.length) : 0;
    s.activityIndex = next;
    s.status = "completed";
    s.totalScore = total;
  } else {
    s.activityIndex = next;
    s.attempts = 0; s.feedback = null; s.recognized = "";
    s._revealed = false;
    s.status = statusFor(s.plan.activities[next]);
  }
}

function exitLesson() {
  stopTTS(); cancelSTT();
  // Drop any in-flight recording or playback with the lesson.
  if (mediaRecorder && mediaRecorder.state !== "inactive") { try { mediaRecorder.stop(); } catch {} }
  if (playbackEl) { playbackEl.pause(); playbackEl = null; }
  state.voice = { kind: "idle" };
  state.session = null;
}

function persistSession() {
  const s = state.session; if (!s) return;
  const done = s.status === "completed";
  const totalScore = done ? s.totalScore : Math.round(s.scores.reduce((a, b) => a + b, 0) / Math.max(1, s.scores.length));
  setProgress({
    day: s.plan.day.day,
    section: s.plan.day.section_id,
    module: s.plan.day.module_id,
    activityIndex: s.activityIndex,
    attempts: s.attempts,
    scores: s.scores,
    score: totalScore,
    completed: done,
    updatedAt: Date.now(),
  });
}

// ── Answer matcher (mirrors AnswerMatcher.kt) ───────────────────────────────
function normalize(s) {
  return s.toLowerCase().trim()
    .replace(/[’‘]/g, "'").replace(/[“”]/g, '"')
    .replace(/\s+/g, " ").replace(/[.!?]+$/, "");
}
function similarity(a, b) {
  if (a === b) return 1; if (!a || !b) return 0;
  const dp = new Array(b.length + 1).fill(0).map((_, i) => i);
  for (let i = 0; i < a.length; i++) {
    let prev = dp[0]; dp[0] = i + 1;
    for (let j = 0; j < b.length; j++) {
      const old = dp[j + 1];
      dp[j + 1] = Math.min(dp[j + 1] + 1, dp[j] + 1, prev + (a[i] === b[j] ? 0 : 1));
      prev = old;
    }
  }
  return 1 - dp[dp.length - 1] / Math.max(a.length, b.length);
}
function evaluate(answer, expected, threshold) {
  const norm = normalize(answer);
  if (!expected) return { correct: true, normalized: norm, similarity: 1.0, feedback: "Response recorded. Continue when ready." };
  const nExp = normalize(expected);
  const sim = norm === nExp ? 1.0 : similarity(norm, nExp);
  const passed = sim >= (threshold ?? 0.7);
  const feedback = passed
    ? (sim >= 0.9 ? "Excellent — that matches the lesson."
      : sim >= 0.7 ? "Well done. Close enough to the lesson."
      : "Good attempt. Try to match the lesson more closely.")
    : "Not quite — that didn't match the lesson. Try again.";
  return { correct: passed, normalized: norm, similarity: sim, feedback };
}

// ── Tap-to-translate (mirrors Glossary.kt) ──────────────────────────────────
// One entry per surface form used in the course, so lookups normally hit
// exactly. The suffix chain below is a safety net for forms the generator may
// have missed; it never guesses by similarity, because a wrong meaning is
// worse for a learner than no meaning.
function normalizeWord(raw) {
  return String(raw).toLowerCase().trim()
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/^[^a-z]+/, "")
    .replace(/[^a-z]+$/, "");
}

function wordCandidates(word) {
  const out = [word];
  const add = w => { if (w && !out.includes(w)) out.push(w); };
  if (word.endsWith("'s") && word.length > 3) add(word.slice(0, -2));
  if (word.endsWith("ies") && word.length > 4) add(word.slice(0, -3) + "y");
  if (word.endsWith("es") && word.length > 4) add(word.slice(0, -2));
  if (word.endsWith("s") && !word.endsWith("ss") && word.length > 3) add(word.slice(0, -1));
  if (word.endsWith("ed") && word.length > 4) { add(word.slice(0, -2)); add(word.slice(0, -1)); }
  if (word.endsWith("ing") && word.length > 5) {
    const stem = word.slice(0, -3);
    add(stem);
    add(stem + "e");
    if (stem.length > 2 && stem[stem.length - 1] === stem[stem.length - 2]) add(stem.slice(0, -1));
  }
  return out;
}

function lookupWord(word) {
  const g = state.glossary;
  if (!g || !word) return null;
  for (const candidate of wordCandidates(word)) {
    if (g[candidate]) return g[candidate];
  }
  return null;
}

// Escapes the text and wraps every known word in a span the delegated click
// handler picks up. Unknown words stay plain text, so a tap never dead-ends.
function linkWords(text) {
  return String(text)
    .split(/([A-Za-z]+(?:['\u2019-][A-Za-z]+)*)/)
    .map((part, i) => {
      if (i % 2 === 1) {
        const word = normalizeWord(part);
        if (lookupWord(word)) {
          return `<span class="w" data-w="${escapeHtml(word)}">${escapeHtml(part)}</span>`;
        }
      }
      return escapeHtml(part);
    })
    .join('');
}

// The Tamil line printed under an English line: the generated whole-line
// translation when there is one, otherwise a word-by-word gloss, so a line is
// never left untranslated. Hidden entirely when the student turns Tamil off.
function tamilLine(text) {
  // Only an explicit "off" hides it: a state object without the flag (an older
  // saved session, a test harness) must not silently lose the Tamil line.
  if (state.showTamil === false) return "";
  const s = String(text == null ? "" : text);
  if (!s.trim()) return "";
  const natural = state.translations && state.translations[s.trim()];
  const tamil = natural || wordGloss(s);
  if (!tamil) return "";
  // A speaker button only when the device actually has a Tamil voice —
  // otherwise an English voice would read Tamil script as gibberish.
  const speaker = tamilVoiceAvailable()
    ? `<button class="ta-speak" data-speak-ta="${escapeHtml(tamil)}" title="Listen in Tamil">🔊</button>`
    : "";
  return `<div class="ta-line">${escapeHtml(tamil)}${speaker}</div>`;
}

let tamilVoiceChecked = false;
function tamilVoiceAvailable() {
  if (!ttsAvailable) return false;
  const voices = window.speechSynthesis.getVoices ? window.speechSynthesis.getVoices() : [];
  if (!voices.length && !tamilVoiceChecked) {
    // The voice list can be empty on first call; re-render once it arrives.
    tamilVoiceChecked = true;
    window.speechSynthesis.onvoiceschanged = () => { tamilVoiceChecked = false; render(); };
    return false;
  }
  return voices.some(v => (v.lang || "").toLowerCase().startsWith("ta"));
}

/** Reads the Tamil line aloud, when a Tamil voice exists. */
function speakTamil(text) {
  if (!ttsAvailable || !text || !text.trim()) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "ta-IN";
  u.rate = 0.9;
  window.speechSynthesis.speak(u);
}

// Word-by-word fallback: known words become Tamil, everything else is kept.
function wordGloss(text) {
  if (!state.glossary) return "";
  let translated = false;
  const out = String(text)
    .split(/([A-Za-z]+(?:['\u2019-][A-Za-z]+)*)/)
    .map((part, i) => {
      if (i % 2 === 1) {
        const meaning = lookupWord(normalizeWord(part));
        if (meaning) { translated = true; return meaning; }
      }
      return part;
    })
    .join("");
  return translated ? out.trim() : "";
}

let wordPopupEl = null;
function showWordPopup(word) {
  const meaning = lookupWord(word);
  if (!meaning) return;
  hideWordPopup();
  const el = document.createElement('div');
  el.className = 'wp-scrim';
  el.innerHTML = `
    <div class="wp-card">
      <div class="wp-head">
        <div>
          <div class="wp-word">${escapeHtml(word)}</div>
          <div class="wp-label">தமிழ் பொருள்</div>
        </div>
        <button class="wp-close" data-wp-close="1">✕</button>
      </div>
      <div class="wp-meaning">${escapeHtml(meaning)}</div>
    </div>`;
  el.addEventListener('click', e => {
    if (e.target === el || (e.target.dataset && e.target.dataset.wpClose)) hideWordPopup();
  });
  document.body.appendChild(el);
  wordPopupEl = el;
}

function hideWordPopup() {
  if (wordPopupEl) { wordPopupEl.remove(); wordPopupEl = null; }
}

function wireWordTap() {
  // Delegated, so no lesson text ever has to be interpolated into an inline
  // handler: text travels in data-* attributes instead, which escapeHtml can
  // safely encode for either quote style.
  document.addEventListener('click', e => {
    const el = e.target.closest ? e.target.closest('[data-speak-ta],[data-speak],.w') : null;
    if (!el) return;
    if (el.dataset.speakTa) { speakTamil(el.dataset.speakTa); return; }
    if (el.dataset.speak) { speakTeacher(el.dataset.speak); return; }
    if (el.dataset.w) showWordPopup(el.dataset.w);
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') hideWordPopup(); });
}

// ── Speech: TTS ─────────────────────────────────────────────────────────────
const ttsAvailable = "speechSynthesis" in window;

// Turn text into something the TTS engine reads naturally. "/" gets read as
// "slash", "etc." as "e t c" — students hear that as noise. Rewrite the
// spoken form only; the displayed text stays exactly what the book has.
function speakableText(text) {
  return text
    .replace(/\betc\.?/gi, "etcetera")
    .replace(/\bEg\./g, "For example,")
    .replace(/\be\.g\./gi, "for example,")
    .replace(/\bi\.e\./gi, "that is,")
    .replace(/\bMr\./g, "Mister")
    .replace(/\bMrs\./g, "Missus")
    .replace(/\bMs\./g, "Miss")
    .replace(/\bDr\./g, "Doctor")
    .replace(/\bSt\./g, "Saint")
    .replace(/\s*\/\s*/g, " or ")
    .replace(/\s*—\s*/g, ", ")     // em dash → comma pause
    .replace(/\s*–\s*/g, ", ")     // en dash → comma pause
    .replace(/\s+/g, " ")
    .trim();
}

function speakTeacher(text) {
  if (!ttsAvailable || state.muted || !text || !text.trim()) return;
  window.speechSynthesis.cancel();
  const spoken = speakableText(text);
  // Chunk on sentences so long m4 passages don't get truncated (~200-char safe)
  const chunks = spoken.match(/[^.!?\n]+[.!?\n]?|\S+/g) || [spoken];
  for (const chunk of chunks) {
    const u = new SpeechSynthesisUtterance(chunk.trim());
    u.rate = state.ttsSpeed;
    u.pitch = 1;
    u.lang = "en-IN";
    window.speechSynthesis.speak(u);
  }
}
function stopTTS() { if (ttsAvailable) window.speechSynthesis.cancel(); }

// ── Speech: STT ─────────────────────────────────────────────────────────────
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;
function startSTT(onResult) {
  if (!SR) { state.sttState = { kind: "unavailable" }; render(); return; }
  cancelSTT();
  try {
    recognizer = new SR();
    recognizer.lang = "en-IN";
    recognizer.continuous = false;
    recognizer.interimResults = false;
    recognizer.onresult = e => {
      const t = e.results[0][0].transcript;
      state.sttState = { kind: "result", text: t };
      recognizer = null;
      onResult(t);
      render();
    };
    recognizer.onerror = e => {
      state.sttState = { kind: "error", message: e.error };
      recognizer = null;
      render();
    };
    recognizer.onend = () => { if (state.sttState.kind === "listening") { state.sttState = { kind: "idle" }; render(); } };
    state.sttState = { kind: "listening" };
    recognizer.start();
    render();
  } catch (e) {
    state.sttState = { kind: "error", message: e.message };
    render();
  }
}
function cancelSTT() { if (recognizer) { try { recognizer.abort(); } catch {} recognizer = null; } state.sttState = { kind: "idle" }; }

// ── Record and compare ──────────────────────────────────────────────────────
// A shadowing tool, separate from the scored attempt: the microphone is held by
// either the recogniser or the recorder, never both, so this records, plays
// back, and lets the student compare with the teacher. Nothing here is scored.
let mediaRecorder = null;
let recordedChunks = [];
let recordedUrl = null;
let playbackEl = null;

async function startRecording() {
  if (!navigator.mediaDevices || !window.MediaRecorder) {
    state.voice = { kind: "error", message: "Recording is not supported in this browser." };
    render();
    return;
  }
  cancelSTT(); stopTTS();
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => { if (e.data && e.data.size) recordedChunks.push(e.data); };
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || "audio/webm" });
      if (recordedUrl) URL.revokeObjectURL(recordedUrl);
      recordedUrl = URL.createObjectURL(blob);
      state.voice = { kind: "recorded" };
      render();
    };
    mediaRecorder.start();
    state.voice = { kind: "recording" };
  } catch (e) {
    state.voice = { kind: "error", message: "Microphone permission is needed to record." };
  }
  render();
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
}

function playRecording() {
  if (!recordedUrl) return;
  stopTTS();
  playbackEl = new Audio(recordedUrl);
  playbackEl.onended = () => { state.voice = { kind: "recorded" }; render(); };
  playbackEl.play();
  state.voice = { kind: "playing" };
  render();
}

function stopVoice() {
  if (state.voice.kind === "recording") { stopRecording(); return; }
  if (playbackEl) { playbackEl.pause(); playbackEl = null; }
  state.voice = recordedUrl ? { kind: "recorded" } : { kind: "idle" };
  render();
}

function renderVoicePractice() {
  const v = state.voice || { kind: "idle" };
  let buttons;
  if (v.kind === "recording") {
    buttons = `<button class="btn-retry" onclick="stopRecording()">⏹ Stop recording</button>`;
  } else if (v.kind === "playing") {
    buttons = `<button class="btn-skip" onclick="stopVoice()">⏹ Stop</button>`;
  } else if (v.kind === "recorded") {
    buttons = `<button class="btn-continue" onclick="playRecording()">▶️ Play my voice</button>
               <button class="btn-skip" onclick="startRecording()">Record again</button>`;
  } else {
    buttons = `<button class="btn-continue" onclick="startRecording()">🎤 Record yourself</button>`;
  }
  const err = v.kind === "error"
    ? `<div style="font-size:11px;color:#C62828;margin-top:6px">${escapeHtml(v.message)}</div>` : "";
  return `<div class="card" style="background:#F3E5F5">
    <div style="font-weight:600;font-size:13px">🎤 Your turn — record and compare</div>
    <div style="font-size:11px;color:var(--muted-2);margin:4px 0 8px">Say it yourself, then listen back and compare with the teacher. Nothing here is scored.</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">${buttons}</div>${err}
  </div>`;
}

// ── Router ──────────────────────────────────────────────────────────────────
function goto(name, params = {}) { state.route = { name, params }; render(); }

// ── Render ──────────────────────────────────────────────────────────────────
const $app = document.getElementById("app");
function render() {
  if (!state.course || !state.content) { $app.innerHTML = `<div class="loading">Loading course…</div>`; return; }
  if (state.session && state.session.status === "completed") return renderResult();
  if (state.session) return renderTeacher();
  switch (state.route.name) {
    case "overview": return renderOverview();
    case "module":   return renderModule();
    case "progress": return renderProgressScreen();
    case "settings": return renderSettings();
    default:         return renderHome();
  }
}

function bottomNav(active) {
  return `
    <div class="bottom-nav">
      <div class="nav-item ${active === 'home' ? 'active' : ''}" onclick="goto('home')"><span class="ni">🏠</span>Home</div>
      <div class="nav-item ${active === 'lessons' ? 'active' : ''}" onclick="goto('overview')"><span class="ni">📖</span>Lessons</div>
      <div class="nav-item ${active === 'progress' ? 'active' : ''}" onclick="goto('progress')"><span class="ni">📊</span>Progress</div>
      <div class="nav-item ${active === 'settings' ? 'active' : ''}" onclick="goto('settings')"><span class="ni">⚙️</span>Settings</div>
    </div>`;
}

function renderHome() {
  const total = state.course.days.length;
  $app.innerHTML = `
    <div class="screen">
      <div class="hero">
        <div class="emoji">📚</div>
        <h1>${state.course.course_title}</h1>
        <div class="tag">Teacher-led · Offline-first · ${total} lessons</div>
      </div>
      <div class="body pad0">
        <div class="feature-grid">
          <div class="feature-card"><div class="fe">🎤</div><div class="ft">Speak</div><div class="fd">Practice aloud with speech recognition</div></div>
          <div class="feature-card"><div class="fe">🧑‍🏫</div><div class="ft">Teacher</div><div class="fd">Step-by-step guided learning</div></div>
          <div class="feature-card"><div class="fe">📶</div><div class="ft">Offline</div><div class="fd">Content bundled — no network needed</div></div>
          <div class="feature-card"><div class="fe">📊</div><div class="ft">Tracked</div><div class="fd">Progress saved in browser</div></div>
        </div>
        <button class="big-btn" onclick="goto('overview')">▶ Start Learning</button>
      </div>
      ${bottomNav('home')}
    </div>`;
}

function renderOverview() {
  const days = state.course.days;
  const done = Object.values(state.progress).filter(p => p.completed).length;
  const pct = Math.round(done * 100 / Math.max(1, days.length));
  const modules = state.content.modules.map((m, i) => {
    const modDays = days.filter(d => d.module_id === m.module_id);
    const modDone = modDays.filter(d => getProgress(d.day)?.completed).length;
    const modPct = modDays.length ? Math.round(modDone * 100 / modDays.length) : 0;
    const emoji = ["💬","📖","✏️","📝","🖊️"][i] || "📚";
    return `
      <div class="card clickable" onclick="goto('module',{module:'${m.module_id}'})">
        <div class="module-card ${modPct === 100 ? 'done' : ''}">
          <div class="icon-box">${emoji}</div>
          <div class="info">
            <div class="name">MODULE ${i+1}: ${m.title}</div>
            <div class="stat ${modPct === 100 ? 'ok' : ''}">${modDone}/${modDays.length} lessons · ${modPct}%</div>
            <div class="bar thin" style="margin-top:6px"><div class="fill" style="width:${modPct}%"></div></div>
          </div>
          <div class="chevron">›</div>
        </div>
      </div>`;
  }).join("");
  $app.innerHTML = `
    <div class="screen">
      <div class="topbar">
        <button class="back" onclick="goto('home')">←</button>
        <div class="title">Course Overview<div class="subtitle">${state.content.modules.length} Modules · ${days.length} Lessons</div></div>
      </div>
      <div class="body">
        <div class="card overall-card">
          <div class="row"><b>Overall Progress</b><span class="pct">${pct}%</span></div>
          <div class="bar"><div class="fill" style="width:${pct}%"></div></div>
          <div class="stat" style="font-size:11px;color:var(--muted-2)">${done} of ${days.length} lessons completed</div>
        </div>
        ${modules}
      </div>
      ${bottomNav('lessons')}
    </div>`;
}

function renderModule() {
  const mid = state.route.params.module;
  const mod = state.content.modules.find(m => m.module_id === mid);
  if (!mod) { goto('overview'); return; }
  const modDays = state.course.days.filter(d => d.module_id === mid);
  const bySection = new Map();
  for (const d of modDays) { (bySection.get(d.section_id) || bySection.set(d.section_id, []).get(d.section_id)).push(d); }
  const html = mod.sections.map(sec => {
    const secDays = (bySection.get(sec.section_id) || []).filter(d => !d.is_exam);
    const intros = sectionIntros(sec.section_id);
    // Show the section if it has either lessons or intros
    if (!secDays.length && !intros.length) return "";
    const rows = secDays.map((d, i) => {
      const p = getProgress(d.day);
      const activityCount = d.activity_sequence.filter(w => !NOT_COUNTED.has(w)).length || 1;
      const done = p?.completed;
      const idx = p?.activityIndex || 0;
      const stat = done ? `Score: ${p.score}%`
                       : (p ? `Activity ${idx} of ${activityCount}` : `${activityCount} activities · not started`);
      const barPct = done ? 100 : Math.min(100, Math.round(idx * 100 / activityCount));
      const name = secDays.length > 1 ? `Lesson ${i + 1} of ${secDays.length}` : sec.title;
      return `
        <div class="card clickable" onclick="startSession(${d.day})">
          <div class="lesson-card ${done ? 'done' : ''}">
            <div class="day-badge">${done ? '✓' : i + 1}</div>
            <div class="info">
              <div class="name">${escapeHtml(name)}</div>
              <div class="stat ${done ? 'ok' : ''}">${stat}</div>
              ${p && !done ? `<div class="bar thin" style="margin-top:6px"><div class="fill" style="width:${barPct}%"></div></div>` : ''}
            </div>
          </div>
        </div>`;
    }).join("");
    const introCard = intros.length ? `
      <div class="intro-card">
        <div class="intro-hdr">📖 Why this section</div>
        ${intros.map(it => `<div class="intro-para">${linkWords(it.text)}${tamilLine(it.text)}</div>`).join('')}
        <button class="intro-listen" data-speak="${escapeHtml(intros.map(i => i.text).join(" "))}">🔊 Listen to this</button>
      </div>` : '';
    return `<div class="section-hdr">${sec.title}</div>${introCard}${rows}`;
  }).join("");

  // Module final exam — locked until all regular lessons are done
  const examDay = modDays.find(d => d.is_exam);
  let examCard = "";
  if (examDay) {
    const regular = modDays.filter(d => !d.is_exam);
    const doneCount = regular.filter(d => getProgress(d.day)?.completed).length;
    const remaining = regular.length - doneCount;
    const unlocked = regular.length > 0 && remaining === 0;
    const exProg = getProgress(examDay.day);
    const examScore = exProg?.score || 0;
    const passed = exProg?.completed && examScore >= 60;
    const emoji = !unlocked ? '🔒' : passed ? '🏆' : (exProg?.completed ? '🔁' : '📝');
    const bg = !unlocked ? '#ECEFF1' : passed ? '#E8F5E9' : (exProg?.completed ? '#FFEBEE' : '#FFF3D6');
    const stat = !unlocked
      ? `Complete ${remaining} more lesson${remaining === 1 ? '' : 's'} to unlock`
      : passed
        ? `Passed · Score ${examScore}% · Retake anytime`
        : exProg?.completed
          ? `Score ${examScore}% · Below 60% — retake to pass`
          : `10 questions · Pass at 60%`;
    examCard = `
      <div class="exam-card ${unlocked ? 'clickable' : ''}"
           style="background:${bg}"
           ${unlocked ? `onclick="startSession(${examDay.day})"` : ''}>
        <div class="exam-emoji">${emoji}</div>
        <div class="exam-info">
          <div class="exam-title">${escapeHtml(examDay.lesson_title)}</div>
          <div class="exam-stat">${stat}</div>
        </div>
        ${unlocked ? '<div class="chevron">›</div>' : ''}
      </div>`;
  }

  const lessonCount = modDays.filter(d => !d.is_exam).length;
  const examLabel = examDay ? ' · 1 exam' : '';
  $app.innerHTML = `
    <div class="screen">
      <div class="topbar">
        <button class="back" onclick="goto('overview')">←</button>
        <div class="title">${mod.title}<div class="subtitle">${lessonCount} lessons${examLabel}</div></div>
      </div>
      <div class="body">${html}${examCard}</div>
      ${bottomNav('lessons')}
    </div>`;
}

// ── Lesson (Teacher / RolePlay) ─────────────────────────────────────────────
// Render structured content parts (blocks / questions / table) when the
// content.json item carries a `parts` field, else fall back to plain text.
function renderPartsOrText(a) {
  const p = a?.parts;
  if (!p) return `${linkWords(a?.content || 'No content')}${tamilLine(a?.content || '')}`;
  if (p.kind === 'blocks') return renderBlocks(p.blocks);
  if (p.kind === 'questions') return renderQuestions(p.questions);
  if (p.kind === 'table') return renderTable(p.rows);
  if (p.kind === 'phrase') return renderPhraseCard(p.context, p.phrase);
  return `${linkWords(a.content)}${tamilLine(a.content)}`;
}

function renderPhraseCard(context, phrase) {
  return `
    <div class="phr-context">💡 ${linkWords(context)}${tamilLine(context)}</div>
    <div class="phr-card">
      <div class="phr-label">🗣 SAY THIS</div>
      <div class="phr-text">"${linkWords(phrase)}"</div>
      ${tamilLine(phrase)}
    </div>`;
}

function renderBlocks(blocks) {
  const label = {
    rule:      { icon: '📘', label: 'Rule',       cls: 'blk-rule' },
    example:   { icon: '📖', label: 'Example',    cls: 'blk-example' },
    exception: { icon: '⚠',  label: 'Exception',  cls: 'blk-exception' },
    note:      { icon: '💡', label: 'Note',       cls: 'blk-note' },
    body:      { icon: '',   label: '',           cls: 'blk-body' },
  };
  return blocks.map(b => {
    const meta = label[b.kind] || label.body;
    const header = meta.label ? `<div class="blk-hdr">${meta.icon} ${meta.label}</div>` : '';
    return `<div class="blk ${meta.cls}">${header}<div class="blk-txt">${linkWords(b.text)}${tamilLine(b.text)}</div></div>`;
  }).join('');
}

function renderQuestions(questions) {
  return `<div class="qa-list">` + questions.map((q, i) => {
    const answer = q.a ? `<div class="qa-a"><span class="qa-label">A</span> ${linkWords(q.a)}${tamilLine(q.a)}</div>` : '';
    return `<div class="qa-item"><div class="qa-q"><span class="qa-label q">Q${i+1}</span> ${linkWords(q.q)}${tamilLine(q.q)}</div>${answer}</div>`;
  }).join('') + `</div>`;
}

function renderTable(rows) {
  if (!rows.length) return '';
  const header = rows[0];
  const body = rows.slice(1);
  return `<table class="content-table">
    <thead><tr>${header.map(h => `<th>${linkWords(h)}</th>`).join('')}</tr></thead>
    <tbody>${body.map(r => `<tr>${r.map(c => `<td>${linkWords(c)}</td>`).join('')}</tr>`).join('')}</tbody>
  </table>`;
}

function activityInstruction(type, isRecall) {
  if (isRecall) {
    return `<div class="instr">🧠 <b>Say it from memory.</b> Tap 👁 Peek if you need a hint. The teacher won't read it out this time.</div>`;
  }
  const map = {
    listen:        `<div class="instr">🔊 <b>Listen carefully.</b> The teacher will read this to you — just observe.</div>`,
    listen_repeat: `<div class="instr">🎙 <b>Repeat after the teacher.</b> Tap the mic and say what you just heard.</div>`,
    read_aloud:    `<div class="instr">📖 <b>Read this aloud yourself.</b> Tap the mic and speak the passage clearly.</div>`,
    speak:         `<div class="instr">💬 <b>Speak on this topic.</b> Use the prompt as your starting point.</div>`,
    writing:       `<div class="instr">✏ <b>Type your answer.</b></div>`,
    assessment:    `<div class="instr">🧪 <b>Final check.</b> Speak the phrase or answer to complete this lesson.</div>`,
    teach:         `<div class="instr">📚 <b>Learn this rule.</b> Read it once, then say it back.</div>`,
  };
  return map[type] || "";
}

function activityChip(type) {
  const map = {
    listen:        ["🔊 Listen", "listen"],
    listen_repeat: ["🔊 Listen", "listen"],
    read_aloud:    ["🎙 Read Aloud", "read"],
    speak:         ["🎤 Speak", "speak"],
    writing:       ["✏ Write", "write"],
    assessment:    ["🧪 Assessment", "assess"],
    discussion:    ["💬 Discussion", "dis"],
    role_play:     ["🎭 Role Play", "role"],
    teach:         ["📚 Teach", "teach"],
  };
  const [label, cls] = map[type] || [type, "listen"];
  return `<div class="chip ${cls}">${label}</div>`;
}

function renderTeacher() {
  const s = state.session;
  const a = s.plan.activities[s.activityIndex];
  const day = s.plan.day;
  const totalAct = s.plan.activities.length;
  const barPct = Math.min(100, Math.round(s.activityIndex * 100 / totalAct));

  if (a && a.type === "role_play") return renderRolePlay(s, a);

  // Auto-speak teacher content once per activity — but only for teach/practice
  // phases where the student is expected to hear the content. In the recall
  // phase (speak / assessment on short items) we stay silent so the student
  // works from memory instead.
  const isShort = a && a.content.length <= VERBATIM_MAX;
  const isRecall = a && (a.type === "speak" || a.type === "assessment") && isShort;
  if (a && s._lastSpoken !== s.activityIndex) {
    s._lastSpoken = s.activityIndex;
    if (!isRecall) setTimeout(() => speakTeacher(a.content), 100);
  }

  const canType = a && a.type === "writing";
  const isSpeaking = a && ["speak","listen_repeat","read_aloud","role_play","assessment"].includes(a.type);
  const answered = ["correct","incorrect"].includes(s.status);

  const fb = s.feedback ? renderFeedback(s, a) : "";
  const inp = canType ? `<textarea class="answer-input" id="answer-input" placeholder="Your response"></textarea>` : "";
  const stt = renderSttRow();
  const instr = activityInstruction(a?.type, isRecall);

  $app.innerHTML = `
    <div class="screen">
      <div class="topbar">
        <button class="back" onclick="if(s.activityIndex>0){previousActivity()}else{exitLesson();goto('module',{module:'${day.module_id}'})}">←</button>
        <div class="title">${escapeHtml(day.lesson_title)}<div class="subtitle">${s.activityIndex+1} of ${totalAct} activities</div></div>
        ${s.scores.length ? `<span class="badge">${avg(s.scores)}%</span>` : ''}
        <button class="mute-btn ${state.showTamil ? '' : 'muted'}" onclick="toggleTamil()" title="${state.showTamil ? 'Hide' : 'Show'} Tamil meaning">த</button>
        <button class="mute-btn ${state.muted ? 'muted' : ''}" onclick="toggleMute()">${state.muted ? '🔇' : '🔊'}</button>
      </div>
      <div class="progress-strip"><div class="fill" style="width:${barPct}%"></div></div>
      <div class="body">
        ${activityChip(a?.type || "listen")}
        ${instr}
        <div class="teacher-bubble">
          <div class="avatar">🧑‍🏫</div>
          <div class="bubble ${isRecall && !s._revealed ? 'blur' : ''}">
            <div class="who">Teacher · ${escapeHtml(day.lesson_title)}</div>
            ${isRecall && !s._revealed ? `<button class="peek-btn" onclick="s._revealed=true;render()">👁 Peek</button>` : ''}
            <div class="content-body">${renderPartsOrText(a)}</div>
            <button class="replay-btn" data-speak="${escapeHtml(a?.content || '')}">🔊 Replay</button>
            <div class="wp-hint">💡 Tamil meaning is shown under each line</div>
          </div>
        </div>
        ${fb}
        <div class="stt-row ${state.sttState.kind === 'listening' ? 'listening' : state.sttState.kind === 'result' ? 'result' : ''}">${stt}</div>
        ${renderVoicePractice()}
        ${inp}
      </div>
      ${renderActionBar(s, a, isSpeaking, canType, answered)}
    </div>`;
  // Store the exit-back binding
  window.s = s;
}

function renderRolePlay(s, a) {
  const turns = a.turns;
  s._turnIdx = s._turnIdx ?? 0;
  const speakers = [...new Set(turns.map(t => t.speaker))];
  const tSpeaker = speakers[0] || "Speaker 1";
  const uSpeaker = speakers[1] || "Speaker 2";
  const curr = turns[s._turnIdx];
  const isTeacherTurn = curr && curr.speaker === tSpeaker;

  if (curr && s._lastSpoken !== `${s.activityIndex}-${s._turnIdx}`) {
    s._lastSpoken = `${s.activityIndex}-${s._turnIdx}`;
    if (isTeacherTurn) setTimeout(() => speakTeacher(curr.text), 100);
  }

  const bubbles = turns.slice(0, Math.min(s._turnIdx + 1, turns.length)).map((t, i) => {
    const isT = t.speaker === tSpeaker;
    const badge = roleBadge(t.role);
    return `
      <div class="turn-row ${isT ? 'teacher' : 'student'}">
        <div class="avatar ${isT ? '' : 'student'}">${isT ? '🧑‍🏫' : '🙋'}</div>
        <div class="bubble">
          <div class="who">${t.speaker}${badge}</div>
          ${linkWords(t.text)}${tamilLine(t.text)}
        </div>
      </div>`;
  }).join("");

  const bar = s._turnIdx < turns.length ? (
    isTeacherTurn
      ? `<button class="btn-continue" onclick="s._turnIdx++;render()">Next →</button>`
      : `<button class="btn-mic" onclick="startSTT(t=>{s._turnIdx++})">🎤 Speak as ${uSpeaker}</button>
         <button class="btn-skip" onclick="s._turnIdx++;render()">Skip</button>`
  ) : `<button class="btn-continue" onclick="advance();persistSession();render()">Done ✓</button>`;

  $app.innerHTML = `
    <div class="screen">
      <div class="topbar">
        <button class="back" onclick="if(s.activityIndex>0){previousActivity()}else{exitLesson();goto('module',{module:'${s.plan.day.module_id}'})}">←</button>
        <div class="title">${a.title || 'Role Play'}<div class="subtitle">Turn ${Math.min(s._turnIdx + 1, turns.length)} of ${turns.length}</div></div>
        <button class="mute-btn ${state.showTamil ? '' : 'muted'}" onclick="toggleTamil()" title="${state.showTamil ? 'Hide' : 'Show'} Tamil meaning">த</button>
        <button class="mute-btn ${state.muted ? 'muted' : ''}" onclick="toggleMute()">${state.muted ? '🔇' : '🔊'}</button>
      </div>
      <div class="card" style="margin:8px 12px">
        <div style="display:flex;gap:16px;font-size:12px">
          <div>🧑‍🏫 Teacher plays <b style="color:var(--primary)">${tSpeaker}</b></div>
          <div>🙋 You play <b style="color:var(--success)">${uSpeaker}</b></div>
        </div>
      </div>
      <div class="body">${bubbles}</div>
      <div class="action-bar">${bar}</div>
    </div>`;
  window.s = s;
}

function roleBadge(role) {
  const m = {
    question: ["?", "question"], request: ["Request", "request"], greeting: ["Greeting", "greeting"],
    acknowledgment: ["Reply", "ack"], stage_direction: ["Action", "action"],
  }[role];
  return m ? `<span class="role-badge role-${m[1]}">${m[0]}</span>` : "";
}

function renderFeedback(s, a) {
  // Tier by actual score rather than binary correct/incorrect.
  const score = s.scores.at(-1) ?? -1;
  let cls, title;
  if (s.status === "incorrect")     { cls = "err";  title = "Not quite"; }
  else if (score >= 90)             { cls = "ok";   title = "Excellent!"; }
  else if (score >= 70)             { cls = "ok";   title = "Well done"; }
  else if (score >= 40)             { cls = "info"; title = "Attempted"; }
  else if (score >= 0)              { cls = "err";  title = "Try harder"; }
  else                              { cls = "info"; title = "Feedback"; }
  const diff = (a && a.expected && s.recognized && (s.status === "correct" || s.status === "incorrect"))
    ? wordDiffHtml(a.expected, s.recognized)
    : "";
  return `<div class="feedback ${cls}"><b>${title}</b> — ${escapeHtml(s.feedback)}${score >= 0 ? ` · Score: ${score}` : ''}${diff}</div>`;
}

// Word-level pronunciation feedback, mirroring AnswerDiff.kt: the expected text
// with heard words in green and missed words underlined in red, so the student
// can see which word to work on rather than just a percentage.
function compareWords(expected, heard) {
  const tokenize = t => String(t).split(/\s+/).filter(Boolean);
  const norm = t => t.toLowerCase().replace(/[\u2018\u2019]/g, "'").replace(/^[^a-z0-9]+/, "").replace(/[^a-z0-9]+$/, "");
  const exp = tokenize(expected);
  const got = tokenize(heard);
  const a = exp.map(norm), b = got.map(norm);

  const dp = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const heardFlag = new Array(exp.length).fill(false);
  const matched = new Array(got.length).fill(false);
  let i = 0, j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { heardFlag[i] = true; matched[j] = true; i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) i++;
    else j++;
  }
  return {
    words: exp.map((text, k) => ({ text, heard: heardFlag[k] })),
    missed: exp.filter((_, k) => !heardFlag[k]).map(norm).filter((v, k, arr) => arr.indexOf(v) === k),
  };
}

function wordDiffHtml(expected, heard) {
  const diff = compareWords(expected, heard);
  if (diff.words.length < 2) return "";
  const body = diff.words
    .map(w => `<span class="${w.heard ? "wd-heard" : "wd-missed"}">${escapeHtml(w.text)}</span>`)
    .join(" ");
  const summary = diff.missed.length === 0
    ? `<div class="wd-sum ok">Every word was recognised ✓</div>`
    : `<div class="wd-sum">Not heard: ${escapeHtml(diff.missed.slice(0, 6).join(", "))}</div>`;
  return `<div class="wd"><div class="wd-title">🎯 Heard word by word</div><div class="wd-body">${body}</div>${summary}</div>`;
}

function renderSttRow() {
  const st = state.sttState;
  if (st.kind === "listening") return "🎧 Listening…";
  if (st.kind === "result") return `You said: "${escapeHtml(st.text)}"`;
  if (st.kind === "error") return `⚠️ ${st.message}`;
  if (st.kind === "unavailable") return "⚠️ Speech recognition not available in this browser (try Chrome/Edge).";
  return "";
}

function renderActionBar(s, a, isSpeaking, canType, answered) {
  const parts = [];
  if (!answered && isSpeaking) {
    parts.push(`<button class="btn-mic" onclick="startSTT(t=>submitAnswer(t))">🎤 Speak</button>`);
  } else if (!answered && canType) {
    parts.push(`<button class="btn-check" onclick="submitAnswer(document.getElementById('answer-input').value)">Check</button>`);
  } else if (!answered && a?.type === "listen") {
    parts.push(`<button class="btn-continue" onclick="continueLesson()">I heard it ✓</button>`);
    return `<div class="action-bar">${parts.join('')}</div>`;
  }
  let contLabel = "Continue", contCls = "btn-continue";
  if (s.status === "retry") { contLabel = "Retry"; contCls = "btn-retry"; }
  else if (s.status === "correct") { contLabel = "Continue ✓"; contCls = "btn-continue"; }
  else if (s.status === "incorrect") { contLabel = "Next →"; contCls = "btn-next"; }
  parts.push(`<button class="${contCls}" onclick="continueLesson()">${contLabel}</button>`);
  return `<div class="action-bar">${parts.join("")}</div>`;
}

function avg(arr) { return arr.length ? Math.round(arr.reduce((a,b)=>a+b,0)/arr.length) : 0; }

// ── Result / Progress / Settings ────────────────────────────────────────────
function renderResult() {
  const s = state.session;
  const passed = s.totalScore >= s.plan.requiredScore;
  const day = s.plan.day;
  $app.innerHTML = `
    <div class="screen">
      <div class="body">
        <div class="result">
          <div style="font-size:56px">${passed ? '🎉' : '📖'}</div>
          <h2 style="color:${passed?'var(--success)':'var(--accent)'}">${passed ? 'Lesson Complete!' : 'Keep Practising!'}</h2>
          <div style="color:var(--muted)">${escapeHtml(day.lesson_title)}</div>
          <div class="badge ${passed?'':'fail'}">
            <div class="score">${s.totalScore}%</div>
            <div class="label">${passed?'PASSED':'TRY AGAIN'}</div>
          </div>
          <div style="font-size:12px;color:var(--muted-2)">Required: ${s.plan.requiredScore}% — ${passed?'You passed ✓':`Score ${s.totalScore}% — Try again`}</div>
        </div>
      </div>
      <div class="action-bar">
        ${!passed ? `<button class="btn-retry" onclick="startSession(${day.day})">🔁 Retry</button>`:''}
        <button class="btn-continue" onclick="exitLesson();goto('module',{module:'${day.module_id}'})">Back to Module</button>
      </div>
    </div>`;
}

function renderProgressScreen() {
  const total = state.course.days.length;
  const list = Object.values(state.progress).sort((a,b)=>a.day-b.day);
  const done = list.filter(p=>p.completed).length;
  const passMark = state.course.lesson_engine?.completion?.default_required_score_percent ?? 80;
  // Revision queue: started but not passed, weakest first.
  const revision = list.map(p => {
      const d = state.course.days.find(x => x.day === p.day);
      if (!d) return null;
      const required = d.is_exam ? 60 : passMark;
      return (!p.completed || p.score < required) ? { p, d, required } : null;
    })
    .filter(Boolean)
    .sort((a, b) => (a.p.completed - b.p.completed) || (a.p.score - b.p.score))
    .slice(0, 5);
  const revisionCard = revision.length ? `
    <div class="card" style="background:#FFF8E1">
      <div style="font-weight:bold">🔁 Revise next</div>
      <div style="font-size:11px;color:var(--muted-2);margin-bottom:8px">Lessons you started but have not passed yet.</div>
      ${revision.map(({ p, d, required }) => `
        <div class="revise-row">
          <div class="info">
            <div class="name">${escapeHtml(d.lesson_title)}</div>
            <div class="stat">${!p.completed ? `Not finished · ${p.score}% so far` : `${p.score}% · needs ${required}%`}</div>
          </div>
          <button class="btn-continue" style="padding:6px 12px;font-size:12px" onclick="startSession(${d.day})">Practice</button>
        </div>`).join('')}
    </div>` : "";
  const rows = list.map(p => {
    const d = state.course.days.find(x=>x.day===p.day);
    const acts = d ? d.activity_sequence.filter(w=>!NOT_COUNTED.has(w)).length : 1;
    const name = d ? d.lesson_title : `Lesson ${p.day}`;
    return `<div class="card"><div class="progress-row">
      <div class="day-box ${p.completed?'done':'pending'}">${p.completed?'✓':p.day}</div>
      <div class="info"><div class="name">${escapeHtml(name)}</div>
        <div class="stat">${p.completed?`Completed · ${p.score}%`:`Activity ${p.activityIndex} of ${acts}`}</div>
      </div>
      ${p.completed?`<div class="score" style="color:var(--success)">${p.score}%</div>`:''}
    </div></div>`;
  }).join("");
  $app.innerHTML = `
    <div class="screen">
      <div class="topbar" style="background:white;color:#222"><div class="title" style="color:#222">My Progress<div class="subtitle" style="color:var(--muted-2)">${done} of ${total} lessons</div></div></div>
      <div class="body">
        ${revisionCard}
        <div class="card overall-card"><div class="row"><b>Overall</b><span class="pct">${Math.round(done*100/Math.max(1,total))}%</span></div>
          <div class="bar"><div class="fill" style="width:${done*100/Math.max(1,total)}%"></div></div></div>
        ${rows || '<div style="text-align:center;color:var(--muted-2);padding:40px">No lessons started yet.</div>'}
      </div>
      ${bottomNav('progress')}
    </div>`;
}

function renderSettings() {
  $app.innerHTML = `
    <div class="screen">
      <div class="topbar" style="background:white;color:#222"><div class="title" style="color:#222">Settings</div></div>
      <div class="body">
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div><b>Teacher Voice Speed</b><div style="font-size:11px;color:var(--muted)">How fast the teacher speaks</div></div>
            <span class="badge" style="background:var(--pill);color:var(--primary);padding:4px 8px;border-radius:6px;font-size:12px;font-weight:bold">${state.ttsSpeed.toFixed(1)}×</span>
          </div>
          <input type="range" min="0.5" max="1.5" step="0.1" value="${state.ttsSpeed}" style="width:100%;margin-top:8px"
            oninput="state.ttsSpeed=parseFloat(this.value);localStorage.setItem('englive_speed',state.ttsSpeed);render()">
        </div>
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div><b>Tamil meaning</b><div style="font-size:11px;color:var(--muted)">Show the Tamil translation under each English line</div></div>
            <button style="border:0;cursor:pointer;background:${state.showTamil ? 'var(--success)' : 'var(--pill)'};color:${state.showTamil ? 'white' : 'var(--primary)'};padding:6px 10px;border-radius:6px;font-size:12px;font-weight:bold"
              onclick="toggleTamil()">${state.showTamil ? 'ON' : 'OFF'}</button>
          </div>
        </div>
        <div class="card">
          <button class="big-btn muted" style="margin:0;width:100%" onclick="if(confirm('Clear all local progress?')){localStorage.removeItem('englive_progress');state.progress={};render()}">Clear Progress</button>
        </div>
        <div style="text-align:center;padding:20px;color:var(--muted-2);font-size:12px">Web version · Fed by content.json + course.json</div>
      </div>
      ${bottomNav('settings')}
    </div>`;
}

function toggleMute() { state.muted = !state.muted; localStorage.setItem("englive_muted", state.muted?"1":"0"); if (state.muted) stopTTS(); render(); }
function toggleTamil() { state.showTamil = !state.showTamil; localStorage.setItem("englive_tamil", state.showTamil ? "1" : "0"); render(); }

// ── Utility ──────────────────────────────────────────────────────────────────
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }

// ── Boot ─────────────────────────────────────────────────────────────────────
wireWordTap();
loadData().then(render).catch(e => { $app.innerHTML = `<div class="loading">Load error: ${e.message}<br><br>Run <code>python3 -m http.server 8000</code> from the project root then open <code>http://localhost:8000/web/</code></div>`; });
