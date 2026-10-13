"""Exact Python replica of CourseContent.sectionContent / sectionIntros / plan binding.

Used only to review the shipped lesson+chapter structure. Reads assets, writes
a UTF-8 report to review.md (no asset is modified).
"""
import json
import sys
from collections import Counter, defaultdict

ROOT = "app/src/main/assets"
course = json.load(open(f"{ROOT}/course.json", encoding="utf-8"))
content = json.load(open(f"{ROOT}/content.json", encoding="utf-8"))

META_INTRO_SECTIONS = {
    "m1_greetings", "m1_gratitude", "m1_wishes_festive", "m1_wishes_exams",
    "m1_condolences", "m1_farewell", "m1_expressions", "m1_common_q",
    "m1_profession", "m1_casual_talk", "m1_games", "m1_holidays",
    "m1_impression", "m1_political",
    "m2_introduction", "m3_pos_intro", "m5_reading_intro", "m5_letters",
}

META_MARKERS = [
    "learners", "students", "this course", "necessary that", "essential ",
    "imperative that", "vocabulary is", "pronunciation is", "while speaking",
    "in the course of", "should not", "must be", "normally face",
    "formal british",
]


def is_meta_intro(text: str) -> bool:
    if len(text) < 200:
        return False
    low = text.lower()
    if text.count("?") >= 3:
        return False
    if text.count("!") >= 2:
        return False
    if low.split("i am ").__len__() - 1 >= 3:
        return False
    if low.split("congratulations").__len__() - 1 >= 2:
        return False
    if text.count("\u2013") >= 5:
        return False
    if text.count("\u2014") >= 5:
        return False
    return any(m in low for m in META_MARKERS)


def section_content(section_id: str):
    tagged = [i for i in content["canonical_items"]
              if i.get("section_id") == section_id and i["type"] != "heading"]
    if section_id == "m1_dialogues":
        tagged = [i for i in tagged if i["type"] == "dialogue"]
    if section_id in META_INTRO_SECTIONS:
        tagged = [i for i in tagged if not (i["type"] == "text" and is_meta_intro(i["text"]))]
    tagged.sort(key=lambda i: i["source_order"])
    return tagged[:400]


def section_intros(section_id: str):
    if section_id not in META_INTRO_SECTIONS:
        return []
    return sorted([i for i in content["canonical_items"]
                   if i.get("section_id") == section_id and i["type"] == "text"
                   and is_meta_intro(i["text"])], key=lambda i: i["source_order"])


def plan_item(day):
    src = section_content(day["section_id"])
    if not src:
        return None
    start = sum(1 for d in course["days"]
                if d["section_id"] == day["section_id"] and d["day"] < day["day"])
    return src[start] if start < len(src) else src[-1]


sec_meta = {}
for m in content["modules"]:
    for s in m["sections"]:
        sec_meta[s["section_id"]] = (m["module_id"], m["title"], m["title"])

days = course["days"]
days_by_sec = defaultdict(list)
for d in days:
    days_by_sec[d["section_id"]].append(d)

out = []
W = out.append

W("# Lesson & chapter structure audit (read-only)\n")
W(f"- course.json schema {course['schema_version']} · {len(days)} days")
W(f"- content.json schema {content['schema_version']} · "
  f"{len(content['modules'])} modules · "
  f"{sum(len(m['sections']) for m in content['modules'])} sections · "
  f"{len(content['canonical_items'])} canonical items\n")

W("## 1. Chapter inventory (`sectionContent` result vs. days)\n")
W("| module | section_id | section title | days | teachable items | intros | verdict |")
W("|---|---|---|---|---|---|---|")
problems = []
for m in content["modules"]:
    for s in m["sections"]:
        sid = s["section_id"]
        its = section_content(sid)
        intr = section_intros(sid)
        ds = days_by_sec.get(sid, [])
        verdict = "ok"
        if not ds and not intr:
            verdict = "**ORPHAN — no lessons and no intro**"
        elif not ds:
            # The UI deliberately renders a chapter that has only an intro card:
            # `if (sectionDays.isEmpty() && secIntros.isEmpty()) return@forEach`.
            verdict = "intro-only (by design)"
        elif len(ds) > len(its):
            verdict = f"**{len(ds) - len(its)} extra day(s) repeat last item**"
        elif len(its) > len(ds):
            verdict = f"{len(its) - len(ds)} item(s) never taught"
        if verdict != "ok":
            problems.append((sid, s["title"], len(ds), len(its), verdict))
        W(f"| {m['module_id']} | `{sid}` | {s['title'][:52]} | {len(ds)} | {len(its)} | "
          f"{len(intr)} | {verdict} |")

W("\n## 2. Chapter problems\n")
if not problems:
    W("none")
for sid, title, nd, ni, v in problems:
    W(f"- `{sid}` ({title[:60]}) — days={nd}, teachable items={ni} → {v}")

W("\n## 3. Exact lesson → item binding (what a student actually gets)\n")
for m in content["modules"]:
    for s in m["sections"]:
        sid = s["section_id"]
        ds = sorted(days_by_sec.get(sid, []), key=lambda d: d["day"])
        if not ds:
            continue
        its = section_content(sid)
        W(f"\n### `{sid}` — {s['title']}  ({len(ds)} days / {len(its)} items)")
        for n, d in enumerate(ds):
            if n < len(its):
                it = its[n]
                tag = it["content_id"]
            else:
                it = its[-1]
                tag = it["content_id"] + " **REPEAT**"
            txt = it["text"].replace("\n", " ⏎ ")
            W(f"- day {d['day']}: `{tag}` type={it['type']} len={len(it['text'])} "
              f"| title: *{d['lesson_title'][:70]}*")
            W(f"  - item text: {txt[:220]}")

W("\n## 4. Content quality flags\n")
c = Counter()
W("\n### 4a. Items whose text looks like instructional commentary but are taught")
for m in content["modules"]:
    for s in m["sections"]:
        sid = s["section_id"]
        for it in section_content(sid):
            t = it["text"]
            low = t.lower()
            hits = [mk for mk in META_MARKERS if mk in low]
            if hits and len(t) < 200:
                c["short_meta"] += 1
                W(f"- `{it['content_id']}` in `{sid}` (len {len(t)}) markers={hits[:3]}: {t[:150]}")

W("\n### 4b. Very short teachable items (< 25 chars) — thin lessons")
for m in content["modules"]:
    for s in m["sections"]:
        sid = s["section_id"]
        for it in section_content(sid):
            if len(it["text"]) < 25:
                c["tiny"] += 1
                W(f"- `{it['content_id']}` in `{sid}` (len {len(it['text'])}): {it['text']!r}")

W("\n### 4c. Identical / near-duplicate item texts across the course")
seen = defaultdict(list)
for it in content["canonical_items"]:
    seen[it["text"].strip().lower()].append(it)
dups = {k: v for k, v in seen.items() if len(v) > 1 and k}
W(f"exact duplicate texts: {len(dups)}")
for k, v in list(dups.items())[:60]:
    ids = ", ".join(f"{x['content_id']}@{x.get('section_id')}" for x in v)
    W(f"- {ids} :: {k[:90]}")

W("\n### 4d. Lesson titles that repeat the chapter title or the source item heading")
for d in days:
    if d.get("is_exam"):
        continue
    sid = d["section_id"]
    ct = sec_meta.get(sid, ("", "", ""))[1].strip().lower()
    lt = d["lesson_title"].strip().lower()
    if ct and (lt == ct or lt.startswith(ct)):
        c["title_eq_chapter"] += 1
W(f"lesson titles equal/starting with chapter title: {c['title_eq_chapter']}")

W("\n### 4e. '· n/m' fraction markers in lesson titles — do they match day order?")
bad = 0
for sid, ds in days_by_sec.items():
    ds_sorted = sorted(ds, key=lambda d: d["day"])
    for n, d in enumerate(ds_sorted):
        lt = d["lesson_title"]
        if "\u00b7" in lt:
            frac = lt.rsplit("\u00b7", 1)[1].strip()
            want = f"{n + 1}/{len(ds_sorted)}"
            if frac != want:
                bad += 1
                if bad <= 40:
                    W(f"- day {d['day']} `{sid}` has '{frac}' expected '{want}' :: {lt[:70]}")
W(f"fraction-marker mismatches: {bad}")

W("\n### 4f. Exam days")
for d in days:
    if d.get("is_exam"):
        W(f"- day {d['day']} module={d['module_id']} seq={d['activity_sequence']} "
          f"title=*{d['lesson_title']}* sel={d['content_selection']}")

W("\n### 4g. Sections in META_INTRO_SECTIONS where the intro filter removes everything teachable")
for sid in sorted(META_INTRO_SECTIONS):
    its = section_content(sid)
    if not its:
        W(f"- `{sid}` → 0 teachable items, {len(section_intros(sid))} intro(s); "
          f"days={len(days_by_sec.get(sid, []))}")

W("\n### 4h. Counts")
W(f"- short_meta (commentary taught as a lesson): {c['short_meta']}")
W(f"- tiny items (<25 chars): {c['tiny']}")
W(f"- duplicate texts: {len(dups)}")

open("tools/content_review/review.md", "w", encoding="utf-8").write("\n".join(out))
print("wrote tools/content_review/review.md", len(out), "lines")
print("problems:", problems)
