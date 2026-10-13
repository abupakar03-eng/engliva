"""Apply verified proofreading fixes to the shipped assets.

Each fix is a minimal substring replacement. It is applied to
  * content.json   (item text, and every structured `parts` string — including
    nested table rows and question cells)
  * course.json    (lesson titles)
  * translations.json *keys* only (the Tamil values are untouched), so a fixed
    lesson keeps its natural Tamil line instead of falling back to the gloss.
glossary.json is deliberately left alone: it is keyed by the words the course
*used* to contain, and regenerating it is `tools/glossary/extract_words.py`.

Replacement strings are chosen to be unique enough that they can only match the
one place they are meant to fix; `--check` reports the blast radius first.

Run:  python tools/content_review/fix_typos.py --check
      python tools/content_review/fix_typos.py
"""
import json
import sys
from collections import OrderedDict

ASSETS = "app/src/main/assets"

# (exact substring as shipped, corrected substring, why)
FIXES = [
    # ── greetings / courtesy phrases ─────────────────────────────────────────
    ("your greet them", "you greet them",
     "'your' for 'you'"),
    ("If its an old friend", "If it’s an old friend",
     "missing apostrophe in it's"),
    ("It’s long time since we met", "It’s a long time since we met",
     "missing article"),
    ("I’ve an headache", "I’ve a headache",
     "'an' before a consonant sound"),
    # ── teacher prose ────────────────────────────────────────────────────────
    ("the areas of confusion is made clear", "the areas of confusion are made clear",
     "subject-verb disagreement"),
    ("in the conservation is a very vital", "in the conversation is a very vital",
     "'conservation' for 'conversation'"),
    ("of a question are direct", "of a question is direct",
     "subject-verb disagreement in a grammar rule"),
    ("you dispose of something you threw it away",
     "you dispose of something you throw it away",
     "tense: present 'dispose' with past 'threw'"),
    # ── dialogues ────────────────────────────────────────────────────────────
    ("Hai, Raja", "Hi, Raja",
     "'Hai' for 'Hi'"),
    ("Dr. Roa", "Dr. Rao",
     "misspelt surname"),
    ("Had the post man delivered", "Had the postman delivered",
     "'post man' is one word"),
    ("Every body loves animals.", "Everybody loves animals.",
     "'every body' for 'everybody'"),
    ("how was the film “Abbe Sivam”?", "how was the film “Anbe Sivam”?",
     "misspelt film title (the film with Kamal Haasan and Madhavan is Anbe Sivam)"),
    # ── vocabulary tables and exercises ──────────────────────────────────────
    ("Hanger", "Hangar",
     "a hangar houses aeroplanes; a hanger holds clothes"),
    ("Ironmanager", "Ironmonger",
     "'Ironmanager' for 'Ironmonger'"),
    ("A list of table of duties", "A list or table of duties",
     "'of' for 'or'"),
    ("Maxico", "Mexico",
     "misspelt country name"),
    ("New Zeeland", "New Zealand",
     "misspelt country name"),
    ("Games(s)", "Game(s)",
     "garbled table header"),
    ("Fuel", "Full",
     "Plenary means Full; 'Fuel' is a one-letter slip (only occurrence is this table cell)"),
    ("bluge", "bulge",
     "'bluge' for 'bulge'"),
    ("cosumables", "consumables",
     "'cosumables' for 'consumables'"),
    ("Knivers", "Knives",
     "'Knivers' for 'Knives' (paired with 'fork' in the word bank)"),
    ("Vermal", "Vermin",
     "'Vermal' for 'Vermin' in the always-plural list"),
    ("There is a plenty of fish here.", "There is plenty of fish here.",
     "'a plenty' for 'plenty'"),
    ("The hunter shot there (deer, deers)", "The hunter shot three (deer, deers)",
     "'there' for 'three'"),
    ("A dare-evil", "A dare-devil",
     "the idiom is 'dare-devil'"),
    ("connected which:", "connected with?",
     "garbled question end"),
    ("Horse 2. Rose 3. March", "1. Horse 2. Rose 3. March",
     "answers list lost its '1.'"),
    ("Present Tense 2. Past Tense 3. Future Tense",
     "1. Present Tense 2. Past Tense 3. Future Tense",
     "list lost its '1.'"),
    ("It (is raining / have been raining) all right.",
     "It (is raining / has been raining) all right.",
     "'It … have' in a tense exercise; the pair should be is raining / has been raining"),
    # ── grammar notes ────────────────────────────────────────────────────────
    ("At, by, for, off, in, with", "At, by, for, of, in, with",
     "'off' for 'of' in the list of simple prepositions"),
    ("The Bagavat Gita", "The Bhagavad Gita",
     "misspelt title"),
    ("Kolkotta", "Kolkata",
     "misspelt city name"),
    # ── composition hints ────────────────────────────────────────────────────
    ("tells his to lay them aside", "tells him to lay them aside",
     "'his' for 'him'"),
    ("the rotten apple spoils the good one’s",
     "the rotten apple spoils the good ones",
     "possessive apostrophe; a plural is meant"),
    ("once climbs up a tree", "one climbs up a tree",
     "'once' for 'one' (the next clause says 'the other')"),
    ("queen of Sheeba", "queen of Sheba",
     "misspelt proper noun"),
    # ── model letter ─────────────────────────────────────────────────────────
    ("Economics class my Roll No. is", "Economics class. My Roll No. is",
     "run-on; the model letter needs a full stop"),
    # ── chapter / lesson titles ──────────────────────────────────────────────
    ("Kinds of Sentence", "Kinds of Sentences",
     "title: 'kinds of' takes a plural noun"),
    ("Kinds of Noun — ", "Kinds of Nouns — ",
     "title: 'kinds of' takes a plural noun"),
    ("Kinds of Pronoun", "Kinds of Pronouns",
     "title: 'kinds of' takes a plural noun"),
    ("Kinds of Adverb", "Kinds of Adverbs",
     "title: 'kinds of' takes a plural noun"),
    ("Question Tags — Remember", "Question Tags — Points to Remember",
     "title reads as a fragment"),
]


def walk_fix(node, old, new):
    """Replace in every string value.

    Idempotent: a string that already contains `new` is left alone, so re-running
    the script (to add a new fix) cannot double-apply a fix whose replacement
    still contains its own search string — e.g. "Kinds of Sentence" ->
    "Kinds of Sentences", or a "1." inserted at the front of a list.
    """
    n = 0
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str):
                if old in v and new not in v:
                    node[k] = v.replace(old, new)
                    n += v.count(old)
            else:
                n += walk_fix(v, old, new)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str):
                if old in v and new not in v:
                    node[i] = v.replace(old, new)
                    n += v.count(old)
            else:
                n += walk_fix(v, old, new)
    return n


def walk_count(node, old, new):
    """Count occurrences in strings that still need the fix.

    A string that already contains `new` is not pending, which is what makes
    re-running the script safe for fixes whose replacement contains its own
    search string ("Kinds of Sentence" -> "Kinds of Sentences", or a "1."
    inserted at the front of a list).
    """
    n = 0
    if isinstance(node, dict):
        for v in node.values():
            n += walk_count(v, old, new)
    elif isinstance(node, list):
        for v in node:
            n += walk_count(v, old, new)
    elif isinstance(node, str):
        if old in node and new not in node:
            n += node.count(old)
    return n


def pending_keys(strings, old, new):
    return [k for k in strings if old in k and new not in k]


def load():
    return (json.load(open(f"{ASSETS}/content.json", encoding="utf-8"),
                      object_pairs_hook=OrderedDict),
            json.load(open(f"{ASSETS}/course.json", encoding="utf-8"),
                      object_pairs_hook=OrderedDict),
            json.load(open(f"{ASSETS}/translations.json", encoding="utf-8"),
                      object_pairs_hook=OrderedDict))


def main():
    check = "--check" in sys.argv
    content, course, tr_file = load()

    total = 0
    surprising = []
    for old, new, why in FIXES:
        c = walk_count(content, old, new)
        d = walk_count(course, old, new)
        t = len(pending_keys(tr_file["strings"], old, new))
        if check:
            print(f"  content={c:<3d} course={d:<3d} trkeys={t:<3d}  {old!r} -> {new!r}")
            continue
        if c + d + t == 0:
            continue
        walk_fix(content, old, new)
        walk_fix(course, old, new)
        strings = tr_file["strings"]
        renamed = 0
        for k in pending_keys(strings, old, new):
            nk = k.replace(old, new)
            if nk in strings:
                print(f"  !! key collision, left alone: {nk[:60]!r}")
                continue
            strings[nk] = strings.pop(k)
            renamed += 1
        total += c + d + renamed
        print(f"  content={c:<3d} course={d:<3d} trkeys={renamed:<3d}  {old!r} -> {new!r}")

    if check:
        print(f"\nchecked {len(FIXES)} fixes")
        return

    # A rename can collide with a key that already exists (e.g. "New Zeeland" ->
    # "New Zealand" when a correct "New Zealand" key is already there). The old
    # key is then unreachable; drop it so no misspelling ships in the data.
    # Liveness is tested against the actual string values, not a JSON dump,
    # because a dump escapes newlines and every multi-line key would look dead.
    live = set()

    def collect(node):
        if isinstance(node, str):
            live.add(node)
        elif isinstance(node, dict):
            for v in node.values():
                collect(v)
        elif isinstance(node, list):
            for v in node:
                collect(v)

    collect(content)
    collect(course)
    strings = tr_file["strings"]
    dead = []
    for k in strings:
        for o, n, _ in FIXES:
            if o in k and n not in k and k not in live:
                dead.append(k)
                break
    for k in dead:
        strings.pop(k)
    if dead:
        print(f"  dropped {len(dead)} unreachable pre-fix key(s): "
              f"{[k[:40] for k in dead]}")

    print(f"\ntotal replacements: {total}")
    if not total and not dead:
        return
    for path, data, indent, nl in (
        (f"{ASSETS}/content.json", content, 2, "\r\n"),
        (f"{ASSETS}/course.json", course, 2, "\r\n"),
        (f"{ASSETS}/translations.json", tr_file, None, ""),
    ):
        with open(path, "w", encoding="utf-8", newline=nl) as fh:
            if indent:
                json.dump(data, fh, ensure_ascii=False, indent=indent)
            else:
                json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print("written")


if __name__ == "__main__":
    main()
