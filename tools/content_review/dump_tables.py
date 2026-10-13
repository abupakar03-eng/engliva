"""Print the table rows of chosen chapters, so authored Q&A can quote the answers."""
import json
import sys

ROOT = "app/src/main/assets"
content = json.load(open(f"{ROOT}/content.json", encoding="utf-8"))
WANT = sys.argv[1:] or []
for it in content["canonical_items"]:
    sid = it.get("section_id")
    if WANT and sid not in WANT:
        continue
    p = it.get("parts") or {}
    if p.get("kind") != "table":
        continue
    print(f"\n## {sid}  {it['content_id']}")
    for row in p.get("rows") or []:
        print("   " + " | ".join(row))
