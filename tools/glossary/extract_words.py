#!/usr/bin/env python3
"""Extract every English word displayed by the app from the bundled assets.

Sources: app/src/main/assets/content.json (all string values, including
conversation turns and structured `parts`) and app/src/main/assets/course.json
(course title + lesson titles).

Outputs:
  tools/glossary/words.txt    – unique words, one per line, sorted
  tools/glossary/chunks/*.json– input batches for glossary generation
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "app", "src", "main", "assets")
OUT = os.path.join(ROOT, "tools", "glossary")
CHUNK_SIZE = 150

WORD = re.compile(r"[A-Za-z]+(?:['\u2019-][A-Za-z]+)*")

def walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)

def main():
    words = {}
    for name in ("content.json", "course.json"):
        with open(os.path.join(ASSETS, name), encoding="utf-8") as fh:
            data = json.load(fh)
        for s in walk_strings(data):
            for m in WORD.findall(s):
                w = m.replace("\u2019", "'").lower()
                words[w] = words.get(w, 0) + 1

    ordered = sorted(words)
    os.makedirs(os.path.join(OUT, "chunks"), exist_ok=True)
    with open(os.path.join(OUT, "words.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(ordered) + "\n")

    for old in os.listdir(os.path.join(OUT, "chunks")):
        os.remove(os.path.join(OUT, "chunks", old))
    chunks = [ordered[i:i + CHUNK_SIZE] for i in range(0, len(ordered), CHUNK_SIZE)]
    for i, chunk in enumerate(chunks):
        with open(os.path.join(OUT, "chunks", f"chunk_{i:02d}.json"), "w", encoding="utf-8") as fh:
            json.dump(chunk, fh, ensure_ascii=False, indent=0)

    print(f"unique words : {len(ordered)}")
    print(f"total tokens : {sum(words.values())}")
    print(f"chunks       : {len(chunks)} x <= {CHUNK_SIZE}")
    print("sample       :", ", ".join(ordered[:15]))

if __name__ == "__main__":
    main()
