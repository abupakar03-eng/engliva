"""Give every lesson an end-of-lesson check: a question the app asks and marks.

`author_additions.py` rebuilt whole chapters; this only attaches a `check` to an
existing item, so nothing already taught is touched.

Two sources:
  * `HAND` — written out for lessons whose content is prose (passages, compositions,
    grammar rules), in `authored/checks.py`;
  * generated from a lesson's table, using the book's own rows, so a
    "Word | Meaning" table becomes "What does ‘kennel’ mean?" with the book's
    meaning as the model answer, and the Tamil already stored for that meaning.

Run:  python tools/content_review/author_checks.py [--dry-run]
"""
import json
import sys
from collections import Counter, OrderedDict

sys.path.insert(0, "tools/content_review")
from authored.checks import HAND  # noqa: E402

ASSETS = "app/src/main/assets"

# header (lowercased) -> (question with {k}, tamil question with {k})
TEMPLATES = {
    ("word", "meaning"): ("What does ‘{k}’ mean?", "‘{k}’ என்பதன் பொருள் என்ன?"),
    ("expression", "meaning"): ("What does ‘{k}’ mean?", "‘{k}’ என்பதன் பொருள் என்ன?"),
    ("singular", "plural"): ("What is the plural of ‘{k}’?", "‘{k}’ என்பதன் பன்மை என்ன?"),
    ("masculine", "feminine"): ("What is the feminine of ‘{k}’?", "‘{k}’-இன் பெண்பால் என்ன?"),
    ("bird", "sound"): ("What sound does a {k} make?", "{k} எந்த ஒலி எழுப்பும்?"),
    ("adult", "young"): ("What is the young of a {k} called?", "{k}-இன் குட்டியை என்ன என்பார்கள்?"),
    ("wrong", "right"): ("Say it correctly: {k}", "இதைச் சரியாகச் சொல்லுங்கள்: {k}"),
    ("difficult word", "easier word"):
        ("What is an easier word for ‘{k}’?", "‘{k}’ என்பதற்கு எளிய சொல் என்ன?"),
    ("a. country", "b. currency"):
        ("Which currency is used in {k}?", "{k}-இல் எந்த நாணயம் பயன்படுத்தப்படுகிறது?"),
}
# 4-column families: (header, step) -> pair of column names
FOUR = {
    ("difficult word", "easier word"): None,          # rows are k,v,k,v
    ("noun", "verb", "adjective", "adverb"): None,    # rows are noun,verb,adj,adv
}
FOUR_Q = {
    ("noun", "verb", "adjective", "adverb"): [
        ("Give the verb form of ‘{k}’.", "‘{k}’ என்பதன் வினை வடிவம் என்ன?", 1),
        ("Give the adjective form of ‘{k}’.", "‘{k}’ என்பதன் பெயரடை வடிவம் என்ன?", 2),
        ("Give the adverb form of ‘{k}’?", "‘{k}’ என்பதன் வினையடை வடிவம் என்ன?", 3),
    ],
}
MAX_PER_LESSON = 3


def table_checks(item, strings):
    parts = item.get("parts") or {}
    if parts.get("kind") != "table":
        return []
    rows = parts.get("rows") or []
    if len(rows) < 2:
        return []
    header = tuple(c.strip().lower() for c in rows[0])
    body = [r for r in rows[1:] if any(c.strip() for c in r)]
    out = []

    def add(q, qta, a):
        a = (a or "").strip()
        if not a or len(q) > 160:
            return
        out.append((q, a, qta, strings.get(a, a)))

    key = FOUR_Q.get(header)
    if key:
        for row in body:
            cells = [c.strip() for c in row]
            if len(cells) < 4 or not cells[0]:
                continue
            for qt, qtt, idx in key:
                if cells[idx] and cells[idx] != "-":
                    add(qt.format(k=cells[0]), qtt.format(k=cells[0]), cells[idx])
            if len(out) >= MAX_PER_LESSON:
                break
        return out[:MAX_PER_LESSON]

    tmpl = TEMPLATES.get(header)
    if tmpl is None:
        return []
    qt, qtt = tmpl
    if header in (("difficult word", "easier word"),):
        # rows hold two pairs: k, v, k, v
        for row in body:
            cells = [c.strip() for c in row]
            for a_i, b_i in ((0, 1), (2, 3)):
                if len(cells) > b_i and cells[a_i] and cells[b_i]:
                    add(qt.format(k=cells[a_i]), qtt.format(k=cells[a_i]), cells[b_i])
            if len(out) >= MAX_PER_LESSON:
                break
        return out[:MAX_PER_LESSON]

    for row in body:
        cells = [c.strip() for c in row]
        if len(cells) < 2 or not cells[0] or not cells[1]:
            continue
        add(qt.format(k=cells[0]), qtt.format(k=cells[0]), cells[1])
        if len(out) >= MAX_PER_LESSON:
            break
    return out[:MAX_PER_LESSON]


def main(dry_run=False):
    content = json.load(open(f"{ASSETS}/content.json", encoding="utf-8"),
                        object_pairs_hook=OrderedDict)
    tr = json.load(open(f"{ASSETS}/translations.json", encoding="utf-8"),
                  object_pairs_hook=OrderedDict)
    strings = tr["strings"]

    hand = gen = skipped = 0
    no_source = []
    for it in content["canonical_items"]:
        cid = it["content_id"]
        if it.get("check") or it.get("turns"):
            continue
        parts = it.get("parts") or {}
        if parts.get("kind") == "questions":
            qs = parts.get("questions") or []
            # Only skip when the item already asks its own questions *and* they all
            # carry answers. A questions item with blank answers cannot become a
            # quiz, so it still needs a check of its own.
            if qs and all((q.get("a") or "").strip() for q in qs):
                continue
        pairs = []
        if cid in HAND:
            pairs = HAND[cid]
            if pairs:
                hand += 1
        if not pairs:
            pairs = table_checks(it, strings)
            if pairs:
                gen += 1
        if not pairs:
            if len(it["text"]) > 200:
                no_source.append((cid, it.get("section_id"), len(it["text"]),
                                  it["text"][:70].replace("\n", " ")))
            continue
        it["check"] = [OrderedDict([("q", q), ("a", a)]) for q, a, _, _ in pairs]
        for q, a, qta, ata in pairs:
            strings.setdefault(q.strip(), qta)
            strings.setdefault(a.strip(), ata)

    print(f"checks written by hand : {hand}")
    print(f"checks from tables     : {gen}")
    print(f"still without a check  : {len(no_source)}")
    for cid, sid, n, prev in no_source[:25]:
        print(f"   {cid:8s} {str(sid):20s} {n:4d}  {prev}")
    print(f"translations: {len(strings)}")
    if dry_run:
        print("[dry run] nothing written")
        return
    with open(f"{ASSETS}/content.json", "w", encoding="utf-8", newline="\r\n") as fh:
        json.dump(content, fh, ensure_ascii=False, indent=2)
    with open(f"{ASSETS}/translations.json", "w", encoding="utf-8", newline="") as fh:
        json.dump(tr, fh, ensure_ascii=False, separators=(",", ":"))
    print("written")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
