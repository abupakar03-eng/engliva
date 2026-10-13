"""Restore natural Tamil translations for lessons created by merging items.

`Glossary.translate` (Kotlin) and `tamilLine` (web) both look the lesson's whole
text up in `translations.json`, falling back to a word-by-word gloss. Merging
two items that each had a natural translation therefore produced a new key that
did not exist yet.

This composes it: the merged text is exactly "\n".join(component texts), so its
natural translation is "\n".join(component translations) — the same convention
the 37 existing multi-line entries already use.

Only composite entries in which EVERY component already has a natural
translation are added; anything else is left to the gloss fallback, unchanged.

Run:  python tools/content_review/compose_translations.py
"""
import json
import sys
from collections import OrderedDict

# The proofreading pass (fix_typos.py) renames translation keys to the corrected
# spelling, so a component text taken from the pre-restructure backup must be
# put through the same corrections before it is looked up.
sys.path.insert(0, "tools/content_review")
from fix_typos import FIXES  # noqa: E402

ROOT = "app/src/main/assets"
TRANSLATIONS = f"{ROOT}/translations.json"
BACKUP_CONTENT = "tools/content_review/backup/content.json"
MANIFEST = "tools/content_review/merge_manifest.json"

tr_file = json.load(open(TRANSLATIONS, encoding="utf-8"), object_pairs_hook=OrderedDict)
strings = tr_file["strings"]

old_items = {i["content_id"]: i["text"]
             for i in json.load(open(BACKUP_CONTENT, encoding="utf-8"))["canonical_items"]}
new_items = {i["content_id"]: i["text"]
             for i in json.load(open(f"{ROOT}/content.json", encoding="utf-8"))["canonical_items"]}
manifest = json.load(open(MANIFEST, encoding="utf-8"))

added = skipped_partial = already = 0


def corrected(text):
    for o, n, _ in FIXES:
        text = text.replace(o, n)
    return text


for new_cid, old_cids in manifest:
    if new_cid not in new_items:
        continue
    key = new_items[new_cid].strip()
    if key in strings:
        already += 1
        continue
    parts = [corrected(old_items.get(c, "")).strip() for c in old_cids]
    if not all(p in strings for p in parts):
        skipped_partial += 1
        continue
    strings[key] = "\n".join(strings[p] for p in parts)
    added += 1

with open(TRANSLATIONS, "w", encoding="utf-8", newline="") as fh:
    json.dump(tr_file, fh, ensure_ascii=False, separators=(",", ":"))

print(f"translations.json: {len(strings)} entries "
      f"(+{added} composed, {already} already present, "
      f"{skipped_partial} left to the word-gloss fallback)")
