# tools/content_review

Tooling behind the lesson/chapter restructure described in
[`../../CONTENT_REVIEW.md`](../../CONTENT_REVIEW.md). Nothing here ships in the app;
the assets it edits do.

Everything is data-only: the scripts rewrite
`app/src/main/assets/{course,content,translations}.json` and never touch Kotlin or
JavaScript, so no runtime rule changes.

## Pipeline

```bash
git checkout HEAD -- app/src/main/assets      # pristine assets
python tools/content_review/restructure.py    # lesson + chapter transform
python tools/content_review/compose_translations.py
python tools/content_review/validate.py
```

| script | what it does |
|---|---|
| `restructure.py` | The transform. Explicit tables — `SECTION_TITLES`, `DEMOTE`, `ABSORB_TITLE`, `GROUPS`, `SPLIT_QUESTIONS`, `RETITLE`, `DROP_PARTS`, `DROP`, `MOVE`, `NEW_SECTIONS`, `REMOVE_SECTIONS` — then regenerates `course.json` days from the result. Writes `merge_manifest.json`. Refuses to run twice without `--force`. |
| `compose_translations.py` | Gives merged lessons a natural Tamil line by composing their components' existing translations (`"\n"`-joined, the convention the 37 existing multi-line entries already use). |
| `validate.py` | Python replica of `CourseContent.validate`, `CourseContent.sectionContent`/`sectionIntros` and the three `CourseContentTest` assertions, plus a schema check against `CourseModels.kt` and the `parts`-hiding checks. Exit 1 on any error. |
| `check_engine.py` | Extracts `precomputeSections` / `sectionContent` / `buildExamPlan` from `web/app.js` and runs them against the assets — the shipped web engine, not a re-implementation. |
| `exam_pools.py` | Module exam-pool sizes before/after. `buildExamPlan` only samples items of 20–300 chars, so merging short items shrinks a pool; this is how that gets caught. |
| `tamil_coverage.py` | User-visible Tamil coverage before/after, using the same lookup `Glossary.translate` and `tamilLine` perform. Counts what the screen renders (`parts` cell-by-cell when present, the raw text otherwise) — counting whole item texts overstates the gap. |
| `audit.py` | Chapter inventory + per-lesson item binding → `review.md`. |
| `dump_prose.py` | Writes every lesson text in day order to `prose_*.txt` (resolving each day through the same rule the runtime uses), for a manual proofread. |
| `fix_typos.py` | The proofreading fixes: minimal substring replacements applied to `content.json`, `course.json` and the `translations.json` **keys** (values untouched, so Tamil lines survive). `--check` prints each replacement's blast radius first. |
| `no_content_loss.py` | Proves every original item text still exists in the new `content.json` (kept, demoted, absorbed, or corrected by `fix_typos.py`). |
| `verify_apk.py` | Checks a built APK: every asset inside it is byte-identical to the repo copy, and the bundled content carries the new structure and the proofreading. Run after unzipping `assets/` out of the APK (see the script's header). |
| `compare.py` / `refresh_table.py` | Chapter-by-chapter before/after lesson counts, and the script that regenerates that table inside `CONTENT_REVIEW.md`. |
| `merge_manifest.json` | Generated: `[new content_id, [original content_ids]]` for every merge. |
| `backup/` | The pristine `course.json`, `content.json` and `translations.json` (identical to `git HEAD`), so the "before" side of every comparison is reproducible. |

## Verify the result

```bash
python tools/content_review/validate.py        # asset invariants + parts checks
python tools/content_review/check_engine.py    # every lesson resolves, every exam builds
python tools/content_review/exam_pools.py      # exam-pool health
python tools/content_review/tamil_coverage.py  # Tamil coverage before/after
node tools/glossary/check_web.mjs              # glossary / translation lookup
```

`check_web.mjs` fails on a pristine Windows checkout because `core.autocrlf=true`
gives `tools/glossary/words.txt` CRLF endings and the script splits on `"\n"`. That
is a pre-existing checkout artefact; normalise the file to LF (or fix the split) and
it passes.

`./gradlew :app:testDebugUnitTest` does not run here either — Gradle 9.1.0 is not in
the local cache and the wrapper cannot write its lock file under `~/.gradle`.
`validate.py` is the substitute: it mirrors the same assertions over the assets.
