#!/usr/bin/env python3
"""Merge the translation chunks into app/src/main/assets/translations.json.

Checks:
  1. every chunk has an output whose length equals its input length;
  2. every value is a non-empty string containing at least one Tamil character
     (English grammar terms may stay in English, so Latin is allowed);
  3. no value is left identical to its English source;
  4. the merged map covers 100% of the displayed strings.

Exits non-zero on any problem.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools", "glossary")
CHUNKS = os.path.join(TOOLS, "string_chunks")
GENERATED = os.path.join(TOOLS, "translations_out")
ASSET = os.path.join(ROOT, "app", "src", "main", "assets", "translations.json")

TAMIL = re.compile(r"[\u0B80-\u0BFF]")
WORD = re.compile(r"[A-Za-z][A-Za-z'\u2019-]*")
NO_MEANING = "புரியாத சொல்"


def is_word_list_line(line):
    """True for lines that are really a comma-separated list of words.

    These are the vocabulary and pronunciation lists ("Bicycle, Calculate,
    Educate, ..."). Translating them as a sentence produced transliterations
    (பைசிக்கிள், கால்குலேட்) rather than meanings, so they are rewritten from
    the word glossary instead.
    """
    line = line.strip()
    if not line or len(line) > 300:
        return False
    if re.search(r"[.!?]\s+[A-Z]", line):        # an embedded sentence, not a list
        return False
    parts = [p.strip() for p in line.split(",") if p.strip()]
    if len(parts) < 3:
        return False
    short = [p for p in parts if len(p.split()) <= 2]
    return len(short) / len(parts) >= 0.7 and all(WORD.search(p) for p in parts)


def rewrite_segment(segment, glossary):
    """`Bicycle` → `Bicycle (சைக்கிள்)`; anything else is left untouched."""
    raw = segment.strip()
    if not raw or not WORD.search(raw):
        return raw
    # "... etc." tails keep the word meaningful: `Elastic etc.` → `Elastic (…) இத்யாதி.`
    tail = ""
    etc = re.fullmatch(r"([A-Za-z][A-Za-z'\u2019-]*)\s+etc\.?", raw, re.IGNORECASE)
    if etc:
        raw, tail = etc.group(1), " இத்யாதி."
    match = re.fullmatch(r"([^A-Za-z]*)([A-Za-z][A-Za-z'\u2019-]*)([^A-Za-z]*)", raw)
    if not match:
        return raw                                # multi-word phrase — leave it
    pre, word, post = match.groups()
    if word.lower() in {"etc", "eg", "ie", "vs"}:
        return raw
    meaning = glossary.get(word.lower())
    if not meaning or meaning == NO_MEANING:
        return raw                                # nothing better to offer
    return f"{pre}{word} ({meaning}){post}{tail}"


def rewrite_line(line, glossary):
    if not is_word_list_line(line):
        return line, False
    segments = line.split(",")
    rewritten = ", ".join(rewrite_segment(s, glossary) for s in segments)
    return rewritten, rewritten != line


def translate_word_lists(english, tamil, glossary):
    """Replace transliterated word lists with real meanings, per line.

    Any Tamil prose the translator appended (for example the explanation in an
    odd-one-out exercise) is preserved after an em dash.
    """
    english_lines = english.split("\n")
    tamil_lines = tamil.split("\n")
    output, changed = [], False
    for index, english_line in enumerate(english_lines):
        tamil_line = tamil_lines[index] if index < len(tamil_lines) else ""
        rewritten, line_changed = rewrite_line(english_line, glossary)
        if line_changed:
            suffix = ""
            marker = tamil_line.find(" — ")
            if marker >= 0 and TAMIL.search(tamil_line[marker:]):
                suffix = tamil_line[marker:]
            if suffix and rewritten.endswith("."):
                rewritten = rewritten[:-1]
            output.append(rewritten + suffix)
            changed = True
        else:
            output.append(tamil_line or english_line)
    return "\n".join(output), changed


def main():
    with open(os.path.join(TOOLS, "strings.json"), encoding="utf-8") as fh:
        strings = json.load(fh)

    translations = {}
    problems = []

    for name in sorted(os.listdir(CHUNKS)):
        chunk_id = name[len("tchunk_"):-len(".json")]
        with open(os.path.join(CHUNKS, name), encoding="utf-8") as fh:
            source = json.load(fh)
        out_path = os.path.join(GENERATED, name)
        if not os.path.exists(out_path):
            problems.append(f"tchunk_{chunk_id}: no translation output")
            continue
        with open(out_path, encoding="utf-8") as fh:
            produced = json.load(fh)

        if not isinstance(produced, list):
            problems.append(f"tchunk_{chunk_id}: output is not a JSON array")
            continue
        if len(produced) != len(source):
            problems.append(
                f"tchunk_{chunk_id}: length mismatch — {len(source)} in, {len(produced)} out"
            )
            continue

        for english, tamil in zip(source, produced):
            if not isinstance(tamil, str) or not tamil.strip():
                problems.append(f"tchunk_{chunk_id}: empty translation for {english[:60]!r}")
            elif not TAMIL.search(tamil):
                problems.append(f"tchunk_{chunk_id}: no Tamil script for {english[:60]!r}")
            elif tamil.strip() == english.strip():
                problems.append(f"tchunk_{chunk_id}: left untranslated — {english[:60]!r}")
            else:
                translations[english] = tamil.strip()

    missing = [s for s in strings if s not in translations]
    for s in missing[:20]:
        problems.append(f"no translation for {s[:60]!r} ({len(missing)} total)")

    if problems:
        print(f"PROBLEMS: {len(problems)}")
        for p in problems[:40]:
            print("  -", p)
        return 1

    # Vocabulary/pronunciation lists get their meanings from the word glossary:
    # a transliterated list ("பைசிக்கிள், கால்குலேட்") teaches nothing.
    with open(os.path.join(ROOT, "app", "src", "main", "assets", "glossary.json"),
              encoding="utf-8") as fh:
        glossary = json.load(fh)["entries"]
    rewritten = 0
    for english in strings:
        fixed, changed = translate_word_lists(english, translations[english], glossary)
        if changed:
            translations[english] = fixed
            rewritten += 1

    payload = {
        "schema_version": "1.0.0",
        "language": "ta",
        "style": "spoken",
        "strings": {s: translations[s] for s in strings},
    }
    with open(ASSET, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))

    gloss_only = sum(1 for s in strings if not TAMIL.search(translations[s]))
    print(f"strings      : {len(strings)}")
    print(f"translated   : {len(translations)}")
    print(f"coverage     : {len(translations) * 100 // len(strings)}%")
    print(f"asset        : {os.path.relpath(ASSET, ROOT)} ({os.path.getsize(ASSET) / 1024:.0f} KB)")
    print(f"no Tamil     : {gloss_only}")
    print(f"word lists   : {rewritten} lines rewritten with word meanings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
