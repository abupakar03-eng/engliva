# Lesson & chapter review — Englive course content

Reviewed and restructured: `app/src/main/assets/{course.json,content.json,translations.json}`.
**No Kotlin, no JavaScript and no runtime rule was changed** — the whole change is content data,
so every engine behaviour (positional lesson→item binding, `heading` exclusion,
`META_INTRO_SECTIONS` filtering, module-exam sampling) is untouched.

Verified against the source book `English_Book_Digitized.docx` (Heading 1/2/3 + table
structure) and against the shipped runtime rules, re-implemented exactly from
`CourseContent.kt`, `CourseRepository.kt` and `web/app.js`.

---

## Result at a glance

| | before | after |
|---|---|---|
| modules | 5 | 5 |
| chapters (sections) | 56 | 56 |
| days | 519 | 360 |
| lessons (non-exam) | 514 | 355 |
| canonical items | 593 | 473 |
| lessons that are scaffolding, not English content | 42 | 0 |
| lessons whose screen showed something other than their own text | 6 | 0 |
| duplicate lesson texts | 6 | 0 |
| original item texts deleted | — | **0** |

---

## What was wrong

### 1. Non-content lessons

42 lessons were book scaffolding that the runtime now excludes (retagged `heading`),
and 13 more became the chapter's orientation card. **No text was deleted** — a
`heading` item still carries its text, it just is not a lesson.

* **Teacher-facing notes and directions (6)** — Gratitude's aside to the teacher
  ("don't use Indianisms … this is the standard form"), Silent Letters' lead-in,
  the "Generally UG students can use commonly known words" commentary, "Observe"
  (`m3_sentence`), "Garland decoration" (an `Image Caption` in the docx),
  "Develop the following hints into stories".
* **Run-in sub-headings above a table (26)** — each was a lesson of its own *while
  the vocabulary table it names was a separate lesson*. The label is now the table
  lesson's title, so `m2_categories` reads "Medical Words", "Words Pertaining to
  Death", "Literary Words" instead of `WORDS DENOTING PHRASES AND SENTENCES · 21/32`.
  Same pattern removed from `m3_nouns` ("Noun in number", "We should always say:",
  "Exercise"), `m3_pronouns` ("Personal Pronouns"), `m3_adjectives`
  ("There are six kinds of adjectives."), `m3_adverb` ("Kinds of Adverb"),
  `m3_clauses` ("Adverb Clause"), `m3_prepositions` ("Kinds of prepositions",
  "The uses of at and in"), `m3_articles` ("Observe these sentences"),
  `m3_question_tags` ("Remember") and `m2_fun_words` ("A. Country | B. Currency").
* **10 conversational-function labels in `m1_farewell`** — "Surprise", "Expressing
  obligation", "Making suggestions" … They are an index of functions with no model
  sentences, and none is about farewell. Kept in the asset as one reference block.
* **Orientation content (13)** — the 5 reading-skill instructions in
  `m5_reading_intro` and the 8 requisition-format rules became their chapter's
  intro card, which is what the book's *Heading 2* + rules actually are.

### 2. Chapters that did not match the book

* **`m5_letters` (MODEL LETTERS) had 0 lessons.** It was built from the book's
  *Heading 1* "MODEL LETTERS", which is the parent of the "Requisitions" chapter, so
  it captured only that chapter's intro paragraph. Its 27 fragments are now **two
  complete model letters** and its intro paragraph plus the 8 format rules form the
  chapter's orientation card. The empty `m5_requisitions` chapter is gone.
* **`m4_passages` was titled "MODULE – IV: COMPREHENSION"** — the module heading, not
  a chapter name. Renamed to **Comprehension Passages**.
* **`m1_greetings` was titled with a note** ("A note on the expressions to be used on
  certain occasions"). Renamed to **Greetings and Introductions**.
* **Missing chapter split.** "DISTINCTIVE NAMES GIVEN TO THE YOUNG ONES OF ANIMALS"
  is a *Heading 3* in the book, but its table had been dumped into `m2_categories`.
  It is now the chapter `m2_young_ones`.
* **`m5_story_hints`** — "Garland decoration" and "Develop the following hints into
  stories" were lessons 1 and 2.
* 47 chapters were retitled to one consistent naming style (the book mixes ALL CAPS
  headings with sentence-case ones), and the 5 module titles from `CONVERSATION` to
  `Conversation`.

### 3. Lessons that were fragments of one unit
* **`m2_fun_words`: 73 lessons → 15.** One lesson per book exercise
  (I. Spot Out the Odd Word … X. The 26-Letter Crossword, Answers, Lemonade —
  Vocabulary Test). The exercise's direction, its answer key ("Answers:", "Cold : it
  is not a season"), its stray markers ("III.") and its figure captions
  ("Bottle puzzle", "Missing letters grid") were all separate lessons; they are now
  part of the exercise they belong to. The jumbled-letter items
  ("esroh — (name of an animal)") stay inside their exercise rather than being read
  aloud or graded as English.
* **Ten author bylines were lesson 1 of an article** — "By Naveen Chawla,
  page: 235", "Dr. Alan Loy Mc Ginnis", "By C. Raj Kumar, Courtesy "The Hindu"". Now
  part of the article they credit.
* **One fable split in half across two lessons.** `m4_passages` days 462-463 were
  the two paragraphs of the ant-and-dove story, cut mid-narrative.
* **The comprehension questions were mis-parsed, not missing.** Every comprehension
  item in the book is a passage with its questions on the following lines. The
  digitiser stored that as `parts.questions` — but question 1 held the **entire
  passage** plus the first question, and the last question was stored in the *answer*
  slot. Since the UI renders `parts` *instead of* the item text, the student saw a
  broken Q&A list and never saw the passage as a passage. Each item is now a clean
  **passage lesson + "… — Questions" lesson**, where the questions render as a
  numbered list.
* **Letter templates split into 8 fragments per letter**, with exact duplicates
  (`From [Your Address]`, `Respected Sir,`, `Thank You,`, `Yours Faithfully,
  Signature` each appeared twice). 27 lessons → 2 complete letters.
* **Incomplete lead-ins taught as their own lesson** — "Thanks is a very vital aspect
  of British manners. You say," (the phrases followed in the next lesson),
  "Simple Present: Used to express", "There are five kinds of nouns:",
  "In disorder → In order:".
* **6 byte-identical duplicate lesson texts** removed (5 in the letters, 1 duplicated
  tense exercise "The train had left before they (reached / had reached) the station.").

### 4. `parts` that hid the lesson (6 lessons)

`TeacherBubble` is `if (parts != null) StructuredContent(parts) else BilingualText(content)` —
so whenever an item carries `parts`, its own `text` is **not shown at all**. Merging a
lead-in into an item that had `parts` therefore hid the lead-in, and one pre-existing
item carried a `parts` that was never its own content:

* `c0011`, `c0027` — the "phrase" card held the *next* item's sentence, so the merged
  text was invisible (and duplicated what the next lesson already showed).
* `c0047`, `c0050`, `c0052`, `c0266` — the Q&A `parts` belonged to the examples, so
  merging the **rule** into them hid the rule.
* `c0313` (`Distributive Adjective`) — stored as three bogus "questions" in which
  question 1 held the whole lesson and the last question sat in the answer slot.
* `c0522`–`c0526` — the mis-parsed comprehension blocks described above.

The stale `parts` are dropped, so each lesson now renders its own full text, and the
mis-typed grammar item renders as the explanation it is. For merges where the survivor
is a **table**, the merge was replaced by the sub-heading pattern instead (the prose is
demoted and the table keeps its `parts`), so tables still render as tables.
`validate.py` now fails if any lesson's `parts` hides more than 60 characters of its
text, or if a `questions` block contains a passage or a question in the answer slot.

---

## Proofreading pass

All 355 lesson texts were read end to end and checked against
`English_Book_Digitized.docx`. **44 corrections** are applied by
`tools/content_review/fix_typos.py`; almost all of the errors are in the source book
itself, not digitisation damage.

Because `translations.json` is keyed by the exact English string, each fix renames the
matching key as well — so the natural Tamil lines survived and coverage is unchanged
(260 natural / 82 structured / 13 gloss, exactly as before the pass). Each replacement
was checked to occur only where it was meant to before being applied
(`fix_typos.py --check`), and the script is idempotent, so re-running it to add a fix
cannot double-apply one.

| kind | corrections |
|---|---|
| misspelt proper nouns | `Maxico`→Mexico, `New Zeeland`→New Zealand, `Kolkotta`→Kolkata, `Bagavat Gita`→Bhagavad Gita, `Abbe Sivam`→Anbe Sivam, `Sheeba`→Sheba, `Dr. Roa`→Rao |
| misspelt words | `Hanger`→Hangar, `Ironmanager`→Ironmonger, `bluge`→bulge, `cosumables`→consumables, `Knivers`→Knives, `Vermal`→Vermin, `A dare-evil`→dare-devil, `there`→three, `post man`→postman, `Every body`→Everybody, `a plenty`→plenty |
| wrong word | `conservation`→conversation, `A list of table`→`or table`, `for, off, in`→`for, of, in`, `connected which`→`connected with`, `Games(s)`→`Game(s)`, `tells his`→`tells him`, `once climbs up`→`one climbs up` |
| grammar / punctuation | `If its`→`If it’s`, `It’s long time`→`It’s a long time`, `I’ve an headache`→`a headache`, `areas … is`→`are`, `of a question are`→`is`, `threw`→`throw`, `the good one’s`→`the good ones`, `Economics class my`→`Economics class. My`, two answer lists missing their `1.` |
| chapter / lesson titles | `Kinds of Sentence(s)`, `Kinds of Noun(s)`, `Kinds of Pronoun(s)`, `Kinds of Adverb(s)`, `Question Tags — Remember`→`Points to Remember` |

### Found, but deliberately not changed

These need an editorial decision or cannot be resolved without guessing:

* **A wrong answer key.** The *Country and Currency* answers table still pairs
  `Burma | Cruzeiro`, `Canada | Kyat`, `Maxico | Dollar`, `New Zealand | Peso`,
  `Brazil | [Sterling]` — those five rows are the leftover options in A-order, not
  matches. The correct pairs are Burma–Kyat, Canada–Dollar, Mexico–Peso,
  New Zealand–Dollar, Brazil–Cruzeiro. (The country spellings are fixed; the pairings
  were left for you.)
* **Two adjective labels that contradict their own chapter.** "He is a man of few
  words. — (Adjective of quality)" and "Some dream of much reality. — (Adjective of
  quality)" — elsewhere the same chapter labels *much* as quantity and *many* as
  number.
* **OCR garble whose intended word cannot be determined**, so no minimal fix is
  defensible: `insurant`, `foran`, `portative`, `hyperaemia` (synonym/antonym
  distractors), `Dooton`, `Humplet`, `Hund` (match-the-pairs), `Bowet` (young of a
  hawk), `duce` (silent-`c` list).
* **Telegraphic composition hints left as written**: "a boy takes aim the dove bee
  stings", "asks the other what the bear", "two garlands of flower".
* **Names and variants I could not confirm**: `Kamal Hasan`, `Dr. Alan Loy Mc Ginnis`,
  `Tiruverambur`, `Swiss Development Central Co-operation`, `Bonafide`, `fiance`/
  `fiancee` (unaccented), `Kuran`, and lowercase `germany`/`christmas` inside
  pronunciation lists.

> **Follow-up this creates:** `words.txt` and `glossary.json` still describe the words
> the course *used* to contain, so corrected words such as `mexico`, `kolkata`,
> `hangar` and `ironmonger` have no glossary entry and appear untranslated inside the
> Tamil gloss line. `tools/glossary/extract_words.py` plus the glossary pass closes
> that.

---

## Chapter-by-chapter

<!-- generated by tools/content_review/compare.py -->

| chapter | lessons before → after | title |
|---|---|---|
| `m1_greetings` | 10 → **8** | Greetings and Introductions |
| `m1_gratitude` | 5 → **2** | *Gratitude* |
| `m1_wishes_festive` | 2 → **1** | Wishes at Celebrations and Festive Occasions |
| `m1_wishes_exams` | 1 | Wishes Before an Examination |
| `m1_condolences` | 2 → **1** | *Condolences* |
| `m1_farewell` | 13 → **3** | Farewell and Everyday Courtesies |
| `m1_expressions` | 2 | Some Common Expressions in English |
| `m1_framing_q` | 9 → **4** | Framing Questions |
| `m1_common_q` | 2 | Some Common Questions |
| `m1_profession` | 1 | What Is Your Profession? |
| `m1_casual_talk` | 1 | A Casual Talk Between Two Friends |
| `m1_games` | 2 | *Games* |
| `m1_holidays` | 2 | *Holidays* |
| `m1_impression` | 2 → **1** | My Impression of Tiruchy |
| `m1_political` | 1 | Write a Paragraph or Speak About a Political Leader |
| `m1_dialogues` | 9 | *Exercise — Scripted Dialogues* |
| `m2_introduction` | 1 | *Introduction to Vocabulary* |
| `m2_monosyllabic` | 1 | Words with One Speech Unit (Monosyllabic) |
| `m2_disyllabic` | 1 | Words with Two Speech Units (Disyllabic) |
| `m2_trisyllabic` | 1 | Words with Three Speech Units (Trisyllabic) |
| `m2_tetrasyllabic` | 1 | Words with Four Speech Units (Tetrasyllabic) |
| `m2_pentasyllabic` | 2 | Words with Five or More Speech Units |
| `m2_silent_letters` | 15 → **14** | Silent Letters |
| `m2_easier_vocab` | 2 → **1** | Take the Easier Route in Improving Your Vocabulary |
| `m2_figurative` | 1 | Figurative Expressions and Their Explanations |
| `m2_categories` | 32 → **16** | Words Denoting Phrases and Sentences |
| `m2_young_ones` | **new** → 1 | Distinctive Names Given to the Young Ones of Animals |
| `m2_confusables` | 4 | *Confusables* |
| `m2_troublesome` | 6 | Troublesome Words |
| `m2_fun_words` | 73 → **15** | Fun with Words |
| `m3_sentence` | 7 → **2** | The Sentence |
| `m3_kinds_sentence` | 13 → **5** | Kinds of Sentence |
| `m3_pos_intro` | 1 | Parts of Speech |
| `m3_nouns` | 21 → **16** | The Noun |
| `m3_pronouns` | 4 → **3** | The Pronoun |
| `m3_adjectives` | 13 → **12** | The Adjective |
| `m3_exercise_pos` | 2 → **1** | *Exercise — Parts of Speech* |
| `m3_verbs` | 7 | The Verb |
| `m3_subject_verb` | 21 | Agreement of Verb with the Subject |
| `m3_tenses` | 51 → **47** | Tenses |
| `m3_sequence` | 4 | The Sequence of Tenses |
| `m3_voice` | 25 | Voice |
| `m3_adverb` | 8 → **7** | The Adverb |
| `m3_clauses` | 27 → **26** | The Clause |
| `m3_prepositions` | 19 → **17** | Prepositions |
| `m3_articles` | 12 → **11** | Articles |
| `m3_question_tags` | 14 → **13** | Question Tags |
| `m4_passages` | 7 → **12** | Comprehension Passages |
| `m5_reading_intro` | 5 → **0** | How to Improve Your Reading Skill |
| `m5_corruption` | 2 → **1** | Corruption as Human Rights Violation |
| `m5_mother_teresa` | 2 → **1** | Mother Teresa |
| `m5_rural_managers` | 3 | Grooming India’s Rural Managers |
| `m5_women` | 4 → **3** | Are Women More Dependent on Relationships for Identity? |
| `m5_conflicts` | 4 | How Do You React to Conflicts? |
| `m5_letters` | 0 → **2** | Model Letters |
| `m5_story_hints` | 7 → **5** | Composition – B: Developing Hints |
| `m5_requisitions` | **27 → removed** | (content re-homed) |

`m4_passages` grows because each comprehension item became a passage **and** its
questions, which were previously buried in the passage text.

`m5_reading_intro` is the one chapter with no lessons: it is the book's
*Heading 2* "IMPROVE YOUR READING SKILL", whose only content is guidance for reading
the five passages that follow. That guidance is now the chapter's intro card — the
module screen renders a chapter that has only an intro, by design
(`CourseContent`/`CourseScreen`: *"Show the section as long as it has either lessons
or intros"*).

---

## Verification

`./gradlew :app:testDebugUnitTest` **could not be run in this environment** (Gradle
9.1.0 is not in the local cache and the wrapper cannot write to `~/.gradle`, so the
distribution cannot be fetched). The asset-level invariants those tests assert were
instead checked with an exact Python replica of the shipped code:

```
python tools/content_review/validate.py       # 0 errors, 0 warnings
python tools/content_review/check_engine.py   # 355 lessons resolve, 5 exams build
python tools/content_review/audit.py          # chapter inventory
python tools/content_review/exam_pools.py     # exam-pool health
python tools/content_review/tamil_coverage.py # user-visible Tamil coverage
python tools/content_review/no_content_loss.py
```

* **No content was deleted.** Every one of the 593 original item texts is still
  present verbatim in `content.json` — kept as a lesson, demoted to a `heading`, or
  absorbed into a merged/split item: **0 texts lost**, 83,304 → 83,356 characters.
* `CourseContent.validate` equivalent: course/content ids match, no duplicate day or
  item ids, every day's module and section exist, every activity wire is known, every
  chapter with days has items and enough of them. **0 problems.**
* `CourseContentTest.everyLessonResolvesToItsOwnItem` equivalent: every lesson
  resolves to a unique item — **0 lessons with no content, 0 repeated items.**
* `CourseContentTest.introSectionsStillSurfaceTheirContextParagraphs`: `m2_introduction`
  still surfaces 4 intro paragraphs.
* `CourseContentTest.sectionContentSkipsHeadings`: holds for `m1_greetings`.
* **A `parts` block can no longer hide a lesson**: nothing omits more than 60
  characters of its own text, and no `questions` block holds a passage or a question
  in its answer slot.
* `web/app.js`'s own `precomputeSections` / `sectionContent` / `buildExamPlan`
  extracted and run against the new assets: every lesson resolves, no chapter has more
  days than items, all 5 module exams build.
* `tools/glossary/check_web.mjs`: **`web OK: 3482 words resolve`**. (It only fails on a
  pristine Windows checkout because `core.autocrlf=true` gives `tools/glossary/words.txt`
  CRLF endings — a pre-existing checkout artefact, unrelated to this change.)

### Known trade-offs

* **Whole-line Tamil.** `translations.json` is keyed by the exact string the screen
  renders, so merging items creates new keys. Counting what a learner actually sees
  (`LessonScreens` renders `parts` cell-by-cell when present, and the raw text
  otherwise):

  | | before | after |
  |---|---|---|
  | lessons rendered from structured `parts` (each cell translated) | 91 | 82 |
  | lessons rendered from raw text, natural translation present | 423 | 260 |
  | lessons rendered from raw text, word-by-word glossary | 0 | 13 (3.7%) |

  Nothing is left untranslated — the glossary fallback still prints Tamil. The 13 are
  the long merged blocks (the comprehension passages, four merged grammar/phrase
  lessons, the re-joined ant story) plus question-sets whose source lines were never
  translated on their own. Where every component of a merge *did* have a translation it
  was composed automatically (+31 entries). Closing the last 13 needs a translation
  pass: `extract_strings.py` → `PROMPT_TRANSLATE.md` → `build_translations.py`. (The
  merge step only combines pre-generated chunks — it cannot translate new strings.)
* **Module-exam pools** (the engine samples items of 20–300 characters, so merging
  short items shrinks a pool). Every exam still builds, and the comprehension exam
  improves from 1 question to 6:

  | module | pool before | pool after | questions asked |
  |---|---|---|---|
  | `m1_conversation` | 47 | 25 | 10 |
  | `m2_vocabulary` | 112 | 43 | 10 |
  | `m3_grammar` | 220 | 194 | 10 |
  | `m4_comprehension` | 1 | 6 | 6 |
  | `m5_composition` | 33 | 6 | 6 |

  The `m5` drop is mostly *correct*: its old pool was padded with teacher
  instructions ("Read the following passages aloud.") and author bylines, which are
  poor recall questions. The remaining 6 are real content (3 article paragraphs and 3
  composition hints).
* **Day numbers were renumbered**, so any saved progress rows are invalidated
  (`ProgressStore` keys by day). Intended.
* **Module boundaries were deliberately left alone.** In the book, "MODEL LETTERS"
  and "COMPOSITION – B: DEVELOPING HINTS" are *Heading 1* — separate top-level parts —
  while the app keeps them inside module 5. Splitting them into modules would add
  module exams, i.e. a feature change, so it is reported here rather than made.

---

## Reproducing

```bash
git checkout HEAD -- app/src/main/assets      # start from the pristine assets
python tools/content_review/restructure.py    # the lesson/chapter transform
python tools/content_review/compose_translations.py
python tools/content_review/fix_typos.py      # the proofreading pass
python tools/content_review/validate.py
```

Order matters only in that `compose_translations.py` needs `restructure.py`'s
`merge_manifest.json`; `fix_typos.py` is idempotent and can be re-run at any time to
add a correction.

`restructure.py` is not idempotent and refuses a second run unless `--force` is
passed. It is built from explicit tables (`SECTION_TITLES`, `DEMOTE`,
`ABSORB_TITLE`, `GROUPS`, `SPLIT_QUESTIONS`, `RETITLE`, `DROP_PARTS`, `DROP`,
`MOVE`, `NEW_SECTIONS`, `REMOVE_SECTIONS`) rather than heuristics, so every edit is
reviewable in one file. See `tools/content_review/README.md`.

---

## Teacher-led lesson shape (all modules)

The app could always render a lesson as labelled cards, a Q&A list and a role play —
the content just never used it. **383 of 473 items rendered as one paragraph.** Now
every lesson that can be structured is:

| how a lesson renders | before | after |
|---|---|---|
| labelled blocks (`NOTE` / `EXAMPLE` / `RULE`) — one line per card, **each with its own Tamil line** | 0 | **299** |
| Q&A list (`Q1 … A`), with the model answers supplied | 22 | **65** |
| role-play conversation (`turns`) | 9 | **24** |
| table | 28 | 28 |
| still one paragraph | **383** | **18** (intro cards only — no lesson) |

**Every one of the 416 lessons now renders with its own natural Tamil line — 0 fall
back to the word-by-word gloss** (was 13, against 383 paragraphs). `text` is never
changed, so grading, TTS and the exam pools are untouched — only the display.

**46 chapters open with a teacher's note** ("Say each word aloud and notice the silent
letter.", "The verb must agree with the subject. Say the correct sentence aloud each
time."), in English and Tamil, rendered as the first `NOTE` card of the chapter.

### How the split keeps the Tamil

The natural Tamil line is stored against the whole lesson text, so splitting a lesson
would normally lose it. `tools/content_review/structure_all.py` splits the English and
the existing Tamil **the same way** — by newline, en-dash list, semicolon, or sentence
boundary — and only accepts a split when both sides produce the same number of pieces.
Measured over the course: 50 lessons split on newlines, 48 on sentences, 12 on
dashes/semicolons, and the rest stay whole so they keep their natural translation.

### Display fixes (code)

| file | change |
|---|---|
| `ui/CourseScreens.kt`, `web/app.js` | the lesson list shows `day.lessonTitle` instead of the placeholder `Lesson 3 of 5` — the numbered badge already shows the position |
| `ui/CourseScreens.kt` | the module header no longer prints `M1 CONVERSATION: Conversation`; just the title |

### Class flow — how the activities run

Every lesson now runs the same class, in the app's own activity vocabulary:

| the app's step | what the student does | marked |
|---|---|---|
| `listen` | the teacher reads it out — "just observe" | — |
| `listen_repeat` | says each line back after the teacher | ✓ |
| `read_aloud` | says the whole thing themselves | ✓ |
| `assessment` | **a Q&A lesson** → the app asks each question in turn; the answer is held back and what you say is graded against the model answer | ✓ |
| `assessment` | **short content** → the text blurs: "say it from memory", 👁 Peek if stuck | ✓ |
| `discussion` | role play — the teacher takes one part, the student the other, and **the student's lines are graded** | ✓ |

| lesson holds | sequence | lessons |
|---|---|---|
| short content (≤200 chars) | `listen → listen_repeat → read_aloud → assessment` (blurred memory check) | 225 |
| anything with a question to ask | `listen → read_aloud → assessment` — **one activity per question** | 167 |
| conversation | `discussion` | 24 |

**Every one of the 416 lessons now ends with a question the app asks and marks — 402
questions in all, asked one at a time.** No lesson just stops after a read-aloud.

### How a lesson gets its questions

Three sources, in order:

1. **The book's own Q&A** — a questions item whose every question has an answer
   (58 lessons). Module 4's comprehension questions gained their **30 model answers**
   here; they shipped with none.
2. **An authored `check`** — a new optional block on a lesson item:
   `"check": [{"q": …, "a": …}]`. Written for the 109 lessons whose content is prose —
   passages, compositions, grammar rules, and Module 1's teaching lessons
   (`tools/content_review/authored/checks.py`, plus a generator in
   `author_checks.py` that turns the book's own tables into questions, e.g. a
   `Word | Meaning` row becomes *"What does ‘kennel’ mean?"* with the book's meaning,
   in English and Tamil, as the model answer).
3. **The memory check** — short lessons the app already blurs.

The check step itself (`assessment` with `quizIndex`/`quizTotal`): the question is on
screen and read out by the teacher, the model answer sits behind a **👁 Show the
answer** button, and what the student says is graded against that one answer.

**Model answers offering alternatives.** Many answers are written the way a teachersays them — *"Good evening, Sir. / Good evening, Madam."* Grading that whole string
against one spoken answer scored a correct reply at **60%** and reported "Good
evening," as *not heard*. `quizQuestions()` now splits such an answer: the first
option is the expected answer and the rest are `acceptedAnswers`, which
`AnswerMatcher` already scored against and took the best of. The card still shows
both options. Measured after the fix:

| the student says | before | after |
|---|---|---|
| "Good evening, Madam." | 0.74 | **1.00** |
| "good evening sir or madam" | 0.60 | **0.72** |
| "good evening sir" | 0.94 | 0.94 |
| "banana banana" | 0.21 — still rejected | 0.21 |

**Grading a spoken answer, not a typed one.** `AnswerMatcher` compared answers with a
character edit distance. Speech to text writes the *same* answer many ways, so a
correct reply was failed:

> asked *"A friend asks 'How are you?' What do you answer?"*, the student said
> **"I am fine how are you"** — every word right — and scored **56%, "Not quite"**.

Scoring now takes the better of the character comparison and a **word-level** one,
with contractions expanded ("I'm" = "I am") and punctuation ignored:

| the student says | before | after |
|---|---|---|
| "I am fine how are you" | 0.56 — failed | **0.75 — passes** |
| "I'm fine, thank you. How are you?" | 1.00 | 1.00 |
| "how are you fine I am" (jumbled) | — | 0.25 — still fails |
| "I am fine" (incomplete) | — | 0.38 — still fails |
| "banana banana" | 0.16 | 0.16 — still fails |

The word comparison is order-sensitive, so a jumbled answer is rejected; and because
the two are combined with `max`, it only ever raises a score — nothing that used to
pass can now fail.

**Role plays were awarding a free 100.** The screen submitted a sentinel
(`__role_play_complete__`) once the turns ran out, and the activity had no expected
answer, so `AnswerMatcher` returned "Response recorded" with a full mark — a student
could tap *Skip* through every turn and still pass. The 24 conversation lessons now
carry the **student's own lines** as the expected answer, the screen collects what the
student actually said, and that is what is marked:

| the student | score |
|---|---|
| says every line | 1.00 |
| says half the lines | 0.68 |
| skips every turn | **0.00 — fails** (was 100) |

The role-play screen also said only *"Role Play"* in its header; it now shows the
lesson's own title ("Conversation: Meeting an Old Friend"), like every other screen.

---

**Two bugs this fixed.**

1. 258 of 416 lessons began with `teach`, which the app maps to **Read Aloud** — so the
   *student* was made to read first and no activity ever introduced the material.
   Every lesson now opens with the teacher. `speak` was also dropped from the practice
   step: on short content the app blurs `speak` exactly like `assessment`, so it was a
   second memory test where a read-aloud belonged.

2. The check step was not a check. The memory blur only applies to content of 200
   characters or less; past that the app showed the whole text again under the words
   *"Final check — read the passage aloud one more time to finish"* — for a lessons on
   greetings, which is not a passage. `assessment` is now used only where it really
   checks something:

   * **Q&A lessons became a real quiz** (new `quizIndex`/`quizTotal` on `LessonActivity`,
     `quizQuestions()` in `CourseRepository`, `ModelAnswerCard` + `QuizInstructionCard`
     in the UI, mirrored in `web/app.js` + `web/style.css`). A five-question practice
     lesson is now seven activities: listen, read aloud, then **Question 1 of 5 …
     Question 5 of 5** — the question on screen and read out, the model answer covered
     behind a **👁 Show the answer** button, and the student's spoken answer graded
     against that one model answer. **241 questions across the course are now asked and
     marked**, one at a time, instead of one blurred blob.
   * Where no check is possible, the misleading step is simply gone.

---

### Authored practice — complete

The mechanical pass makes every lesson *read* like a teacher's lesson. What the book
never supplies is an answer key (its exercises have none) and, outside Module 1, any
conversation at all. That is what was authored:

| module | what was added |
|---|---|
| **1 Conversation** | **15 of 16 chapters rewritten** as NOTE + EXAMPLE lines + practice Q&A with answers + a role play (47 lessons). The 16th chapter is the book's own 9 scripted dialogues, already conversations. |
| **2 Vocabulary** | a "Practice: …" Q&A lesson for all **14 chapters**, quoting the book's own answers |
| **3 Grammar** | Q&A for all **17 chapters** plus **8 conversations** (sentence kinds, nouns, subject–verb agreement, tenses, voice, prepositions, articles, question tags) |
| **4 Comprehension** | the **30 model answers** filled into the six existing "… — Questions" lessons — the questions shipped with no answers before |
| **5 Composition** | a "Practice: …" Q&A lesson for the five articles, the model letters and the story hints |

Sources: `tools/content_review/authored/module1.py`, `module1_more.py`, `module2.py`,
`module3.py`, `module45.py`, applied by `author.py` (whole chapters) and
`author_additions.py` (practice appended to existing chapters).

Conversations are not forced onto word-list chapters: where the topic cannot carry a
dialogue, the spoken practice is the Q&A drill itself.

---

## Android build (debug APK)
```
app/build/outputs/apk/debug/app-debug.apk   17.5 MB
com.engliva   versionName 1.0   minSdk 26   targetSdk 35   debug-signed
sha256 2283E2F4A149A75D2ECF08623322CFE2C069D8BB249D184899C8452EB2EE0C66
```

`tools/content_review/verify_apk.py` confirms all four asset files inside the APK are
**byte-identical** to the ones in the repo, and that the bundle carries the new
structure (5 modules, 56 chapters, 473 items, 360 days / 355 lessons + 5 exams, the new
`m2_young_ones` chapter, no `m5_requisitions`, 6 comprehension question lessons) and the
proofreading (`Mexico`, `Hangar`, `Ironmonger`, `Kolkata`… present; `Maxico`,
`Ironmanager`, `Kolkotta`… absent).

### Build-config fixes this required

The project had been set up on macOS and could not build anywhere else. Three minimal
changes (no app code touched):

| file | change | why |
|---|---|---|
| `gradle.properties` | commented out `org.gradle.java.home=/Applications/Android Studio.app/Contents/jbr/Contents/Home` | a hardcoded macOS JDK path — Gradle refused to start with *"Java home supplied is invalid"*. The JDK should come from `JAVA_HOME` / the IDE. |
| `gradle/wrapper/gradle-wrapper.properties` | `gradle-9.1.0-all.zip` → `gradle-8.14.3-all.zip` | AGP **8.6.1** does not support Gradle 9; and 9.1.0 was not available locally. 8.14.3 is both compatible and already cached. |
| `app/build.gradle.kts` | `VERSION_21` / `jvmToolchain(21)` → `17` | only JDK 17 is installed here. AGP 8.6 requires JDK 17+, so 17 is a valid baseline. Restore 21 (and uncomment the `java.home` line, or set `JAVA_HOME`) on a machine that has JDK 21. |

`local.properties` (`sdk.dir`) is machine-local and git-ignored; it was created for this
machine. On a machine with Android Studio none of this is needed beyond the
`java.home` line, which was the actual blocker for everyone but the original author.

A **release** APK/AAB is not possible yet: the project has no `signingConfigs` block, so
only the debug keystore signs the output. Add one before publishing.
