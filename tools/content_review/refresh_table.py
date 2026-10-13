"""Regenerate the chapter table in CONTENT_REVIEW.md from compare.py output."""
import subprocess
import sys

out = subprocess.run([sys.executable, "tools/content_review/compare.py"],
                     capture_output=True, text=True, encoding="utf-8").stdout
tbl = out.split("BEFORE chapters:")[0].rstrip().replace("\ufeff", "") + "\n"

rep = open("CONTENT_REVIEW.md", encoding="utf-8").read().replace("\ufeff", "")
start = rep.find("| chapter |")
end = rep.find("`m4_passages` grows because")
assert start > 0 and end > start, (start, end)
rep = rep[:start] + tbl + "\n" + rep[end:]
open("CONTENT_REVIEW.md", "w", encoding="utf-8", newline="\n").write(rep)
open("tools/content_review/compare.md", "w", encoding="utf-8", newline="\n").write(out)
print("chapter table refreshed")
