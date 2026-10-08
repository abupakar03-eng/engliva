# Glossary generation task

You are generating part of an **offline Tamil glossary** for an English-learning app used by
Tamil-speaking students in India (college beginners). The glossary is a plain lookup table:
English word in, Tamil meaning out. A student taps any word in a lesson and sees the meaning.

You will be given one **chunk id** (for example `00`). Work only on that chunk.

## Input

`tools/glossary/chunks/chunk_<ID>.json` — a JSON array of lowercase English words.
Some entries are proper nouns, abbreviations, or OCR noise from the scanned textbook.

## Output

`tools/glossary/out/chunk_<ID>.json` — a single JSON **object** (double-quoted keys/values)
mapping *every* word in the input array to its Tamil meaning. Write it with the `write` tool.

The key set must **exactly** equal the input array: every word present, no extra keys, no
missing keys. Keys stay lowercase, exactly as given. Before writing, count both sets and fix
any mismatch.

## Tamil style — this is the important part

Use **everyday spoken Tamil (பேச்சுத் தமிழ்)** — the way people actually talk. Do **not** use
literary or formal Tamil (செந்தமிழ் / Sanskritised Tamil).

| Use (spoken) | Avoid (literary) |
| --- | --- |
| சாப்பிடு | உண், அசனம், புஜிக்க |
| பணம் | தனம், பொருள் (for money) |
| வீடு | இல்லம், நிலயம் |
| போ / வா / பார் / சொல் / கேள் | செல் / வருக / காண் / உரை / ஆலிசு |
| நல்ல | உத்தம |
| நிறைய | அதிகம் (fine, but "நிறைய" is more spoken) |
| ஏன் | எதற்கு (fine), ஏனெனில் (literary) |

Format rules for each value:

* 1–3 Tamil words. No sentences, no explanations, no grammar notes.
* **Tamil script only.** No Latin letters, no transliteration like "sappidu".
* Allowed characters in a value: Tamil script, space, `,` `-` `/` `.` `?`
* For grammar/function words give the Tamil equivalent: `the` → அந்த, `is` → இருக்கிறது,
  `of` → -இன், `and` → மற்றும், `not` → இல்லை, `to` → -க்கு, `a` → ஒரு.
* Verbs keep the tense of the given form: `walked` → நடந்தார், `walking` → நடந்து
  கொண்டிருக்கிறார், `walks` → நடக்கிறார்.
* Plurals get the plural: `teachers` → ஆசிரியர்கள்.
* Proper nouns and place names: transliterate into Tamil script (`delhi` → டெல்லி,
  `teresa` → தெரேசா).
* Abbreviations: give the spoken expansion (`etc` → இத்யாதி, `dr` → டாக்டர்).
* If a token is not a real English word (OCR noise such as `aaahlmtj`), use exactly:
  `புரியாத சொல்`

## Worked examples

```json
{
  "the": "அந்த",
  "eat": "சாப்பிடு",
  "money": "பணம்",
  "house": "வீடு",
  "walked": "நடந்தார்",
  "teachers": "ஆசிரியர்கள்",
  "beautiful": "அழகான",
  "delhi": "டெல்லி",
  "aaahlmtj": "புரியாத சொல்",
  "is": "இருக்கிறது",
  "of": "-இன்",
  "don't": "வேண்டாம்",
  "etc": "இத்யாதி"
}
```

## Reply

After the file is written and validated, reply with exactly one line:

```
chunk_<ID> ok: <number of keys>
```

If you cannot complete the chunk, reply with `chunk_<ID> FAILED: <reason>` instead.
