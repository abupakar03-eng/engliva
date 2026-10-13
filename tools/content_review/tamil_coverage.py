"""User-visible Tamil coverage, before and after the restructure.

`LessonScreens.kt` renders `StructuredContent(parts)` when an item has `parts`
(tables, blocks, Q&A) — every cell/block is translated on its own — and the raw
item text only when there are no parts. Counting whole item texts therefore
overstates the gap; this counts what the learner actually sees, with the same
lookup `Glossary.translate` / `tamilLine` perform (exact trimmed text, else the
word-by-word glossary fallback).

Run:  python tools/content_review/tamil_coverage.py
"""
import json
import sys

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

ROOT = "app/src/main/assets"
tr = json.load(open(f"{ROOT}/translations.json", encoding="utf-8"))["strings"]


def is_meta_intro(t):
    if len(t) < 200:
        return False
    low = t.lower()
    if t.count("?") >= 3 or t.count("!") >= 2:
        return False
    if low.split("i am ").__len__() - 1 >= 3:
        return False
    if low.split("congratulations").__len__() - 1 >= 2:
        return False
    if t.count("\u2013") >= 5 or t.count("\u2014") >= 5:
        return False
    return any(mk in low for mk in META_MARKERS)


def measure(tag, course_path, content_path, verbose=False):
    course = json.load(open(course_path, encoding="utf-8"))
    content = json.load(open(content_path, encoding="utf-8"))

    def section_content(sid):
        lst = [i for i in content["canonical_items"]
               if i.get("section_id") == sid and i["type"] != "heading"]
        if sid == "m1_dialogues":
            lst = [i for i in lst if i["type"] == "dialogue"]
        if sid in META_INTRO_SECTIONS:
            lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
        return sorted(lst, key=lambda i: i["source_order"])[:400]

    parts = raw_ok = 0
    gloss = []
    for d in course["days"]:
        if d.get("is_exam"):
            continue
        sid = d["section_id"]
        its = section_content(sid)
        if not its:
            continue
        prior = sum(1 for x in course["days"]
                    if x["section_id"] == sid and not x.get("is_exam") and x["day"] < d["day"])
        it = its[prior] if prior < len(its) else its[-1]
        # A conversation renders `turns`, each with its own BilingualText, so it
        # counts as structured even though it has no `parts`.
        if it.get("parts") or it.get("turns"):
            parts += 1
        elif it["text"].strip() in tr:
            raw_ok += 1
        else:
            gloss.append((d["day"], sid, it["content_id"], len(it["text"])))

    total = parts + raw_ok + len(gloss)
    print(f"{tag}: {total} lessons")
    print(f"   structured parts (cells translated individually) : {parts}")
    print(f"   raw text with a natural whole-line translation   : {raw_ok}")
    print(f"   raw text falling back to the word-gloss          : {len(gloss)}"
          f"  ({len(gloss) * 100 // max(total, 1)}%)")
    if verbose:
        for day, sid, cid, n in gloss:
            print(f"      day {day:3d} {sid:18s} {cid:8s} ({n} chars)")
    return len(gloss), total


if __name__ == "__main__":
    verbose = "-v" in sys.argv
    b = measure("BEFORE", "tools/content_review/backup/course.json",
                "tools/content_review/backup/content.json", verbose)
    print()
    a = measure("AFTER ", f"{ROOT}/course.json", f"{ROOT}/content.json", verbose)
