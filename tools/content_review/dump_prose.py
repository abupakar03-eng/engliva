"""Dump every lesson text in order, for a manual proofread.

Resolves each day to the item the shipped runtime would actually show — the same
rule as `CourseContent.sectionContent` (headings dropped, the `m1_dialogues`
dialogue filter, and the `META_INTRO_SECTIONS` commentary filter) — then splits
the result into N files on lesson boundaries (never mid-word).

Run:  python tools/content_review/dump_prose.py [chunks]
"""
import json
import sys

ROOT = "app/src/main/assets"
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


content = json.load(open(f"{ROOT}/content.json", encoding="utf-8"))
course = json.load(open(f"{ROOT}/course.json", encoding="utf-8"))

items = content["canonical_items"]


def section_content(sid):
    lst = [i for i in items if i.get("section_id") == sid and i["type"] != "heading"]
    if sid == "m1_dialogues":
        lst = [i for i in lst if i["type"] == "dialogue"]
    if sid in META_INTRO_SECTIONS:
        lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
    return sorted(lst, key=lambda i: i["source_order"])[:400]


days = [d for d in course["days"] if not d.get("is_exam")]
cache = {}
blocks = []
for d in days:
    sid = d["section_id"]
    if sid not in cache:
        cache[sid] = section_content(sid)
    its = cache[sid]
    if not its:
        continue
    prior = sum(1 for x in days if x["section_id"] == sid and x["day"] < d["day"])
    it = its[prior] if prior < len(its) else its[-1]
    blocks.append(f"### day {d['day']} | {it['content_id']} | {d['lesson_title']}\n"
                  f"{it['text']}\n")

n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
per = (len(blocks) + n - 1) // n
for i in range(n):
    part = blocks[i * per:(i + 1) * per]
    if not part:
        continue
    path = f"tools/content_review/prose_{i}.txt"
    open(path, "w", encoding="utf-8").write("\n".join(part))
    print(f"{path}  {len(part)} lessons  {sum(len(p) for p in part)} chars")
