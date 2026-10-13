"""Give every lesson the class flow: teacher explains → you say it → recall → mark.

The app already has the five steps as wires. This sets each lesson's
`activity_sequence` from what the lesson actually contains, so every lesson in
every module runs the same class:

    1. listen        the teacher reads it out — you listen and follow
    2. listen_repeat you say each line back
    3. read_aloud    you say the whole thing yourself          (marked)
    4. assessment    "say it from memory", Peek if stuck       (marked)

Adapted to the content, because one size does not fit a word list and a passage:

    conversation             discussion                     (teacher takes a part, you take the other — marked)
    question + answer        listen → read_aloud → assessment
    short content (<=200)    listen → listen_repeat → read_aloud → assessment
    medium (201-600)         listen → read_aloud → assessment
    long (>600, passages)    listen → read_aloud

`speak` and `assessment` blur short content, so practice always uses `read_aloud`
(which shows the text) and the memory step is always last.

Run:  python tools/content_review/structure_activities.py [--dry-run]
"""
import json
import sys
from collections import Counter, OrderedDict

ASSETS = "app/src/main/assets"
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

SHORT, MEDIUM = 200, 600


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


def becomes_quiz(item):
    """True when the app will turn this item into one question per activity.

    Either the item carries an authored `check`, or it is a Q&A item whose every
    question has a model answer. Otherwise the app falls back to a plain recall
    activity — and on long content that shows the whole text again under the words
    "Final check", which is not a check at all.
    """
    check = item.get("check") or []
    if check:
        return all((q.get("a") or "").strip() for q in check)
    parts = item.get("parts") or {}
    if parts.get("kind") != "questions":
        return False
    qs = parts.get("questions") or []
    return bool(qs) and all((q.get("a") or "").strip() for q in qs)


def sequence_for(item):
    """The class flow, shaped to what this lesson holds."""
    if item.get("turns"):
        return ["discussion"], "conversation"
    if becomes_quiz(item):
        return ["listen", "read_aloud", "assessment"], "question + answer (real quiz)"
    n = len(item["text"])
    if n <= SHORT:
        return ["listen", "listen_repeat", "read_aloud", "assessment"], "short (memory check)"
    if n <= 400:
        return ["listen", "listen_repeat", "read_aloud"], "medium"
    return ["listen", "read_aloud"], "long passage"


def main(dry_run=False):
    content = json.load(open(f"{ASSETS}/content.json", encoding="utf-8"),
                        object_pairs_hook=OrderedDict)
    course = json.load(open(f"{ASSETS}/course.json", encoding="utf-8"),
                       object_pairs_hook=OrderedDict)
    items = {i["content_id"]: i for i in content["canonical_items"]}

    def section_items(sid):
        lst = [i for i in content["canonical_items"]
               if i.get("section_id") == sid and i["type"] != "heading"]
        if sid == "m1_dialogues":
            lst = [i for i in lst if i["type"] == "dialogue"]
        if sid in META_INTRO_SECTIONS:
            lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
        return sorted(lst, key=lambda i: i["source_order"])[:400]

    cache = {}
    for d in course["days"]:
        if not d.get("is_exam"):
            cache.setdefault(d["section_id"], section_items(d["section_id"]))

    before, after, shapes = Counter(), Counter(), Counter()
    lessons = [d for d in course["days"] if not d.get("is_exam")]
    for d in sorted(lessons, key=lambda d: d["day"]):
        its = cache[d["section_id"]]
        if not its:
            continue
        prior = sum(1 for x in lessons
                    if x["section_id"] == d["section_id"] and x["day"] < d["day"])
        item = its[prior] if prior < len(its) else its[-1]
        seq, shape = sequence_for(item)
        before[" → ".join(d["activity_sequence"])] += 1
        after[" → ".join(seq)] += 1
        shapes[shape] += 1
        if not dry_run:
            d["activity_sequence"] = seq

    print(f"lessons: {len(lessons)}\n")
    print("lesson shapes:")
    for k, n in shapes.most_common():
        print(f"   {n:4d}  {k}")
    print("\nsequences BEFORE:")
    for k, n in before.most_common(12):
        print(f"   {n:4d}  {k}")
    print("\nsequences AFTER:")
    for k, n in after.most_common():
        print(f"   {n:4d}  {k}")
    if dry_run:
        print("\n[dry run] nothing written")
        return
    with open(f"{ASSETS}/course.json", "w", encoding="utf-8", newline="\r\n") as fh:
        json.dump(course, fh, ensure_ascii=False, indent=2)
    print("\nwritten")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
