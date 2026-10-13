"""List the lessons that have no question step, so a check can be authored for each.

A lesson ends with a question when the app can ask one: a Q&A item (quiz), an item
carrying an authored `check`, or short content (the app blurs it for a memory
check). Everything else currently just stops after a read-aloud.
"""
import json
import re
import sys
from collections import Counter

ROOT = "app/src/main/assets"
META = {"m1_greetings", "m1_gratitude", "m1_wishes_festive", "m1_wishes_exams",
        "m1_condolences", "m1_farewell", "m1_expressions", "m1_common_q",
        "m1_profession", "m1_casual_talk", "m1_games", "m1_holidays",
        "m1_impression", "m1_political", "m2_introduction", "m3_pos_intro",
        "m5_reading_intro", "m5_letters"}
MK = ["learners", "students", "this course", "necessary that", "essential ",
      "imperative that", "vocabulary is", "pronunciation is", "while speaking",
      "in the course of", "should not", "must be", "normally face", "formal british"]
SHORT = 200


def meta(t):
    if len(t) < 200:
        return False
    low = t.lower()
    if t.count("?") >= 3 or t.count("!") >= 2:
        return False
    if low.split("i am ").__len__() - 1 >= 3 or low.split("congratulations").__len__() - 1 >= 2:
        return False
    if t.count("\u2013") >= 5 or t.count("\u2014") >= 5:
        return False
    return any(m in low for m in MK)


content = json.load(open(f"{ROOT}/content.json", encoding="utf-8"))
course = json.load(open(f"{ROOT}/course.json", encoding="utf-8"))

BY = {}
for i in content["canonical_items"]:
    BY.setdefault(i.get("section_id"), []).append(i)


def sc(sid):
    lst = [i for i in BY.get(sid, []) if i["type"] != "heading"]
    if sid == "m1_dialogues":
        lst = [i for i in lst if i["type"] == "dialogue"]
    if sid in META:
        lst = [i for i in lst if not (i["type"] == "text" and meta(i["text"]))]
    return sorted(lst, key=lambda i: i["source_order"])[:400]


days = [d for d in course["days"] if not d.get("is_exam")]
cache, rows = {}, []
for d in sorted(days, key=lambda d: d["day"]):
    sid = d["section_id"]
    cache.setdefault(sid, sc(sid))
    its = cache[sid]
    if not its:
        continue
    prior = sum(1 for x in days if x["section_id"] == sid and x["day"] < d["day"])
    it = its[prior] if prior < len(its) else its[-1]
    parts = it.get("parts") or {}
    is_quiz = (parts.get("kind") == "questions" and parts.get("questions")
               and all((q.get("a") or "").strip() for q in parts["questions"]))
    has_check = bool(it.get("check"))
    if it.get("turns") or is_quiz or has_check:
        continue
    if len(it["text"]) <= SHORT:
        continue
    rows.append((d["day"], it["content_id"], sid, d["lesson_title"], len(it["text"]), it["text"]))

print(f"lessons with no question step: {len(rows)}\n")
for sec, n in Counter(r[2] for r in rows).most_common():
    print(f"   {n:3d}  {sec}")
print()
for day, cid, sid, title, n, text in rows:
    flat = re.sub(r"\s+", " ", text)[:100]
    print(f"{day:4d} {cid:8s} {sid:20s} {n:4d} {title[:38]:38s} | {flat}")
