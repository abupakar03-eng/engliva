"""Can every existing lesson be split into short lines WITHOUT losing its Tamil?

The natural Tamil translation is keyed by the whole lesson text. To show one
line of English with its own Tamil line, the English must be split AND the
existing Tamil value split the same way. This measures how often that is
possible, per split strategy.
"""
import json
import re

ROOT = "app/src/main/assets"
tr = json.load(open(f"{ROOT}/translations.json", encoding="utf-8"))["strings"]
content = json.load(open(f"{ROOT}/content.json", encoding="utf-8"))
course = json.load(open(f"{ROOT}/course.json", encoding="utf-8"))

META = {"m1_greetings", "m1_gratitude", "m1_wishes_festive", "m1_wishes_exams",
        "m1_condolences", "m1_farewell", "m1_expressions", "m1_common_q",
        "m1_profession", "m1_casual_talk", "m1_games", "m1_holidays",
        "m1_impression", "m1_political", "m2_introduction", "m3_pos_intro",
        "m5_reading_intro", "m5_letters"}
MK = ["learners", "students", "this course", "necessary that", "essential ",
      "imperative that", "vocabulary is", "pronunciation is", "while speaking",
      "in the course of", "should not", "must be", "normally face", "formal british"]


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


items = content["canonical_items"]
BY = {}
for i in items:
    BY.setdefault(i.get("section_id"), []).append(i)


def sc(sid):
    lst = [i for i in BY.get(sid, []) if i["type"] != "heading"]
    if sid == "m1_dialogues":
        lst = [i for i in lst if i["type"] == "dialogue"]
    if sid in META:
        lst = [i for i in lst if not (i["type"] == "text" and meta(i["text"]))]
    return sorted(lst, key=lambda i: i["source_order"])[:400]


days = [d for d in course["days"] if not d.get("is_exam")]
cache, lessons = {}, []
for d in days:
    sid = d["section_id"]
    cache.setdefault(sid, sc(sid))
    its = cache[sid]
    if not its:
        continue
    prior = sum(1 for x in days if x["section_id"] == sid and x["day"] < d["day"])
    lessons.append((d, its[prior] if prior < len(its) else its[-1]))

SENT_EN = re.compile(r"(?<=[.!?])\s+")
SENT_TA = re.compile(r"(?<=[.!?])\s+")


def pieces(text):
    """Candidate splits, most reliable first."""
    t = text.strip()
    if "\n" in t:
        yield "newline", [p.strip() for p in t.split("\n") if p.strip()]
    if " – " in t:
        yield "endash", [p.strip() for p in t.split(" – ") if p.strip()]
    if "; " in t:
        yield "semicolon", [p.strip() for p in t.split("; ") if p.strip()]
    if SENT_EN.search(t):
        yield "sentence", [p.strip() for p in SENT_EN.split(t) if p.strip()]
    yield "none", [t]


stats = {}
unmatched = []
for d, it in lessons:
    if it.get("parts"):
        stats.setdefault("already structured", []).append(it["content_id"])
        continue
    en = it["text"].strip()
    ta = tr.get(en)
    if ta is None:
        stats.setdefault("no Tamil key", []).append(it["content_id"])
        continue
    best = None
    for name, parts in pieces(en):
        if len(parts) < 2:
            continue
        for tname, tparts in pieces(ta):
            if len(tparts) == len(parts):
                best = (name, tname, len(parts))
                break
        if best:
            break
    if best:
        stats.setdefault(f"aligned via {best[0]}/{best[1]}", []).append(it["content_id"])
    else:
        stats.setdefault("CANNOT SPLIT", []).append(it["content_id"])
        unmatched.append((it["content_id"], len(en), en[:70]))

print(f"lessons: {len(lessons)}\n")
for k in sorted(stats, key=lambda k: -len(stats[k])):
    print(f"  {len(stats[k]):4d}  {k}")
print()
print("examples that cannot be split to align:")
for cid, n, p in unmatched[:20]:
    print(f"   {cid} ({n}): {p!r}")
