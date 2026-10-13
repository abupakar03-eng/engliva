"""Append authored practice lessons to chapters, without touching what they teach.

For each chapter listed in an `authored/moduleN.py` ADDITIONS table this adds
  * a "Practice: …" lesson  — `parts.kind="questions"`, question + model answer
  * optionally a "Conversation: …" lesson — `turns`, which the role-play screen runs

The lessons are appended to the end of the chapter, so the teaching order is
unchanged, and every day is renumbered from the module/chapter/lesson structure.
Existing items, their `text` and their titles are left exactly as they are.

Run:  python tools/content_review/author_additions.py [--dry-run]
"""
import json
import sys
from collections import OrderedDict

sys.path.insert(0, "tools/content_review")
from authored import module2, module3, module45  # noqa: E402

MODULES = [module2, module3, module45]
ANSWER_TABLES = [module45]

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


def load(p):
    return json.load(open(p, encoding="utf-8"), object_pairs_hook=OrderedDict)


def main(dry_run=False):
    content = load(f"{ASSETS}/content.json")
    course = load(f"{ASSETS}/course.json")
    tr = load(f"{ASSETS}/translations.json")
    strings = tr["strings"]

    additions = {}
    for mod in MODULES:
        additions.update(mod.ADDITIONS)

    items = OrderedDict((i["content_id"], i) for i in content["canonical_items"])
    modules = content["modules"]
    sec_module = {s["section_id"]: m["module_id"] for m in modules for s in m["sections"]}
    sec_title = {s["section_id"]: s["title"] for m in modules for s in m["sections"]}

    def section_items(sid):
        lst = [i for i in items.values()
               if i.get("section_id") == sid and i["type"] != "heading"]
        if sid == "m1_dialogues":
            lst = [i for i in lst if i["type"] == "dialogue"]
        if sid in META_INTRO_SECTIONS:
            lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
        return sorted(lst, key=lambda i: i["source_order"])[:400]

    # ── titles and activity sequences for the lessons that already exist ─────
    title_by_cid, seq_by_section = {}, {}
    for d in course["days"]:
        if d.get("is_exam"):
            continue
        seq_by_section.setdefault(d["section_id"], d["activity_sequence"])
        its = section_items(d["section_id"])
        if not its:
            continue
        prior = sum(1 for x in course["days"]
                    if x["section_id"] == d["section_id"] and not x.get("is_exam")
                    and x["day"] < d["day"])
        title_by_cid[(its[prior] if prior < len(its) else its[-1])["content_id"]] = d["lesson_title"]

    # ── fill model answers into question lessons that have none ─────────────
    filled = 0
    for mod in ANSWER_TABLES:
        for cid, answers in (getattr(mod, "ANSWERS", {}) or {}).items():
            it = items.get(cid)
            if it is None:
                print(f"  !! answers for unknown item {cid}")
                continue
            qs = (it.get("parts") or {}).get("questions")
            if not qs:
                print(f"  !! {cid} is not a questions lesson")
                continue
            if len(qs) != len(answers):
                print(f"  !! {cid}: {len(qs)} questions but {len(answers)} answers — skipped")
                continue
            for qa, (a_en, a_ta) in zip(qs, answers):
                if not qa.get("a"):
                    qa["a"] = a_en
                    strings.setdefault(a_en.strip(), a_ta)
                    filled += 1

    # ── append the authored lessons ─────────────────────────────────────────
    new_titles, new_acts, added = {}, {}, 0
    for sid, spec in additions.items():
        if not section_items(sid):
            print(f"  !! {sid}: no existing lessons, skipped")
            continue
        mid = sec_module.get(sid)
        if not mid:
            print(f"  !! {sid}: not in any module, skipped")
            continue
        base = max(i["source_order"] for i in section_items(sid))

        def add(cid, text, parts, kind, title, acts, turns=None):
            nonlocal added
            if cid in items:
                return False
            it = OrderedDict([
                ("content_id", cid), ("text", text),
                ("source_order", 0), ("module_id", mid), ("section_id", sid),
                ("type", kind),
            ])
            if parts is not None:
                it["parts"] = parts
            if turns is not None:
                it["turns"] = turns
            items[cid] = it
            new_titles[cid] = title
            new_acts[cid] = acts
            added += 1
            return True

        qa = spec.get("qa") or []
        if qa:
            qs = [OrderedDict([("q", q), ("a", a)]) for q, a, _, _ in qa]
            title = spec.get("qa_title") or f"Practice: {sec_title.get(sid, sid)}"
            add(f"add_{sid}_qa", "\n".join(q for q, _, _, _ in qa),
                OrderedDict([("kind", "questions"), ("questions", qs)]),
                "text", title, list(spec.get("qa_acts") or ["listen", "read_aloud", "assessment"]))
            for q, a, qta, ata in qa:
                strings.setdefault(q.strip(), qta)
                strings.setdefault(a.strip(), ata)

        talk = spec.get("talk") or []
        if talk:
            turns = [OrderedDict([("turn_id", f"t{n}"), ("speaker", sp),
                                  ("role", role), ("text", en)])
                     for n, (sp, role, en, _) in enumerate(talk, 1)]
            title = spec.get("talk_title") or f"Conversation: {sec_title.get(sid, sid)}"
            add(f"add_{sid}_talk",
                "\n".join(f"{sp}: {en}" for sp, _, en, _ in talk),
                None, "dialogue", title, list(spec.get("talk_acts") or ["discussion"]),
                turns=turns)
            for sp, _, en, ta in talk:
                strings.setdefault(en.strip(), ta)

    # ── give the appended items their place and renumber everything ──────────
    for sid in additions:
        qa_id, talk_id = f"add_{sid}_qa", f"add_{sid}_talk"
        base = max((i["source_order"] for i in items.values()
                    if i.get("section_id") == sid and i["content_id"] not in (qa_id, talk_id)),
                   default=0)
        for n, cid in enumerate([qa_id, talk_id], 1):
            if cid in items:
                items[cid]["source_order"] = base + n

    ordered = []
    for m in modules:
        for s in m["sections"]:
            grp = [i for i in items.values() if i.get("section_id") == s["section_id"]]
            grp.sort(key=lambda i: i["source_order"])
            ordered.extend(grp)
    for n, i in enumerate(ordered):
        i["source_order"] = n
    content["canonical_items"] = ordered

    # ── regenerate every day ────────────────────────────────────────────────
    old_exam = {d["module_id"]: d for d in course["days"] if d.get("is_exam")}
    all_items = list(items.values())
    days, day_no = [], 0
    per_chapter = []
    for m in modules:
        mid = m["module_id"]
        for s in m["sections"]:
            sid = s["section_id"]
            lst = [i for i in all_items
                   if i.get("section_id") == sid and i["type"] != "heading"]
            if sid == "m1_dialogues":
                lst = [i for i in lst if i["type"] == "dialogue"]
            if sid in META_INTRO_SECTIONS:
                lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
            lst.sort(key=lambda i: i["source_order"])
            lst = lst[:400]
            default_seq = seq_by_section.get(sid) or ["listen", "listen_repeat", "read_aloud"]
            for n, it in enumerate(lst):
                day_no += 1
                cid = it["content_id"]
                title = (new_titles.get(cid) or title_by_cid.get(cid)
                         or (s["title"] if len(lst) == 1 else f"{s['title']} · {n + 1}/{len(lst)}"))
                days.append(OrderedDict([
                    ("day", day_no), ("module_id", mid), ("section_id", sid),
                    ("lesson_title", title),
                    ("activity_sequence", list(new_acts.get(cid, default_seq))),
                    ("content_selection", OrderedDict([
                        ("selection_mode", "section_sequence"),
                        ("module_id", mid), ("section_id", sid)])),
                ]))
            per_chapter.append((sid, len(lst)))
        ex = old_exam.get(mid)
        if ex:
            day_no += 1
            days.append(OrderedDict([
                ("day", day_no), ("module_id", mid),
                ("section_id", f"_exam_{mid}"),
                ("lesson_title", f"{m['title']} — Final Exam"),
                ("activity_sequence", ["exam"]),
                ("content_selection", OrderedDict([
                    ("selection_mode", "module_exam"), ("module_id", mid),
                    ("sample_size", ex["content_selection"].get("sample_size", 10))])),
                ("is_exam", True),
            ]))
    course["days"] = days

    print(f"model answers filled in: {filled}")
    print(f"practice lessons added: {added}")
    print(f"items: {len(items)}   days: {len(days)}   translations: {len(strings)}")
    print("\nchapters touched:")
    for sid in additions:
        row = next(r for r in per_chapter if r[0] == sid)
        print(f"  {sid:22s} now {row[1]:2d} lessons")
    if dry_run:
        print("[dry run] nothing written")
        return
    for path, data, indent, nl in (
        (f"{ASSETS}/content.json", content, 2, "\r\n"),
        (f"{ASSETS}/course.json", course, 2, "\r\n"),
        (f"{ASSETS}/translations.json", tr, None, ""),
    ):
        with open(path, "w", encoding="utf-8", newline=nl) as fh:
            if indent:
                json.dump(data, fh, ensure_ascii=False, indent=indent)
            else:
                json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print("written")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
