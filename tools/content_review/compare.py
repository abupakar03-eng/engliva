"""Before/after chapter table for the restructure report."""
import json
from collections import defaultdict

import importlib.util
spec = importlib.util.spec_from_file_location("aud", "tools/content_review/audit.py")

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


def load(cp, tp):
    return (json.load(open(cp, encoding="utf-8")),
            json.load(open(tp, encoding="utf-8")))


def chapters(course, content):
    days = defaultdict(list)
    for d in course["days"]:
        if not d.get("is_exam"):
            days[d["section_id"]].append(d)
    out = []
    for m in content["modules"]:
        for s in m["sections"]:
            sid = s["section_id"]
            lst = [i for i in content["canonical_items"]
                   if i.get("section_id") == sid and i["type"] != "heading"]
            if sid == "m1_dialogues":
                lst = [i for i in lst if i["type"] == "dialogue"]
            if sid in META_INTRO_SECTIONS:
                lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
            out.append((sid, s["title"], len(days.get(sid, [])), len(lst)))
    return out


old = chapters(*load("tools/content_review/backup/course.json",
                     "tools/content_review/backup/content.json"))
new = chapters(*load("app/src/main/assets/course.json",
                     "app/src/main/assets/content.json"))
om = {r[0]: r for r in old}
nm = {r[0]: r for r in new}

print("| chapter | lessons before → after | title |")
print("|---|---|---|")
for sid, title, nd, ni in new:
    if sid not in om:
        print(f"| `{sid}` | **new** → {nd} | {title} |")
        continue
    ob = om[sid]
    delta = f"{ob[2]} → **{nd}**" if ob[2] != nd else f"{nd}"
    t = title if title != ob[1] else f"*{title}*"
    print(f"| `{sid}` | {delta} | {t} |")
for sid, title, nd, ni in old:
    if sid not in nm:
        print(f"| `{sid}` | **{nd} → removed** | (content re-homed) |")

print()
print("BEFORE chapters:", len(old), "lessons:", sum(r[2] for r in old))
print("AFTER  chapters:", len(new), "lessons:", sum(r[2] for r in new))
print("lessons removed:", sum(r[2] for r in old) - sum(r[2] for r in new))
retitled = [r[0] for r in new if r[0] in om and r[1] != om[r[0]][1]]
print("chapters retitled:", len(retitled), retitled)
