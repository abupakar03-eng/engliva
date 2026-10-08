# Tamil translation task

You are translating lesson lines for an **English-learning app for Tamil-speaking college
beginners**. Every English line the app shows must have a Tamil translation printed directly
underneath it, so the student never has to tap anything.

You will be given one **chunk id** (for example `00`). Work only on that chunk.

## Input

`tools/glossary/string_chunks/tchunk_<ID>.json` — a JSON **array** of English strings: lesson
phrases, full sentences, vocabulary lists, grammar rules, reading passages and dialogue lines.

## Output

`tools/glossary/translations_out/tchunk_<ID>.json` — a JSON **array of Tamil strings**, with
**exactly the same length and order** as the input array. Item 7 of your output is the
translation of item 7 of the input. Write it with the `write` tool.

Do **not** output an object and do **not** include the English text — a parallel array only.
The one structural rule that matters: `len(output) == len(input)`.

## Translation rules

* **Translate the meaning of the whole line, not word-by-word.** Use natural, everyday spoken
  Tamil (பேச்சுத் தமிழ்) — the way a teacher explains something to a student. Not literary Tamil.
* Tamil script only, with these exceptions:
  * **English grammar terms stay in English** where a Tamil speaker would say them in English:
    article, noun, verb, tense, preposition, pronoun, passive voice, clause, etc.
    Example: `'The' ஒரு definite article (குறிப்பிட்ட ஒன்றைக் குறிக்கும் சொல்).`
  * **The English word being taught stays in English**, with the Tamil meaning beside it:
    `"Accessory means additional."` → `Accessory என்றால் கூடுதல் பொருள்.`
  * **Names and places transliterate into Tamil script**: `Raju` → ராஜு,
    `Mother Teresa` → மதர் தெரேசா, `Skopje` → ஸ்கோப்ஜே.
* **Vocabulary lists** (`Ace, bay, cow, god, day, five`) — give each word's Tamil meaning in the
  same order: `ஏஸ், பே, பசு, கடவுள், நாள், ஐந்து`.
* Keep numbering and markers exactly (`1.`, `a)`, `b)`, bullets). Keep quotes where they carry
  meaning. Keep the input's paragraph breaks, written as `\n` escapes inside the JSON string.
* Do not leave a value empty, and never leave the whole line untranslated. Every value must
  contain at least one Tamil character.
* Do not add notes, brackets explaining your choice, or transliteration of Tamil in Latin letters.

## Worked examples

| English | Tamil |
| --- | --- |
| Good morning Sir / Madam / Raju etc. | காலை வணக்கம் சார் / மேடம் / ராஜு இத்யாதி. |
| On meeting a person for the first time in the day the usual greeting | ஒருவரை அன்றைய தினம் முதல் முறையாகச் சந்திக்கும்போது சொல்வது வழக்கமான வாழ்த்து. |
| 'The' is a definite article. It is used: | 'The' ஒரு definite article (குறிப்பிட்ட ஒன்றைக் குறிக்கும் சொல்). இதை இப்படிப் பயன்படுத்துவார்கள்: |
| Mother Teresa was born in Skopje. | மதர் தெரேசா ஸ்கோப்ஜேயில் பிறந்தார். |
| Accessory means additional. | Accessory என்றால் கூடுதல் பொருள். |
| Ace, bay, cow, god, day, five | ஏஸ், பே, பசு, கடவுள், நாள், ஐந்து |

## Reply

After the file is written, validate with a quick script or by eye that the array length matches,
then reply with exactly one line:

```
tchunk_<ID> ok: <number of strings>
```

If you cannot complete the chunk, reply `tchunk_<ID> FAILED: <reason>` instead.
