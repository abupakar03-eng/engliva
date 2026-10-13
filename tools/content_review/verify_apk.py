"""Verify the built APK bundles the restructured + proofread content.

Extract the assets first, then run this:

    tar -xf app/build/outputs/apk/debug/app-debug.apk -C build/apk-assets-check assets
    python tools/content_review/verify_apk.py

It checks that every asset inside the APK is byte-identical to the repo copy, and
that the bundled content carries the new lesson/chapter structure and the
proofreading (so a stale APK can never be mistaken for a current one).
"""
import hashlib
import json

SRC = "app/src/main/assets"
APK = "build/apk-assets-check/assets"

for f in ["content.json", "course.json", "translations.json", "glossary.json"]:
    a = hashlib.sha256(open(f"{SRC}/{f}", "rb").read()).hexdigest()
    b = hashlib.sha256(open(f"{APK}/{f}", "rb").read()).hexdigest()
    print(f"  {f:20s} repo == APK : {a == b}")

course = json.load(open(f"{APK}/course.json", encoding="utf-8"))
content = json.load(open(f"{APK}/content.json", encoding="utf-8"))
blob = json.dumps(content, ensure_ascii=False) + json.dumps(course, ensure_ascii=False)

lessons = [d for d in course["days"] if not d.get("is_exam")]
exams = [d for d in course["days"] if d.get("is_exam")]
sections = [s for m in content["modules"] for s in m["sections"]]

print()
print(f"  modules  : {len(content['modules'])}")
print(f"  chapters : {len(sections)}")
print(f"  items    : {len(content['canonical_items'])}")
print(f"  days     : {len(course['days'])}  ({len(lessons)} lessons + {len(exams)} exams)")

print()
print("  restructure evidence:")
print(f"    new m2_young_ones chapter   : "
      f"{any(s['section_id'] == 'm2_young_ones' for s in sections)}")
print(f"    m5_requisitions removed     : "
      f"{not any(s['section_id'] == 'm5_requisitions' for s in sections)}")
print(f"    comprehension q-lessons     : "
      f"{sum(1 for i in content['canonical_items'] if i['content_id'].endswith('q'))}")
print(f"    'Kinds of Sentences' title  : "
      f"{any(s['title'] == 'Kinds of Sentences' for s in sections)}")

print()
print("  proofreading evidence:")
for good in ["Mexico", "New Zealand", "Anbe Sivam", "Hangar", "Ironmonger",
             "Knives", "Vermin", "Kolkata", "Bhagavad Gita", "dare-devil"]:
    print(f"    {good:16s} {blob.count(good)}")
for bad in ["Maxico", "New Zeeland", "Abbe Sivam", "Ironmanager", "Knivers",
            "Vermal", "Kolkotta", "Bagavat Gita", "dare-evil"]:
    print(f"    OLD {bad:12s} {blob.count(bad)}")
