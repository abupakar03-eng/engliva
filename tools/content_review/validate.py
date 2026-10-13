"""Validate the restructured assets.

Mirrors, in Python, exactly what the shipped Kotlin does:
  * CourseContent.validate
  * CourseContent.sectionContent / sectionIntros
  * CourseContentTest.everyLessonResolvesToItsOwnItem
  * CourseContentTest.introSectionsStillSurfaceTheirContextParagraphs
  * CourseContentTest.sectionContentSkipsHeadings
plus a schema check against the @Serializable models in CourseModels.kt.
"""
import json
import sys
from collections import Counter, defaultdict

ROOT = "app/src/main/assets"
course = json.load(open(f"{ROOT}/course.json", encoding="utf-8"))
content = json.load(open(f"{ROOT}/content.json", encoding="utf-8"))

errors = []
warnings = []

# ── schema check (CourseModels.kt) ───────────────────────────────────────────
def need(obj, keys, where):
    for k in keys:
        if k not in obj:
            errors.append(f"{where}: missing required key '{k}'")

need(course, ["schema_version", "course_id", "course_title", "days", "lesson_engine"], "course")
need(course["lesson_engine"], ["sequence", "completion"], "lesson_engine")
need(course["lesson_engine"]["completion"],
     ["default_required_score_percent", "retry_allowed"], "completion")
need(content, ["schema_version", "course_id", "modules", "canonical_items"], "content")

VALID_ITEM_TYPES = {"heading", "text", "list_item", "dialogue", "table"}
for i in content["canonical_items"]:
    need(i, ["content_id", "type", "source_order", "text"], i.get("content_id", "?"))
    if i["type"] not in VALID_ITEM_TYPES:
        errors.append(f"{i['content_id']}: unknown item type {i['type']!r}")
for m in content["modules"]:
    need(m, ["module_id", "title", "sections"], f"module {m.get('module_id')}")
    for s in m["sections"]:
        need(s, ["section_id", "title"], f"section {s.get('section_id')}")
for d in course["days"]:
    need(d, ["day", "module_id", "section_id", "lesson_title",
             "activity_sequence", "content_selection"], f"day {d.get('day')}")
    need(d["content_selection"], ["selection_mode", "module_id"], f"day {d['day']} selection")

# ── replica of CourseContent ─────────────────────────────────────────────────
META_INTRO_SECTIONS = {
    "m1_greetings", "m1_gratitude", "m1_wishes_festive", "m1_wishes_exams",
    "m1_condolences", "m1_farewell", "m1_expressions", "m1_common_q",
    "m1_profession", "m1_casual_talk", "m1_games", "m1_holidays",
    "m1_impression", "m1_political",
    "m2_introduction", "m3_pos_intro", "m5_reading_intro", "m5_letters",
}
META_MARKERS = ["learners", "students", "this course", "necessary that", "essential ",
                "imperative that", "vocabulary is", "pronunciation is", "while speaking",
                "in the course of", "should not", "must be", "normally face",
                "formal british"]


def is_meta_intro(text):
    if len(text) < 200:
        return False
    low = text.lower()
    if text.count("?") >= 3 or text.count("!") >= 2:
        return False
    if low.split("i am ").__len__() - 1 >= 3:
        return False
    if low.split("congratulations").__len__() - 1 >= 2:
        return False
    if text.count("\u2013") >= 5 or text.count("\u2014") >= 5:
        return False
    return any(mk in low for mk in META_MARKERS)


def section_content(sid):
    lst = [i for i in content["canonical_items"]
           if i.get("section_id") == sid and i["type"] != "heading"]
    if sid == "m1_dialogues":
        lst = [i for i in lst if i["type"] == "dialogue"]
    if sid in META_INTRO_SECTIONS:
        lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
    lst.sort(key=lambda i: i["source_order"])
    return lst[:400]


def section_intros(sid):
    if sid not in META_INTRO_SECTIONS:
        return []
    return sorted([i for i in content["canonical_items"]
                   if i.get("section_id") == sid and i["type"] == "text"
                   and is_meta_intro(i["text"])], key=lambda i: i["source_order"])


# ── CourseContent.validate ───────────────────────────────────────────────────
if course["course_id"] != content["course_id"]:
    errors.append("Course IDs do not match")
if len({d["day"] for d in course["days"]}) != len(course["days"]):
    errors.append("Duplicate day IDs")
if len({i["content_id"] for i in content["canonical_items"]}) != len(content["canonical_items"]):
    errors.append("Duplicate canonical content IDs")

module_map = {m["module_id"]: m for m in content["modules"]}
section_map = {s["section_id"]: m["module_id"]
               for m in content["modules"] for s in m["sections"]}
KNOWN_PHASES = {"teach", "guided_practice", "student_response", "feedback",
                "teacher_intro", "example", "retry_or_progress", "completion",
                "discussion", "exam"}
ACTIVITY_TYPES = {"listen", "listen_repeat", "speak", "read_aloud", "identify",
                  "fill_blank", "multiple_choice", "reorder", "role_play",
                  "comprehension", "writing", "assessment", "discussion"}

for d in course["days"]:
    if d.get("is_exam"):
        if module_map.get(d["module_id"]) is None:
            errors.append(f"Day {d['day']}: exam refers to missing module {d['module_id']}")
        continue
    m = module_map.get(d["module_id"])
    if m is None:
        errors.append(f"Day {d['day']}: missing module {d['module_id']}")
    elif all(s["section_id"] != d["section_id"] for s in m["sections"]):
        errors.append(f"Day {d['day']}: section {d['section_id']} not in module {d['module_id']}")
    if d["section_id"] not in section_map:
        errors.append(f"Day {d['day']}: missing section {d['section_id']}")
    for wire in d["activity_sequence"]:
        if wire not in ACTIVITY_TYPES and wire not in KNOWN_PHASES:
            errors.append(f"Day {d['day']}: unsupported activity '{wire}'")

days_by_sec = defaultdict(list)
for d in course["days"]:
    if not d.get("is_exam"):
        days_by_sec[d["section_id"]].append(d)

for sid, ds in days_by_sec.items():
    its = section_content(sid)
    if not its:
        errors.append(f"Section {sid} has no teachable content for days "
                      f"{[d['day'] for d in ds]}")
    elif len(ds) > len(its):
        errors.append(f"Section {sid}: {len(ds)} days but only {len(its)} items")

# ── everyLessonResolvesToItsOwnItem ──────────────────────────────────────────
seen = {}
repeated = []
empty = []
for d in sorted([x for x in course["days"] if not x.get("is_exam")], key=lambda x: x["day"]):
    its = section_content(d["section_id"])
    if not its:
        empty.append(d["day"])
        continue
    prior = sum(1 for x in course["days"]
                if x["section_id"] == d["section_id"] and not x.get("is_exam")
                and x["day"] < d["day"])
    item = its[prior] if prior < len(its) else its[-1]
    key = (d["section_id"], item["content_id"])
    if key in seen:
        repeated.append(f"day {seen[key]} and day {d['day']} both teach {item['content_id']}")
    seen[key] = d["day"]
if empty:
    errors.append(f"lessons with no content: {empty}")
if repeated:
    errors.append(f"repeated lesson content: {repeated[:5]}")

# ── introSectionsStillSurfaceTheirContextParagraphs ──────────────────────────
if not section_intros("m2_introduction"):
    errors.append("m2_introduction no longer surfaces context paragraphs")

# ── sectionContentSkipsHeadings ──────────────────────────────────────────────
if any(i["type"] == "heading" for i in section_content("m1_greetings")):
    errors.append("m1_greetings sectionContent contains a heading")

# ── content-quality checks the restructure was meant to fix ──────────────────
# The UI renders `StructuredContent(parts)` *instead of* the item text whenever
# `parts` is present, so a stale or mis-parsed `parts` silently hides content.
for i in content["canonical_items"]:
    if i["type"] == "heading" or not i.get("parts"):
        continue
    p = i["parts"]
    if p["kind"] == "questions":
        for n, qa in enumerate(p.get("questions") or []):
            q = qa.get("q") or ""
            if not q.strip():
                errors.append(f"{i['content_id']}: questions[{n}] is empty")
            if "\n" in q or len(q) > 300:
                errors.append(f"{i['content_id']}: questions[{n}].q holds {len(q)} "
                              f"chars / {q.count(chr(10)) + 1} lines — not a question")
            a = qa.get("a")
            if a and ("\n" in a or len(a) > 300):
                # A model answer may legitimately BE a question — several
                # exercises say "Ask …", so the answer is the question. What is
                # never legitimate is an answer holding a whole block.
                errors.append(f"{i['content_id']}: questions[{n}].a holds a block, not an answer")
    if p["kind"] == "table":
        covered = "\n".join(" | ".join(r) for r in (p.get("rows") or []))
    elif p["kind"] == "questions":
        covered = "\n".join((qa.get("q") or "") + (qa.get("a") or "")
                            for qa in (p.get("questions") or []))
    elif p["kind"] == "blocks":
        covered = "\n".join(b.get("text") or "" for b in (p.get("blocks") or []))
    elif p["kind"] == "phrase":
        covered = (p.get("context") or "") + (p.get("phrase") or "")
    else:
        covered = ""
    hidden = len(i["text"]) - len(covered)
    if hidden > 60:
        errors.append(f"{i['content_id']}: `parts` hides {hidden} chars of the "
                      f"lesson text (the UI shows parts instead of text)")

for m in content["modules"]:
    for s in m["sections"]:
        sid = s["section_id"]
        its = section_content(sid)
        ds = days_by_sec.get(sid, [])
        if len(its) != len(ds):
            warnings.append(f"{sid}: {len(its)} teachable items but {len(ds)} days")
        texts = [i["text"].strip().lower() for i in its]
        dupes = [t for t, n in Counter(texts).items() if n > 1]
        if dupes:
            errors.append(f"{sid}: duplicate lesson text {dupes[:2]}")
        for i in its:
            t = i["text"].strip()
            if len(t) < 10:
                warnings.append(f"{sid} {i['content_id']}: very short lesson {t!r}")

print("=" * 74)
print("items", len(content["canonical_items"]),
      "| days", len(course["days"]),
      "| lessons", len([d for d in course["days"] if not d.get("is_exam")]),
      "| exams", len([d for d in course["days"] if d.get("is_exam")]),
      "| modules", len(content["modules"]),
      "| chapters", sum(len(m["sections"]) for m in content["modules"]))
print("=" * 74)
print("ERRORS:", len(errors))
for e in errors:
    print("  ✗", e)
print("WARNINGS:", len(warnings))
for w in warnings:
    print("  !", w)

# ── sections with no lessons (expected: intro-only chapters) ────────────────
print("\nchapters with no lessons:")
for m in content["modules"]:
    for s in m["sections"]:
        if not days_by_sec.get(s["section_id"]):
            print(f"  {s['section_id']:20s} intros={len(section_intros(s['section_id']))}"
                  f"  items={len(section_content(s['section_id']))}")

# ── exam placement ──────────────────────────────────────────────────────────
print("\nexam days:")
for d in course["days"]:
    if d.get("is_exam"):
        print(f"  day {d['day']:4d} {d['module_id']:18s} {d['lesson_title']}")

sys.exit(1 if errors else 0)
