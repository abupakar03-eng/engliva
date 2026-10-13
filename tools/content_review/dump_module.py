"""Dump one module's chapters and lessons, so authored practice matches the teaching.

Usage:  python tools/content_review/dump_module.py m2_vocabulary [chars]
"""
import json
import sys

ROOT = "app/src/main/assets"
MOD = sys.argv[1] if len(sys.argv) > 1 else "m2_vocabulary"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 260

content = json.load(open(f"{ROOT}/content.json", encoding="utf-8"))
course = json.load(open(f"{ROOT}/course.json", encoding="utf-8"))
items = {i["content_id"]: i for i in content["canonical_items"]}

mod = next(m for m in content["modules"] if m["module_id"] == MOD)
print(f"=== {MOD}: {mod['title']} ===")
for s in mod["sections"]:
    days = [d for d in course["days"]
            if d["section_id"] == s["section_id"] and not d.get("is_exam")]
    days.sort(key=lambda d: d["day"])
    print(f"\n## {s['section_id']}  ({len(days)} lessons)  — {s['title']}")
    for d in days:
        print(f"   · {d['lesson_title']}")
    # the items themselves, in teaching order
    its = [i for i in content["canonical_items"]
           if i.get("section_id") == s["section_id"] and i["type"] != "heading"]
    its.sort(key=lambda i: i["source_order"])
    for it in its:
        kind = (it.get("parts") or {}).get("kind") or ("turns" if it.get("turns") else "text")
        body = it["text"].replace("\n", " ⏎ ")
        print(f"     [{kind}] {body[:LIMIT]}")
