#!/usr/bin/env python3
"""Merge the generated chunks into app/src/main/assets/glossary.json and verify it.

Checks performed:
  1. every chunk file for every word in words.txt exists and parses;
  2. each chunk's key set exactly equals its input chunk (no missing/extra keys);
  3. every value is non-empty, Tamil-script only, and free of Latin letters;
  4. the merged glossary covers 100% of the words extracted from the assets.

Exits non-zero on any problem, so it can gate a build.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools", "glossary")
CHUNKS = os.path.join(TOOLS, "chunks")
GENERATED = os.path.join(TOOLS, "out")
ASSET = os.path.join(ROOT, "app", "src", "main", "assets", "glossary.json")

TAMIL_ONLY = re.compile(r"^[\u0B80-\u0BFF\s,./?-]+$")
HAS_LATIN = re.compile(r"[A-Za-z]")


def main():
    with open(os.path.join(TOOLS, "words.txt"), encoding="utf-8") as fh:
        words = [w for w in fh.read().split("\n") if w]

    entries = {}
    problems = []
    seen_input = set()

    for name in sorted(os.listdir(CHUNKS)):
        chunk_id = name[len("chunk_"):-len(".json")]
        with open(os.path.join(CHUNKS, name), encoding="utf-8") as fh:
            chunk_words = json.load(fh)
        out_path = os.path.join(GENERATED, name)
        if not os.path.exists(out_path):
            problems.append(f"chunk_{chunk_id}: no generated output")
            continue
        with open(out_path, encoding="utf-8") as fh:
            data = json.load(fh)

        for word in chunk_words:
            seen_input.add(word)
            value = data.get(word)
            if value is None:
                problems.append(f"chunk_{chunk_id}: missing key '{word}'")
            elif not str(value).strip():
                problems.append(f"chunk_{chunk_id}: empty value for '{word}'")
            elif HAS_LATIN.search(value):
                problems.append(f"chunk_{chunk_id}: value for '{word}' has Latin letters: {value!r}")
            elif not TAMIL_ONLY.match(value):
                problems.append(f"chunk_{chunk_id}: value for '{word}' has unexpected chars: {value!r}")
            else:
                entries[word] = value.strip()

        for extra in set(data) - set(chunk_words):
            problems.append(f"chunk_{chunk_id}: unexpected key '{extra}'")

    for word in words:
        if word not in seen_input:
            problems.append(f"word '{word}' is in no chunk")

    missing = [w for w in words if w not in entries]
    for word in missing[:20]:
        problems.append(f"no meaning for '{word}' ({len(missing)} total)")

    # Hand-curated fixes for the few entries the batch generation got wrong
    # (kept in a file so re-running this script reproduces the same asset).
    override_count = 0
    overrides_path = os.path.join(TOOLS, "overrides.json")
    if os.path.exists(overrides_path):
        with open(overrides_path, encoding="utf-8") as fh:
            overrides = json.load(fh)
        for word, value in overrides.items():
            if word not in entries:
                problems.append(f"override for word not in the course: '{word}'")
            elif not TAMIL_ONLY.match(value) or HAS_LATIN.search(value):
                problems.append(f"override for '{word}' is not Tamil-script only: {value!r}")
            else:
                entries[word] = value
                override_count += 1

    if problems:
        print(f"PROBLEMS: {len(problems)}")
        for p in problems[:40]:
            print("  -", p)
        return 1

    payload = {
        "schema_version": "1.0.0",
        "language": "ta",
        "style": "spoken",
        "entries": {w: entries[w] for w in words},
    }
    with open(ASSET, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))

    covered = sum(1 for w in words if w in entries)
    print(f"words        : {len(words)}")
    print(f"entries      : {len(entries)}")
    print(f"coverage     : {covered * 100 // len(words)}% ({covered}/{len(words)})")
    print(f"asset        : {os.path.relpath(ASSET, ROOT)} ({os.path.getsize(ASSET) / 1024:.0f} KB)")
    print(f"unavailable  : {sum(1 for v in entries.values() if v == 'புரியாத சொல்')} OCR-noise entries")
    print(f"overrides    : {override_count} hand-curated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
