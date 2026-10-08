#!/usr/bin/env python3
"""Extract every string the lesson screens actually display, for translation.

Walks content.json in document order and pulls the exact strings the UI renders:
item text (when there are no structured parts), every block/question/answer/table
cell, phrase context + phrase, conversation turns, and titles. Deduplicates while
preserving first-seen order, then splits into translation chunks by character
budget so each chunk stays coherent and small enough to translate well.

Outputs:
  tools/glossary/strings.json          – all unique displayed strings
  tools/glossary/string_chunks/*.json  – batches for translation
"""
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "app", "src", "main", "assets")
OUT = os.path.join(ROOT, "tools", "glossary")
CHUNKS = os.path.join(OUT, "string_chunks")
MAX_CHARS = 7000

LETTER = re.compile(r"[A-Za-z]")


def walk(node, sink):
    if isinstance(node, str):
        sink(node)
    elif isinstance(node, dict):
        for value in node.values():
            walk(value, sink)
    elif isinstance(node, list):
        for value in node:
            walk(value, sink)


def main():
    with open(os.path.join(ASSETS, "content.json"), encoding="utf-8") as fh:
        data = json.load(fh)

    ordered = []
    seen = set()

    def add(s):
        if not isinstance(s, str):
            return
        s = s.strip()
        if len(s) < 2 or not LETTER.search(s) or s in seen:
            return
        seen.add(s)
        ordered.append(s)

    def displayed(item):
        """Strings rendered for one canonical item, in display order."""
        add(item.get("title"))
        parts = item.get("parts")
        if parts:
            for block in parts.get("blocks") or []:
                add(block.get("text"))
            for qa in parts.get("questions") or []:
                add(qa.get("q"))
                add(qa.get("a"))
            for row in parts.get("rows") or []:
                for cell in row:
                    add(cell)
            add(parts.get("context"))
            add(parts.get("phrase"))
        else:
            add(item.get("text"))
        for turn in item.get("turns") or []:
            add(turn.get("text"))

    for item in sorted(data["canonical_items"], key=lambda i: i.get("source_order", 0)):
        displayed(item)

    os.makedirs(CHUNKS, exist_ok=True)
    for old in os.listdir(CHUNKS):
        os.remove(os.path.join(CHUNKS, old))

    chunks, current, size = [], [], 0
    for s in ordered:
        if current and size + len(s) > MAX_CHARS:
            chunks.append(current)
            current, size = [], 0
        current.append(s)
        size += len(s)
    if current:
        chunks.append(current)

    for i, chunk in enumerate(chunks):
        with open(os.path.join(CHUNKS, f"tchunk_{i:02d}.json"), "w", encoding="utf-8") as fh:
            json.dump(chunk, fh, ensure_ascii=False, indent=1)

    with open(os.path.join(OUT, "strings.json"), "w", encoding="utf-8") as fh:
        json.dump(ordered, fh, ensure_ascii=False, indent=1)

    print(f"unique strings : {len(ordered)}")
    print(f"characters     : {sum(len(s) for s in ordered)}")
    print(f"chunks         : {len(chunks)} (<= {MAX_CHARS} chars each)")


if __name__ == "__main__":
    main()
