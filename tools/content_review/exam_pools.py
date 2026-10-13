"""Exam-pool size per module, before and after the restructure.

`buildExamPlan` samples items whose text is 20..300 chars, so merging short
items into longer units shrinks a module's exam. Mirrors the shipped rule.
"""
import json
import re

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


def section_content(content, sid):
    lst = [i for i in content["canonical_items"]
           if i.get("section_id") == sid and i["type"] != "heading"]
    if sid == "m1_dialogues":
        lst = [i for i in lst if i["type"] == "dialogue"]
    if sid in META_INTRO_SECTIONS:
        lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
    return sorted(lst, key=lambda i: i["source_order"])[:400]


def pools(tag, path_c, path_t):
    course = json.load(open(path_c, encoding="utf-8"))
    content = json.load(open(path_t, encoding="utf-8"))
    print(f"--- {tag} ---")
    for m in content["modules"]:
        pool = []
        for s in m["sections"]:
            pool += [i for i in section_content(content, s["section_id"])
                     if 20 <= len(i["text"]) <= 300 and i["type"] != "dialogue"]
        sample = next((d["content_selection"].get("sample_size", 10)
                       for d in course["days"] if d.get("is_exam")
                       and d["module_id"] == m["module_id"]), None)
        mark = "  <-- EXAM WILL FAIL" if not pool else (
            f"  (exam asks {min(sample or 10, len(pool))} of {sample})" if sample else "")
        print(f"  {m['module_id']:18s} pool={len(pool):3d}{mark}")
        if len(pool) <= 12:
            for i in pool[:12]:
                print(f"        {i['content_id']} ({len(i['text'])}): {i['text'][:60]!r}")


pools("BEFORE (git HEAD)", "tools/content_review/backup/course.json",
      "tools/content_review/backup/content.json")
print()
pools("AFTER  (current)", "app/src/main/assets/course.json",
      "app/src/main/assets/content.json")
