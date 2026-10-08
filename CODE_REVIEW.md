# Englive — Code Review

Reviewed: `app/src/main/java/com/engliva/**` (Kotlin/Compose, 11 files, ~3.5k LOC), `app/src/test/**`,
`web/` (JS mirror), `app/src/main/assets/{course,content}.json`, Gradle config and manifest.

**How this was verified**

* `./gradlew :app:testDebugUnitTest --offline` on the current tree → **24 tests, 2 failed** (`:app:testDebugUnitTest` FAILED).
  * `LessonEngineTest.lessonScoreIsAverageOfActivityScores` — `expected:<95> but was:<92>`
  * `AnswerMatcherTest.similarityOnlyAppliesWhenConfigured` — `AssertionError` at `AnswerMatcherTest.kt:8`
* Scripted checks against the shipped assets: 511 days / 593 canonical items, 0 duplicate day IDs, 0 broken
  section/module references, 0 sections with more days than teachable items, 0 items containing `'` or `"`.
* All findings below are from reading the source; nothing was changed.

---

## 1. Blockers

### 1.1 The test suite is red, and it is red for a real reason
`LessonEngine.kt:40` computes the activity score itself:

```kotlin
val activityScore = (evaluation.score - (attempts - 1) * 15).coerceIn(0, 100)
```

but `ScoringEngine.kt` — which exists, is injected into `LessonEngine`, and is unit-tested — specifies
`100 - (attempts - 1) * 10` with a floor of 50. Nothing calls it. So the second-try score is 85, not 90, and
`LessonEngineTest` (which asserts 95 for the lesson average) fails with 92. Pick one owner of the scoring rule
and delete the other; right now the tested behaviour and the shipped behaviour are different functions.

`AnswerMatcherTest.kt:8` asserts that `evaluate("helo", "hello", accepted = [], threshold = null)` is **not**
correct — i.e. "similarity is only applied when configured". `AnswerMatcher.kt:18` instead treats `null` as
`0.7`, so it passes. Either the default should be "no fuzzy matching when the caller didn't ask for it", or the
test is wrong — but a red suite means nobody can tell a new regression from the two known ones.

### 1.2 "Retry Lesson" resumes at the last activity and hands out a free pass
On completion the engine saves `activityIndex = activities.size` (`LessonEngine.kt:105` → `CourseEngine.save`
`:68`). `CourseEngine.start` (`:22`) then feeds that back into `LessonEngine.start` on the next start, which clamps
it to `lastIndex` (`LessonEngine.kt:20`). So pressing **Retry Lesson** (`MainActivity.kt:767`,
`web/app.js:839`) drops the student on the *final* activity with `activityScores` empty:

* last activity answered correctly on the retry → one score of 85–100 → **the failed lesson "passes"**, at 80%
  required, without redoing the lesson;
* if the saved `attempts` was already 3, the restored attempt count costs another 15 points, so a *perfect* read
  scores 55 and the lesson cannot be passed at all.

`attempts` is restored the same way (`CourseEngine.kt:62`), which is the second half of the bug. Restore should be
skipped (or reset to index 0) whenever the stored row is `completed = true`, and `attempts` should never be
restored across a fresh attempt at an activity.

### 1.3 `activityScores` is never persisted
`LessonSession.activityScores` lives only in memory; `CourseEngine.save` (`:68-84`) writes index, attempts, score
and recognised text. Every `restore()` therefore rebuilds the session with an empty list, so:

* `totalScore` is 0 for a part-finished lesson, and `save` overwrites the stored `score` with that 0 (`:78`) —
  work already graded is silently erased;
* completing a resumed lesson averages only the activities answered *after* the resume, so the score is both
  inflated and unrelated to the lesson as a whole (see 1.2).

Persist the per-activity scores (or a running sum + count) with the row.

### 1.4 Android: "say it from memory" is only enforced for the first activity
`MainActivity.kt:1064/1067/1076` key `remember`/`LaunchedEffect` on `activity?.sourceContentId` — but in
`CourseRepository.plan` (`:187-213`) *every* activity in a lesson is built from the same canonical item, so that
key is constant for the whole lesson. Consequences:

* `revealed` is set once (`:1072-1074`) and never reset → after the first graded activity, the blur is off for
  every later Speak/Assessment activity, which is exactly the recall mechanic the code is trying to build;
* `typed` is never reset → an answer typed for one writing activity is pre-filled in the next;
* the auto-speak effect (`:1067`) fires once per lesson instead of once per activity, so a later
  `listen_repeat`/`read_aloud` activity starts silent.

The web mirror gets this right by keying on the activity index (`web/app.js:671`). Key on
`session.activityIndex` (plus content id, if you want both).

---

## 2. High

### 2.1 Navigation dead-ends on a spinner after completion
`EnglivaRoot` reacts to the session with `LaunchedEffect(session)` and `nav.navigate(...)`
(`MainActivity.kt:246-254`), leaving TEACHER on the back stack under RESULT. System Back from the result screen
returns to `TeacherScreen`, whose first branch renders `LoadingFull()` for a completed session (`:1079-1082`). The
key (`session`) hasn't changed, so the effect does not re-fire and the user sits on a spinner. Each Retry also
pushes a fresh TEACHER + RESULT pair, so the stack grows with every attempt. Use
`navigate(RESULT) { popUpTo(TEACHER) { inclusive = true } }` or make the lesson a single route whose content
switches on status.

### 2.2 Role play scores 100 for everyone (and the two clients disagree)
`plan()` builds RolePlay/Discussion activities without `expectedAnswer` (`CourseRepository.kt:192-210`), and
`AnswerMatcher.evaluate` returns `correct = true, score = 100` when there are no candidates (`:14-16`).
`ConversationRolePlayScreen` submits the sentinel `"__role_play_complete__"` (`MainActivity.kt:1271`), so every
role play contributes 100% no matter what the student said — it inflates the lesson average and the pass rate.
The web client records *no* score for the same activity (`web/app.js:748` calls `advance()` directly), so the two
platforms compute different totals for the same lesson. Decide: grade per turn, or mark it ungraded and exclude it
from the average in the UI.

### 2.3 Web: lesson text is interpolated into inline `onclick` attributes unescaped
`web/app.js:519` (`onclick='...JSON.stringify(intros...)'`) and `:703`
(`onclick="speakTeacher(${JSON.stringify(a.content)})"`) put raw content into an HTML attribute. A `'` in the
first, or a `"` in the second, terminates the attribute and breaks the handler; it is also a markup-injection
foothold. I checked the shipped `content.json`: 0 of 593 items contain either character, so this is **latent**,
not live — but the file is generated, `escapeHtml` exists two lines away (`:898`) precisely because this text is
not trusted, and `sec.title` (`:521`) is unescaped while its neighbours are. Prefer `addEventListener` with the
text passed as data, or escape for the attribute context.

### 2.4 Web: going back re-counts an activity
`previousActivity()` (`web/app.js:242-250`) resets index/attempts/feedback but never trims `s.scores`, whereas the
Android engine deliberately drops the tail (`LessonEngine.kt:84-97`). On the web, backing up and answering again
adds a second score for the same activity, so the reported total drifts upward. Mirror the trim.

### 2.5 App-scoped speech engines are closed by a ViewModel
`EnglivaViewModel.onCleared()` calls `teacher.close()` / `student.close()` (`:116-120`), but those instances are
owned by `AppContainer` (application lifetime) and handed to every future ViewModel. Once one ViewModel is
cleared, the container keeps serving shut-down engines → TTS and mic silently no-op for the rest of the process.
Either construct the speech engines per ViewModel or don't close application-scoped singletons.

---

## 3. Medium

* **`validate()` doesn't cover the failures the app actually hits.** `CourseRepository.kt:49-86` checks
  duplicate IDs, missing sections/modules and unknown wires — but not an empty `activitySequence` (yields a plan
  with zero activities and a `LessonStatus.Error` session), not "section has no teachable content after
  filtering" (surfaces later as an error banner from `plan()`), and not `lessonEngine.sequence`
  (`course.json` advertises `"practice"`, which is not an `ActivityType` and is used by no day). These are one
  loop each and would move a runtime tap-time failure to load time.
* **Every lesson start writes a progress row** (`CourseEngine.kt:64` → `save`). Cards immediately read
  "Activity 0 of N" and the Progress screen lists lessons the student only looked at, indistinguishable from real
  partial work. Persist on first submit/advance, or store a distinct "opened" state.
* **Ungraded vs graded is inconsistent for `Listen`.** Neither client submits a Listen activity, so it stays
  unscored while its neighbours score — fine, but it is undocumented and the `Listen` instruction card says
  "just observe" while the web action bar offers "I heard it ✓". Worth a comment that non-speaking activities are
  deliberately excluded from the average.
* **Item↔day binding is positional.** `plan()` picks the item by counting prior days in the section
  (`CourseRepository.kt:186-187`). It happens to line up today (I verified: 0 sections have more days than
  teachable items), but any reordering or deletion of a day silently re-binds every later lesson to the wrong
  text. `ContentSelection` already carries a `sectionId` field that is unused — an explicit `content_id` per day
  would make this robust and let `validate()` check it.
* **Magic numbers drift between the two implementations.** Retry penalty 15 vs `ScoringEngine`'s 10
  (`LessonEngine.kt:40`, `ScoringEngine.kt:2`); max attempts 3 in `RetryEngine` but hardcoded as
  `s.attempts < 3` in `web/app.js:218`; exam pass mark 60 written independently in three places
  (`CourseRepository.kt:264`, `MainActivity.kt:858`, `web/app.js:534`). Note also that `RetryEngine`'s default of
  3 is never exercised by a test, because `LessonEngineTest` passes 3 explicitly.
* **Off-by-one in the progress copy.** `ModuleDetailScreen` shows `Activity $actIdx of N` with a 0-based
  `activityIndex` (`MainActivity.kt:1012`), while the teacher screen shows `index + 1` (`:1126`). Same for the
  Progress screen (`:2244`). A student who has answered two activities sees "Activity 1 of 4".
* **`String.format("%.1f", ttsSpeed)`** (`MainActivity.kt:2339`) uses the default locale → "0,9×" in
  comma-decimal locales. Pass `Locale.US`.
* **`android:allowBackup="true"`** with an unencrypted Room DB holding progress and recognised speech text;
  either exclude the DB or accept it explicitly.

---

## 4. Low / hygiene

* `MainActivity.kt` is 2,375 lines — the Activity, theme, nav graph, splash and ~30 screens/leaf composables in
  one file. Split by screen (`ui/home`, `ui/lesson`, …); it also makes the four navigation bugs above much easier
  to see.
* Dead code that survived a refactor: `LessonsScreen` (`MainActivity.kt:803-846`, never routed — `Routes.LESSONS`
  renders `CourseOverviewScreen`), `SettingsCard` (`:2350-2366`), `ScoringEngine` (whole file),
  `CourseEngine.resume` (`:26-35`), `LessonStatus.Starting/Listening/Evaluating`,
  `LessonActivity.acceptedAnswers` (never populated), `ContentSelection.selectionMode`, and
  `sectionContent`'s legacy positional fallback (`CourseRepository.kt:117-158`) — all 593 shipped items carry
  `section_id`, so that path is unreachable and it is the most intricate code in the file.
* `EnglivaTheme` passes `typography = MaterialTheme.typography` (`MainActivity.kt:146`) — a no-op read of the
  outer theme. Light-only scheme, so dark mode is unhandled.
* Several icon-only `IconButton`s pass `contentDescription = null` (mute, chevrons, replay) and emoji is the only
  label on others; there are no instrumented/UI tests and no Compose previews.
* `EnglivaViewModel.init` ends with `(d as LoadResult.Failure).reason` (`:76`) — sound for today's two-case
  sealed type, but a `when` that binds the failure is safer than a cast.
* Room has no `fallbackToDestructiveMigration` and no migration test; fine at `version = 1`, a crash waiting on
  the first schema change.
* `web/` reaches into `../app/src/main/assets/*.json` at runtime, so it only works when serving the repo root
  (the load-error message in `app.js:901` explains this well). A copy step at build time would decouple the two
  clients.
* `web/app.js` hand-mirrors the engine, matcher and section filtering and has already drifted (2.2, 2.4);
  consider generating it or keeping the shared rules in one spec with tests on both sides.
* Naming: manifest label `Englive`, splash `ENGLIVE`, package/classes `Engliva`, web title `Englive`. Pick one.

---

## 5. What is good

* Clean domain modelling: sealed `ActivityType`/`LessonStatus`, immutable `LessonSession`, typed status
  transitions, and pure engine components that are genuinely unit-testable (`LessonEngine`, `AnswerMatcher`,
  `RetryEngine`).
* Offline-first and honest about it: bundled content, no `INTERNET` permission, `usesCleartextTraffic="false"`.
* `SpeechEngines.kt` shows real device-hardening: main-thread marshalling for `SpeechRecognizer`, recognizer
  teardown after every result/error, defensive TTS chunking at `getMaxSpeechInputLength()`, and the
  `speakableText` rewrites so "etc." isn't read as "e t c".
* Permission flow is thoughtful — `pendingMicAction` starts listening immediately after Allow instead of making
  the student tap twice.
* Asset validation runs at load and surfaces errors in the UI rather than crashing.
* Content and data actually line up: 511 days, no duplicate day IDs, no dangling section/module references, no
  section with more days than teachable items.

---

## 6. Suggested order

1. Make the suite green — one owner for scoring, settle the `threshold = null` contract (1.1).
2. Fix session restore: don't resume a completed lesson, reset `attempts`, persist `activityScores` (1.2, 1.3).
3. Key the lesson UI on the activity, not the content id (1.4).
4. Fix completion navigation / back stack (2.1).
5. Decide how role play and discussion are scored, then make both clients match (2.2, 2.4).
6. Harden the web render path against content containing quotes (2.3).
7. Extend `validate()` to the failure modes that currently appear at tap time (3).
8. Then the dead-code/refactor pass.
