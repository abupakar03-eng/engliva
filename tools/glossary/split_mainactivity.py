#!/usr/bin/env python3
"""One-off: split MainActivity.kt into per-screen files.

Mechanical on purpose — it moves whole top-level declarations without editing
their bodies, converts `private` to `internal` on the ones that move, and gives
every generated file the original import header so nothing needs a new import.

Run with --dry-run to review the assignment first.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "app", "src", "main", "java", "com", "engliva", "MainActivity.kt")
UI = os.path.join(ROOT, "app", "src", "main", "java", "com", "engliva", "ui")

DECL = re.compile(r"^(private |internal |class |object |fun )")
COMMENT = re.compile(r"^\s*(/\*\*|\*|//|/\*)")

THEME = ["PrimaryBlue", "AccentAmber", "SuccessGreen", "ErrorRed", "SurfaceCard", "TamilInk",
         "LocalTamilLines", "LocalShowTamil", "TamilAudio", "LocalTamilAudio",
         "EnglivaTheme", "Quad", "Quint", "LoadingFull"]
BILINGUAL = ["BilingualText", "WordMeaningPopup"]
LESSON = ["TeacherScreen", "ConversationRolePlayScreen", "TurnBubble", "TurnRoleBadge",
          "LegacyDiscussionScreen", "TeacherBubble", "StructuredContent", "PhraseCard",
          "StructuredBlock", "StructuredQuestions", "StructuredTable", "ActivityTypeChip",
          "ActivityInstructionCard", "WordDiffCard", "FeedbackCard", "SttStatusRow", "ActionBar"]
COURSE = ["HomeScreen", "FeatureCard", "CourseOverviewScreen", "ModuleDetailScreen",
          "LessonsScreen", "ModuleExamCard", "SectionIntroCard", "LessonCard"]
PROGRESS = ["ResultScreen", "ProgressScreen", "ProgressRow", "SettingsScreen", "SettingsCard"]
KEEP = ["Routes", "NavItem", "navItems", "MainActivity", "SplashScreen", "EnglivaRoot"]

TARGETS = {}
for name in THEME: TARGETS[name] = "Theme.kt"
for name in BILINGUAL: TARGETS[name] = "BilingualText.kt"
for name in LESSON: TARGETS[name] = "LessonScreens.kt"
for name in COURSE: TARGETS[name] = "CourseScreens.kt"
for name in PROGRESS: TARGETS[name] = "ProgressScreens.kt"
for name in KEEP: TARGETS[name] = None          # stays in MainActivity.kt


def decl_name(decl_line):
    """Name from the declaration line itself, never from the body.

    Scanning the whole block found `onCreate` instead of `MainActivity`, which
    would have routed a class to the wrong file.
    """
    for pattern in (r"fun\s+([A-Za-z0-9_]+)", r"data class\s+([A-Za-z0-9_]+)",
                    r"object\s+([A-Za-z0-9_]+)", r"val\s+([A-Za-z0-9_]+)",
                    r"class\s+([A-Za-z0-9_]+)"):
        m = re.search(pattern, decl_line)
        if m:
            return m.group(1)
    return None


def main():
    dry = "--dry-run" in sys.argv
    lines = open(SRC, encoding="utf-8").read().split("\n")

    starts = [i for i, line in enumerate(lines) if DECL.match(line) and not line.startswith(" ")]
    # A declaration owns the annotations and KDoc sitting directly above it.
    adjusted = []
    for i in starts:
        j = i
        while j > 0 and (lines[j - 1].startswith("@") or COMMENT.match(lines[j - 1])):
            j -= 1
        adjusted.append((j, i))

    header_end = adjusted[0][0] if adjusted else len(lines)
    header = "\n".join(lines[:header_end])

    blocks = []
    for k, (start, decl_line) in enumerate(adjusted):
        end = adjusted[k + 1][0] if k + 1 < len(adjusted) else len(lines)
        text = "\n".join(lines[start:end]).rstrip() + "\n"
        name = decl_name(lines[decl_line])
        if name is None:
            print(f"FATAL: unnamed declaration at line {decl_line + 1}: {lines[decl_line][:70]}")
            return 1
        blocks.append((name, text))

    buckets, kept = {}, []
    for name, text in blocks:
        target = TARGETS.get(name, "UNMAPPED")
        if target is None:
            # LessonsScreen (CourseScreens.kt) navigates with Routes.HOME.
            if name == "Routes":
                text = text.replace("private object Routes", "internal object Routes", 1)
            kept.append(text)
        elif target == "UNMAPPED":
            print(f"FATAL: no target file for declaration '{name}'")
            return 1
        else:
            # Moved declarations must be visible from other files in the module.
            text = re.sub(r"^private ", "internal ", text, count=1, flags=re.M)
            buckets.setdefault(target, []).append(text)

    if dry:
        total = 0
        for target in sorted(buckets):
            print(f"{target}: {len(buckets[target])} declarations")
            total += len(buckets[target])
        print(f"moved: {total} declarations | kept: {len(kept)}")
        print("MainActivity.kt keeps:", ", ".join(
            decl_name(lines[d]) for _, d in adjusted
            if TARGETS.get(decl_name(lines[d]), "?") is None))
        return 0

    os.makedirs(UI, exist_ok=True)
    new_header = header.replace("package com.engliva\n", "package com.engliva.ui\n", 1)
    new_header = new_header.rstrip() + "\nimport com.engliva.Routes\n\n"
    for target, texts in buckets.items():
        path = os.path.join(UI, target)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_header + "\n" + "\n".join(texts))
        print("wrote", os.path.relpath(path, ROOT), len(texts), "declarations")

    # MainActivity keeps the header, the retained declarations, and the ui import.
    main_header = header.rstrip() + "\nimport com.engliva.ui.*\n\n"
    with open(SRC, "w", encoding="utf-8") as fh:
        fh.write(main_header + "\n" + "\n".join(kept))
    print("rewrote MainActivity.kt with", len(kept), "declarations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
