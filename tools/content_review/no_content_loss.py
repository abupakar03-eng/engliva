"""Prove the restructure deleted no content.

Every original item's text must still be findable: either kept as an item, or
absorbed verbatim into a merged/split item. Texts that the proofreading pass
(`fix_typos.py`) intentionally corrected are recognised by un-applying those
fixes, so a genuine loss still stands out.
"""
import json
import sys

sys.path.insert(0, "tools/content_review")
from fix_typos import FIXES  # noqa: E402
from authored.module1 import CHAPTERS as M1A  # noqa: E402
from authored.module1_more import CHAPTERS as M1B  # noqa: E402

# Chapters the authoring pass deliberately rewrote: their old items are meant to
# be gone, so they are reported separately rather than counted as losses.
REWRITTEN = {c["section_id"] for c in M1A + M1B}

old = json.load(open("tools/content_review/backup/content.json", encoding="utf-8"))
new = json.load(open("app/src/main/assets/content.json", encoding="utf-8"))

joined = "\n".join(i["text"] for i in new["canonical_items"])
new_chars = sum(len(i["text"]) for i in new["canonical_items"])
old_chars = sum(len(i["text"]) for i in old["canonical_items"])


def apply_all(text):
    """Apply the proofreading fixes to an original text, so it can be compared
    against the shipped text again."""
    for o, n, _ in FIXES:
        text = text.replace(o, n)
    return text


missing = []
corrected = 0
rewritten = 0
for i in old["canonical_items"]:
    t = i["text"].strip()
    if not t or t in joined:
        continue
    if i.get("section_id") in REWRITTEN:
        rewritten += 1
        continue
    if apply_all(t) in joined:
        corrected += 1
        continue
    missing.append((i["content_id"], i.get("section_id"), len(t), t[:90]))

print(f"original items: {len(old['canonical_items'])}  chars: {old_chars}")
print(f"new items:      {len(new['canonical_items'])}  chars: {new_chars}")
print(f"characters changed: {new_chars - old_chars:+d}")
print()
print(f"items only changed by the proofreading pass: {corrected}")
print(f"items replaced by an authored chapter:       {rewritten}")
print(f"original texts no longer present anywhere:   {len(missing)}")
for cid, sid, n, preview in missing:
    print(f"  {cid} ({sid}, {n} chars): {preview!r}")
