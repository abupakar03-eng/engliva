"""Write authored chapters into the shipped assets.

Replaces the named chapters' items and days with the authored structure, gives
every authored lesson its own title, its own activity sequence and its Tamil
lines, then regenerates the whole day list (module → chapter → lesson, exams
last in each module) so day numbers stay consistent.

Run:  python tools/content_review/author.py [--dry-run]
"""
import json
import sys
from collections import OrderedDict

sys.path.insert(0, "tools/content_review")
from authored.module1 import CHAPTERS as M1A  # noqa: E402
from authored.module1_more import CHAPTERS as M1B  # noqa: E402

CHAPTERS = M1A + M1B

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
NOT_COUNTED = {"feedback", "retry_or_progress", "completion"}


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


def load(path):
    return json.load(open(path, encoding="utf-8"), object_pairs_hook=OrderedDict)


def main(dry_run=False):
    content = load(f"{ASSETS}/content.json")
    course = load(f"{ASSETS}/course.json")
    tr = load(f"{ASSETS}/translations.json")
    strings = tr["strings"]
    items = OrderedDict((i["content_id"], i) for i in content["canonical_items"])

    # ── what the current assets already say, so untouched chapters are kept ───
    existing_ids = set(items)
    modules = content["modules"]
    sec_module = {s["section_id"]: m["module_id"] for m in modules for s in m["sections"]}
    seq_by_section = {}
    for d in course["days"]:
        if not d.get("is_exam"):
            seq_by_section.setdefault(d["section_id"], d["activity_sequence"])

    def section_content(cid_source, sid):
        lst = [i for i in cid_source if i.get("section_id") == sid and i["type"] != "heading"]
        if sid == "m1_dialogues":
            lst = [i for i in lst if i["type"] == "dialogue"]
        if sid in META_INTRO_SECTIONS:
            lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
        return sorted(lst, key=lambda i: i["source_order"])[:400]

    title_by_cid = {}
    for d in course["days"]:
        if d.get("is_exam"):
            continue
        its = section_content(list(items.values()), d["section_id"])
        if not its:
            continue
        prior = sum(1 for x in course["days"]
                    if x["section_id"] == d["section_id"] and not x.get("is_exam")
                    and x["day"] < d["day"])
        hit = its[prior] if prior < len(its) else its[-1]
        title_by_cid[hit["content_id"]] = d["lesson_title"]

    # ── build the authored chapters ──────────────────────────────────────────
    seq = [900000]
    new_titles, new_acts = {}, {}
    for ch in CHAPTERS:
        sid = ch["section_id"]
        old_items = [i for i in items.values() if i.get("section_id") == sid]
        for i in old_items:
            items.pop(i["content_id"], None)

        def add(text, parts, kind, title=None, turns=None):
            seq[0] += 1
            cid = f"a{seq[0]}"
            while cid in items:
                seq[0] += 1
                cid = f"a{seq[0]}"
            it = OrderedDict([
                ("content_id", cid),
                ("text", text),
                ("source_order", seq[0]),
                ("module_id", ch["module_id"]),
                ("section_id", sid),
                ("type", kind),
            ])
            if parts is not None:
                it["parts"] = parts
            if turns is not None:
                it["turns"] = turns
            items[cid] = it
            if title:
                new_titles[cid] = title
            return cid

        # chapter orientation paragraphs — stay intro cards, never lessons
        for en, ta in ch.get("intro", []):
            add(en, None, "text")
            strings[en.strip()] = ta

        for lesson in ch["lessons"]:
            title = lesson["title"]
            acts = lesson["acts"]
            if "blocks" in lesson:
                blocks = [OrderedDict([("kind", k), ("text", en)])
                          for k, en, ta in lesson["blocks"]]
                text = "\n".join(en for _, en, _ in lesson["blocks"])
                cid = add(text, OrderedDict([("kind", "blocks"), ("blocks", blocks)]),
                          "text", title)
                for _, en, ta in lesson["blocks"]:
                    strings[en.strip()] = ta
            elif "questions" in lesson:
                qs = [OrderedDict([("q", q), ("a", a)])
                      for q, a, _, _ in lesson["questions"]]
                text = "\n".join(q for q, _, _, _ in lesson["questions"])
                cid = add(text, OrderedDict([("kind", "questions"), ("questions", qs)]),
                          "text", title)
                for q, a, qta, ata in lesson["questions"]:
                    strings[q.strip()] = qta
                    strings[a.strip()] = ata
            elif "turns" in lesson:
                turns = [OrderedDict([("turn_id", f"t{n}"), ("speaker", sp),
                                      ("role", role), ("text", en)])
                         for n, (sp, role, en, _) in enumerate(lesson["turns"], 1)]
                text = "\n".join(f"{sp}: {en}" for sp, _, en, _ in lesson["turns"])
                cid = add(text, None, "dialogue", title, turns=turns)
                for sp, _, en, ta in lesson["turns"]:
                    strings[en.strip()] = ta
            else:
                raise SystemExit(f"lesson without content: {title}")
            new_acts[cid] = list(acts)

        # replace the section entry in place, keeping its position
        for m in modules:
            for idx, s in enumerate(m["sections"]):
                if s["section_id"] == sid:
                    m["sections"][idx] = OrderedDict([
                        ("section_id", sid), ("title", ch["title"])])

    # ── renumber source_order in module → section → item order ───────────────
    ordered = []
    for m in modules:
        for s in m["sections"]:
            grp = [i for i in items.values() if i.get("section_id") == s["section_id"]]
            grp.sort(key=lambda i: i["source_order"])
            ordered.extend(grp)
    orphans = [i["content_id"] for i in items.values() if i.get("section_id") not in sec_module]
    if orphans:
        raise SystemExit(f"items in unknown sections: {orphans[:5]}")
    for n, i in enumerate(ordered):
        i["source_order"] = n
    content["canonical_items"] = ordered

    # ── regenerate every day ────────────────────────────────────────────────
    old_exam = {d["module_id"]: d for d in course["days"] if d.get("is_exam")}
    all_items = list(items.values())
    days, day_no, per_section = [], 0, []
    for m in modules:
        mid = m["module_id"]
        for s in m["sections"]:
            sid = s["section_id"]
            lessons = section_content(all_items, sid)
            default_seq = seq_by_section.get(sid) or ["listen", "listen_repeat", "read_aloud"]
            for n, it in enumerate(lessons):
                day_no += 1
                cid = it["content_id"]
                title = (new_titles.get(cid) or title_by_cid.get(cid)
                         or (s["title"] if len(lessons) == 1
                             else f"{s['title']} · {n + 1}/{len(lessons)}"))
                days.append(OrderedDict([
                    ("day", day_no),
                    ("module_id", mid),
                    ("section_id", sid),
                    ("lesson_title", title),
                    ("activity_sequence", list(new_acts.get(cid, default_seq))),
                    ("content_selection", OrderedDict([
                        ("selection_mode", "section_sequence"),
                        ("module_id", mid),
                        ("section_id", sid),
                    ])),
                ]))
            per_section.append((sid, s["title"], len(lessons)))
        ex = old_exam.get(mid)
        if ex:
            day_no += 1
            days.append(OrderedDict([
                ("day", day_no),
                ("module_id", mid),
                ("section_id", f"_exam_{mid}"),
                ("lesson_title", f"{m['title']} — Final Exam"),
                ("activity_sequence", ["exam"]),
                ("content_selection", OrderedDict([
                    ("selection_mode", "module_exam"),
                    ("module_id", mid),
                    ("sample_size", ex["content_selection"].get("sample_size", 10)),
                ])),
                ("is_exam", True),
            ]))
    course["days"] = days

    print(f"items {len(existing_ids)} -> {len(items)}   days -> {len(days)}")
    print("\nauthored chapters:")
    for ch in CHAPTERS:
        sid = ch["section_id"]
        row = next(r for r in per_section if r[0] == sid)
        print(f"  {sid:22s} {row[2]:2d} lessons   {ch['title']}")
    print(f"\ntranslations: {len(strings)} entries")
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
