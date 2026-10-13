"""Restructure the shipped lessons (days) and chapters (sections).

DATA-ONLY: rewrites app/src/main/assets/{course,content}.json. No Kotlin/JS is
touched, so every runtime rule (positional item binding, heading exclusion,
META_INTRO filtering, exam sampling) is unchanged.

Run:  python tools/content_review/restructure.py [--dry-run]
"""
import json
import os
import re
import shutil
import sys
from collections import OrderedDict, defaultdict

ROOT = "app/src/main/assets"
COURSE = f"{ROOT}/course.json"
CONTENT = f"{ROOT}/content.json"

# ─────────────────────────────────────────────────────────────────────────────
# 1. Chapter (section) titles, normalised to one naming style.
# ─────────────────────────────────────────────────────────────────────────────
SECTION_TITLES = {
    "m1_greetings": "Greetings and Introductions",
    "m1_gratitude": "Gratitude",
    "m1_wishes_festive": "Wishes at Celebrations and Festive Occasions",
    "m1_wishes_exams": "Wishes Before an Examination",
    "m1_condolences": "Condolences",
    "m1_farewell": "Farewell and Everyday Courtesies",
    "m1_expressions": "Some Common Expressions in English",
    "m1_framing_q": "Framing Questions",
    "m1_common_q": "Some Common Questions",
    "m1_profession": "What Is Your Profession?",
    "m1_casual_talk": "A Casual Talk Between Two Friends",
    "m1_games": "Games",
    "m1_holidays": "Holidays",
    "m1_impression": "My Impression of Tiruchy",
    "m1_political": "Write a Paragraph or Speak About a Political Leader",
    "m1_dialogues": "Exercise — Scripted Dialogues",
    "m2_introduction": "Introduction to Vocabulary",
    "m2_monosyllabic": "Words with One Speech Unit (Monosyllabic)",
    "m2_disyllabic": "Words with Two Speech Units (Disyllabic)",
    "m2_trisyllabic": "Words with Three Speech Units (Trisyllabic)",
    "m2_tetrasyllabic": "Words with Four Speech Units (Tetrasyllabic)",
    "m2_pentasyllabic": "Words with Five or More Speech Units",
    "m2_silent_letters": "Silent Letters",
    "m2_easier_vocab": "Take the Easier Route in Improving Your Vocabulary",
    "m2_figurative": "Figurative Expressions and Their Explanations",
    "m2_categories": "Words Denoting Phrases and Sentences",
    "m2_young_ones": "Distinctive Names Given to the Young Ones of Animals",
    "m2_confusables": "Confusables",
    "m2_troublesome": "Troublesome Words",
    "m2_fun_words": "Fun with Words",
    "m3_sentence": "The Sentence",
    "m3_kinds_sentence": "Kinds of Sentence",
    "m3_pos_intro": "Parts of Speech",
    "m3_nouns": "The Noun",
    "m3_pronouns": "The Pronoun",
    "m3_adjectives": "The Adjective",
    "m3_exercise_pos": "Exercise — Parts of Speech",
    "m3_verbs": "The Verb",
    "m3_subject_verb": "Agreement of Verb with the Subject",
    "m3_tenses": "Tenses",
    "m3_sequence": "The Sequence of Tenses",
    "m3_voice": "Voice",
    "m3_adverb": "The Adverb",
    "m3_clauses": "The Clause",
    "m3_prepositions": "Prepositions",
    "m3_articles": "Articles",
    "m3_question_tags": "Question Tags",
    "m4_passages": "Comprehension Passages",
    "m5_reading_intro": "How to Improve Your Reading Skill",
    "m5_corruption": "Corruption as Human Rights Violation",
    "m5_mother_teresa": "Mother Teresa",
    "m5_rural_managers": "Grooming India’s Rural Managers",
    "m5_women": "Are Women More Dependent on Relationships for Identity?",
    "m5_conflicts": "How Do You React to Conflicts?",
    "m5_letters": "Model Letters",
    "m5_story_hints": "Composition – B: Developing Hints",
}

MODULE_TITLES = {
    "m1_conversation": "Conversation",
    "m2_vocabulary": "Vocabulary",
    "m3_grammar": "Grammar",
    "m4_comprehension": "Comprehension",
    "m5_composition": "Composition",
}

# New chapter, inserted after `after` inside `module`.
NEW_SECTIONS = [
    dict(section_id="m2_young_ones", title=SECTION_TITLES["m2_young_ones"],
         module_id="m2_vocabulary", after="m2_categories"),
]

# Chapters removed from the course browser; their items are re-homed.
REMOVE_SECTIONS = {"m5_requisitions": "m5_letters"}

# ─────────────────────────────────────────────────────────────────────────────
# 2. Item operations.
# ─────────────────────────────────────────────────────────────────────────────

# 2a. DEMOTE — an item that is not teachable on its own (teacher asides,
#     exercise fragments, section scaffolding, table sub-headings that are
#     folded into the following lesson's title). Becomes `type: heading`,
#     which `sectionContent` already excludes; the text stays in the asset.
DEMOTE = [
    "c0020",   # Gratitude — parenthetical note to the teacher
    "c0114",   # Silent Letters — chapter lead-in sentence
    "c0130",   # Easier Vocab — commentary for the teacher
    "c0258",   # Sentence — "Observe"
    "c0587",   # Developing Hints — figure caption "Garland decoration"
    "c0588",   # Developing Hints — "Develop the following hints into stories"
    "c0558",   # Requisitions heading (moved into Model Letters)
]

# Sub-heading -> the lesson it names. The sub-heading is demoted and the
# lesson takes its text as the lesson title.
ABSORB_TITLE = [
    # m2_categories: run-in sub-headings before each vocabulary table
    ("c0135", "c0136", "Words Denoting Numbers"),
    ("c0137", "c0138", "Words Denoting Places"),
    ("c0139", "c0140", "Words Denoting Professions or Trade"),
    ("c0141", "c0142", "Names Given to Persons with Certain Characteristics"),
    ("c0143", "c0144", "Words Pertaining to Government"),
    ("c0145", "c0146", "Words Pertaining to the Church"),
    ("c0147", "c0148", "Pertaining to Marriage"),
    ("c0149", "c0150", "Pertaining to Government and Trade"),
    ("c0151", "c0152", "Literary Words"),
    ("c0153", "c0154", "Miscellaneous Words"),
    ("c0155", "c0156", "Medical Words"),
    ("c0157", "c0158", "Words Pertaining to Death"),
    ("c0159", "c0160", "Nature Study"),
    ("c0164", "c0165", "Distinctive Sounds of Birds and Animals"),
    ("c0161", "c0162", "Gender"),
    # m2_fun_words: the direction above a table is not a lesson; the table is.
    ("c0199", "c0200", "III. Relate the Given Word with Games"),
    ("c0201", "c0202", "IV. Match the Words with Their Countries"),
    ("c0245", "c0247", "Exercise Your Vocabulary"),
    ("c0246", "c0247", "Exercise Your Vocabulary"),
    ("c0321", "c0322", "Exercise — Parts of Speech"),
    # m2_fun_words
    ("c0243", "c0244", "Country and Currency"),
    # m3 chapters
    ("c0289", "c0290", "Noun in Number"),
    ("c0296", "c0297", "Correct Usage — Wrong and Right"),
    ("c0299", "c0300", "Exercise: Choose the Correct Form"),
    ("c0303", "c0304", "Personal Pronouns"),
    ("c0438", "c0439", "Kinds of Adverb"),
    ("c0464", "c0465", "Adverb Clause"),
    ("c0475", "c0476", "Kinds of Prepositions"),
    ("c0479", "c0480", "The Uses of At and In"),
    ("c0494", "c0495", "Articles — Observe These Sentences"),
    ("c0508", "c0509", "Question Tags — Remember"),
]

# 2b. GROUP — several items that are one teaching unit in the book.
#     (list of content_ids, lesson title, result type or None to keep)
GROUPS = [
    ("m1_greetings", ["c0011", "c0012"], "Saying Goodbye", None),
    ("m1_greetings", ["c0013", "c0014"], "Seeking Permission", None),
    ("m1_gratitude", ["c0016", "c0017"], "Saying Thank You", None),
    ("m1_gratitude", ["c0018", "c0019"], "Responding to Thanks", None),
    ("m1_wishes_festive", ["c0022", "c0023"], "Wishes at Celebrations", None),
    ("m1_condolences", ["c0027", "c0028"], "Expressing Condolences", None),
    ("m1_farewell", ["c0031", "c0032", "c0033", "c0034", "c0035",
                     "c0036", "c0037", "c0038", "c0039", "c0040"],
     "Conversational Functions Covered in This Course", "heading"),
    ("m1_framing_q", ["c0047", "c0048", "c0049"], "Framing Direct Questions", None),
    ("m1_framing_q", ["c0050", "c0051"], "Questions with the Verb ‘Be’", None),
    ("m1_framing_q", ["c0052", "c0053", "c0054"], "Friendly Questions and Responses", None),
    ("m1_impression", ["c0070", "c0071"], "My Impression of Tiruchy", None),

    ("m2_fun_words", ["c0181", "c0182", "c0183", "c0184", "c0185", "c0186", "c0187"],
     "I. Spot Out the Odd Word", None),
    ("m2_fun_words", ["c0188", "c0189", "c0190", "c0191", "c0192", "c0193", "c0194",
                      "c0195", "c0196", "c0197", "c0198"], "II. Jumbled Words", None),
    ("m2_fun_words", ["c0203", "c0204"], "V. Missing Letters", None),
    ("m2_fun_words", ["c0205", "c0206"], "VI. Rearrange the Letters", None),
    ("m2_fun_words", ["c0207", "c0208", "c0209", "c0210", "c0211", "c0212"],
     "VII. Synonyms", None),
    ("m2_fun_words", ["c0213", "c0214", "c0215", "c0216", "c0217", "c0218"],
     "VIII. Antonyms", None),
    ("m2_fun_words", ["c0219", "c0220"], "IX. The Bottle Puzzle", None),
    ("m2_fun_words", ["c0221", "c0222"], "X. The 26-Letter Crossword", None),
    ("m2_fun_words", ["c0223", "c0224", "c0225", "c0226", "c0227", "c0228",
                      "c0229", "c0230"], "Answers", None),
    ("m2_fun_words", ["c0231", "c0232", "c0233", "c0234", "c0235", "c0236", "c0237",
                      "c0238", "c0239", "c0240", "c0241", "c0242"],
     "Lemonade — Vocabulary Test", None),
    ("m2_fun_words", ["c0248", "c0249", "c0250", "c0251", "c0252", "c0253"],
     "Answers to Exercise III", None),

    ("m3_sentence", ["c0256", "c0257"], "What Is a Sentence?", None),
    ("m3_sentence", ["c0259", "c0260", "c0261", "c0262"], "In Disorder → In Order", None),
    ("m3_kinds_sentence", ["c0264", "c0265"], "Assertive Sentence", None),
    ("m3_kinds_sentence", ["c0266", "c0267"], "Interrogative Sentence", None),
    ("m3_kinds_sentence", ["c0268", "c0269", "c0270", "c0271", "c0272"],
     "Imperative Sentence", None),
    ("m3_kinds_sentence", ["c0273", "c0274"], "Exclamatory Sentence", None),
    ("m3_kinds_sentence", ["c0275", "c0276"], "Optative Sentence", None),
    ("m3_nouns", ["c0281", "c0282"], "Kinds of Noun — Proper Noun", None),
    ("m3_nouns", ["c0287", "c0288"], "Exercise: Complete the Pairs", None),
    ("m3_adjectives", ["c0308", "c0309"], "Adjectives of Quantity", None),
    ("m3_tenses", ["c0357", "c0358", "c0359", "c0360"], "Simple Present", None),

    ("m5_reading_intro", ["c0531", "c0532", "c0533", "c0534", "c0535"],
     None, "text"),                                    # stays a section intro card
    ("m5_corruption", ["c0537", "c0538"], "Corruption as Human Rights Violation", None),
    ("m5_mother_teresa", ["c0540", "c0541"], "Mother Teresa", None),
    ("m5_women", ["c0547", "c0548"],
     "Are Women More Dependent on Relationships for Identity?", None),
    ("m5_letters", ["c0557", "c0559", "c0560", "c0561", "c0562", "c0563",
                    "c0564", "c0565", "c0566"],
     None, "text"),                                    # stays a section intro card
    ("m5_letters", ["c0567", "c0568", "c0569", "c0570", "c0571", "c0572",
                    "c0573", "c0574", "c0575"],
     "Letter 1 — Request for Bonafide Certificate", "list_item"),
    ("m5_letters", ["c0576", "c0577", "c0578", "c0579", "c0580", "c0581",
                    "c0582", "c0583", "c0584", "c0585"],
     "Letter 2 — Request for Conduct and Transfer Certificate", "list_item"),
]

# 2c. Explicit lesson titles for items that were kept as-is.
RETITLE = {
    "c0014": "Seeking Permission",
    "c0030": "Saying Goodbye",
    "c0041": "Favour or Help",
    "c0042": "Telephone Courtesy",
    "c0255": None,
    "c0257": "What Is a Sentence?",
    "c0278": "What Are the Parts of Speech?",
    "c0280": "What Is a Noun?",
    "c0283": "Kinds of Noun — Common Noun",
    "c0284": "Kinds of Noun — Collective Noun",
    "c0285": "Kinds of Noun — Material Noun",
    "c0286": "Kinds of Noun — Abstract Noun",
    "c0291": "Singular and Plural Forms",
    "c0292": "The Same Form in Singular and Plural",
    "c0293": "Nouns with Two Plural Uses",
    "c0294": "Nouns Always Used in the Singular",
    "c0295": "Nouns Always Used in the Plural",
    "c0298": "Correct Usage — Sentences",
    "c0302": "What Is a Pronoun?",
    "c0305": "Kinds of Pronoun",
    "c0307": "What Is an Adjective?",
    "c0163": "Gender — Masculine and Feminine Forms",
    "c0310": "Adjectives of Quantity — Examples",
    "c0311": "Adjectives of Number",
    "c0312": "Adjectives of Number — Examples",
    "c0313": "Distributive and Demonstrative Adjectives",
    "c0314": "Identifying Adjectives (1)",
    "c0315": "Identifying Adjectives (2)",
    "c0316": "Identifying Adjectives (3)",
    "c0317": "Identifying Adjectives (4)",
    "c0318": "Identifying Adjectives (5)",
    "c0319": "Identifying Adjectives (6)",
    "c0324": "What Is a Verb?",
    "c0437": "Adverbs Modify Verbs",
    "c0446": "Noun Clause",
    "c0447": "Noun Clause as Subject of the Verb",
    "c0448": "Noun Clause as Object of the Verb",
    "c0449": "Noun Clause as Object of a Preposition",
    "c0450": "Noun Clause as Complement",
    "c0451": "Noun Clause in Apposition",
    "c0452": "Exercise: Add Suitable Noun Clauses",
    "c0463": "Adjective Clause",
    "c0507": "What Is a Question Tag?",
    # Composition hints — name each story
    "c0589": "Hints: The Bee and the Dove",
    "c0590": "Hints: The Hen that Laid Golden Eggs",
    "c0591": "Hints: The Rotten Apple",
    "c0592": "Hints: The Bear and the Two Travellers",
    "c0593": "Hints: King Solomon and the Queen of Sheba",
}

# 2g. DROP_PARTS — the UI renders `StructuredContent(parts)` *instead of* the
#     item text, so a stale `parts` silently hides the lesson's own text. Each id
#     here kept its own `parts` from an item that is now a different lesson, or
#     carries a `parts` the digitiser mis-parsed. Dropping it makes the lesson
#     render its full text.
DROP_PARTS = [
    # merged lessons whose `parts` came from one member and hid the others
    "c0011", "c0027", "c0031", "c0047", "c0050", "c0052", "c0266",
    # pre-existing mis-parse: a grammar explanation stored as 3 bogus "questions"
    # (question 1 holds the whole lesson; the last question sits in the answer)
    "c0313",
    # comprehension items: `parts.questions` held the passage as question 1 and
    # the final question in the answer slot
    "c0522", "c0523", "c0524", "c0525", "c0526",
]

# 2d. DROP — byte-identical duplicates of a lesson kept earlier in the chapter.
DROP = [
    "c0391",   # Tenses — exact duplicate of c0387
]

# 2f. SPLIT_QUESTIONS — each comprehension item in the book is a passage with
#     its questions appended on the following lines; the digitiser glued them
#     into one item, so the questions were never shown. Split them back into a
#     "read the passage" lesson and an "answer the questions" lesson.
#     (ids to join as one passage, passage title)
SPLIT_QUESTIONS = [
    (["c0522"], "The Blind Lady and the Doctor"),
    (["c0523"], "The Jackal and the Camel"),
    (["c0524"], "The King’s Son and the Nurse"),
    (["c0525"], "The Miser and the Lost Purse"),
    (["c0526"], "The King and the Stone in the Road"),
    (["c0527", "c0528"], "The Ant and the Dove"),
]

# 2e. MOVE — re-home items into another chapter.
MOVE = {
    "c0166": "m2_young_ones",
    "c0167": "m2_young_ones",
    "c0556": "m5_letters",   # already there, listed for clarity
}

# ─────────────────────────────────────────────────────────────────────────────
# Machinery
# ─────────────────────────────────────────────────────────────────────────────


def load():
    course = json.load(open(COURSE, encoding="utf-8"), object_pairs_hook=OrderedDict)
    content = json.load(open(CONTENT, encoding="utf-8"), object_pairs_hook=OrderedDict)
    return course, content


def main(dry_run=False):
    if os.path.exists("tools/content_review/merge_manifest.json") and "--force" not in sys.argv:
        raise SystemExit(
            "Already applied (merge_manifest.json exists).\n"
            "This transform is not idempotent — restore the pristine assets first:\n"
            "  git checkout HEAD -- app/src/main/assets\n"
            "then re-run. Pass --force to apply anyway."
        )
    course, content = load()

    items = OrderedDict((i["content_id"], i) for i in content["canonical_items"])
    before_items = len(items)
    before_days = len(course["days"])

    section_of = {cid: i.get("section_id") for cid, i in items.items()}
    log = []

    # ── 2e MOVE ──────────────────────────────────────────────────────────────
    for cid, sid in MOVE.items():
        if cid in items:
            items[cid]["section_id"] = sid
    for gone, into in REMOVE_SECTIONS.items():
        for i in items.values():
            if i["section_id"] == gone:
                i["section_id"] = into

    # ── 2d DROP ──────────────────────────────────────────────────────────────
    for cid in DROP:
        items.pop(cid, None)

    # ── 2b GROUP ─────────────────────────────────────────────────────────────
    lesson_titles = dict(RETITLE)
    types = {}
    merge_manifest = []          # [new content_id, [original content_ids]]
    for _sid, ids, title, newtype in GROUPS:
        ids = [c for c in ids if c in items]
        if not ids:
            continue
        merge_manifest.append([ids[0], list(ids)])
        keep = items[ids[0]]
        texts = [items[c]["text"] for c in ids]
        idx = []
        for c in ids:
            idx += items[c].get("source_para_indices", [])
        parts = None
        for c in ids:
            if items[c].get("parts"):
                parts = items[c]["parts"]
        keep["text"] = "\n".join(texts)
        if idx:
            keep["source_para_indices"] = sorted(set(idx))
        if parts:
            keep["parts"] = parts
        if newtype:
            types[ids[0]] = newtype
        if title:
            lesson_titles[ids[0]] = title
        for c in ids[1:]:
            items.pop(c, None)
        log.append(f"GROUP {ids[0]} <- {len(ids)} items :: {(title or '')[:60]}")

    # ── 2a DEMOTE + ABSORB_TITLE ─────────────────────────────────────────────
    for cid in DEMOTE:
        if cid in items:
            types[cid] = "heading"

    for label, target, title in ABSORB_TITLE:
        if label in items:
            types[label] = "heading"
        if target in items:
            lesson_titles[target] = title
        log.append(f"ABSORB {label} -> {target} :: {title}")

    for cid, t in types.items():
        if cid in items:
            items[cid]["type"] = t

    # ── 2g DROP_PARTS ────────────────────────────────────────────────────────
    for cid in DROP_PARTS:
        if cid in items:
            items[cid].pop("parts", None)
            log.append(f"DROP_PARTS {cid}")

    for cid in [c for c, t in lesson_titles.items() if t is None]:
        lesson_titles.pop(cid)
    lesson_titles = {c: t for c, t in lesson_titles.items() if c in items}
    types = {c: t for c, t in types.items() if c in items}

    # ── 2f SPLIT_QUESTIONS ───────────────────────────────────────────────────
    sub_order = {}          # content_id -> tiebreak inside one source_order
    QUESTION_TAIL = re.compile(r"^(Suggest|Give)\b.*title", re.I)

    def is_question(line):
        s = line.strip()
        return bool(s) and (s.endswith("?") or QUESTION_TAIL.match(s))

    for ids, title in SPLIT_QUESTIONS:
        ids = [c for c in ids if c in items]
        if not ids:
            continue
        keep = items[ids[0]]
        joined = "\n".join(items[c]["text"] for c in ids)
        idx = sorted({n for c in ids for n in items[c].get("source_para_indices", [])})
        lines = joined.split("\n")
        cut = len(lines)
        while cut > 0 and is_question(lines[cut - 1]):
            cut -= 1
        if cut == len(lines) or cut == 0:
            raise SystemExit(f"SPLIT_QUESTIONS {ids[0]}: could not locate the questions")
        q_id = ids[-1] + "q"
        q_lines = [ln.strip() for ln in lines[cut:] if ln.strip()]
        q_item = OrderedDict([
            ("content_id", q_id),
            ("text", "\n".join(q_lines)),
            ("source_order", items[ids[-1]]["source_order"]),
            ("module_id", keep["module_id"]),
            ("section_id", keep["section_id"]),
            ("type", "text"),
            # One Q per line, so each question renders (and is translated) on
            # its own instead of the whole block sharing one Tamil line.
            ("parts", OrderedDict([
                ("kind", "questions"),
                ("questions", [OrderedDict([("q", ln)]) for ln in q_lines]),
            ])),
        ])
        items[q_id] = q_item
        sub_order[q_id] = 1
        keep["text"] = "\n".join(lines[:cut]).strip()
        keep.pop("parts", None)          # stale, mis-parsed block
        if idx:
            keep["source_para_indices"] = idx
        lesson_titles[ids[0]] = title
        lesson_titles[q_id] = f"{title} — Questions"
        for c in ids[1:]:
            items.pop(c, None)
        merge_manifest.append([q_id, [ids[-1]]])
        log.append(f"SPLIT {ids[0]} -> passage + {q_id}")

    # ── rebuild the module/section tree ──────────────────────────────────────
    new_sections = {s["section_id"]: s for s in NEW_SECTIONS}
    modules = []
    for m in content["modules"]:
        secs = []
        for s in m["sections"]:
            sid = s["section_id"]
            if sid in REMOVE_SECTIONS:
                continue
            secs.append(OrderedDict([
                ("section_id", sid),
                ("title", SECTION_TITLES.get(sid, s["title"])),
            ]))
            for ns in NEW_SECTIONS:
                if ns["after"] == sid and ns["module_id"] == m["module_id"]:
                    secs.append(OrderedDict([
                        ("section_id", ns["section_id"]),
                        ("title", ns["title"]),
                    ]))
        modules.append(OrderedDict([
            ("module_id", m["module_id"]),
            ("title", MODULE_TITLES.get(m["module_id"], m["title"])),
            ("sections", secs),
        ]))

    module_of = {s["section_id"]: m["module_id"]
                 for m in modules for s in m["sections"]}
    content["modules"] = modules

    # items whose section was moved into a section that now belongs elsewhere
    for cid in items:
        sid = items[cid]["section_id"]
        if sid in module_of:
            items[cid]["module_id"] = module_of[sid]

    # ── order items: module -> section -> old source_order ───────────────────
    ordered = []
    for m in modules:
        for s in m["sections"]:
            group = [i for i in items.values() if i["section_id"] == s["section_id"]]
            group.sort(key=lambda i: (i.get("source_order", 0),
                                      sub_order.get(i["content_id"], 0)))
            ordered.extend(group)
    orphans = [i["content_id"] for i in items.values()
               if i["section_id"] not in module_of]
    if orphans:
        raise SystemExit(f"items in unknown sections: {orphans[:10]}")

    for n, i in enumerate(ordered):
        i["source_order"] = n
    content["canonical_items"] = ordered

    # ── rebuild days from the runtime's own sectionContent rule ──────────────
    META_INTRO_SECTIONS = {
        "m1_greetings", "m1_gratitude", "m1_wishes_festive", "m1_wishes_exams",
        "m1_condolences", "m1_farewell", "m1_expressions", "m1_common_q",
        "m1_profession", "m1_casual_talk", "m1_games", "m1_holidays",
        "m1_impression", "m1_political",
        "m2_introduction", "m3_pos_intro", "m5_reading_intro", "m5_letters",
    }
    META_MARKERS = ["learners", "students", "this course", "necessary that", "essential ",
                    "imperative that", "vocabulary is", "pronunciation is", "while speaking",
                    "in the course of", "should not", "must be", "normally face",
                    "formal british"]

    def is_meta_intro(text):
        if len(text) < 200:
            return False
        low = text.lower()
        if text.count("?") >= 3 or text.count("!") >= 2:
            return False
        if low.split("i am ").__len__() - 1 >= 3:
            return False
        if low.split("congratulations").__len__() - 1 >= 2:
            return False
        if text.count("\u2013") >= 5 or text.count("\u2014") >= 5:
            return False
        return any(mk in low for mk in META_MARKERS)

    def section_content(sid):
        lst = [i for i in items.values()
               if i["section_id"] == sid and i["type"] != "heading"]
        if sid == "m1_dialogues":
            lst = [i for i in lst if i["type"] == "dialogue"]
        if sid in META_INTRO_SECTIONS:
            lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
        lst.sort(key=lambda i: i.get("source_order", 0))
        return lst[:400]

    old_seq = {}
    for d in course["days"]:
        if not d.get("is_exam"):
            old_seq.setdefault(d["section_id"], d["activity_sequence"])
    old_exam = {d["module_id"]: d for d in course["days"] if d.get("is_exam")}

    new_days = []
    day_no = 0
    stats = []
    for m in modules:
        mid = m["module_id"]
        for s in m["sections"]:
            sid = s["section_id"]
            lessons = section_content(sid)
            seq = old_seq.get(sid)
            if seq is None:
                seq = old_seq.get("m5_requisitions", ["teach", "read_aloud", "assessment"])
            for n, it in enumerate(lessons):
                day_no += 1
                title = lesson_titles.get(it["content_id"])
                if title is None:
                    title = (s["title"] if len(lessons) == 1
                             else f"{s['title']} · {n + 1}/{len(lessons)}")
                new_days.append(OrderedDict([
                    ("day", day_no),
                    ("module_id", mid),
                    ("section_id", sid),
                    ("lesson_title", title),
                    ("activity_sequence", list(seq)),
                    ("content_selection", OrderedDict([
                        ("selection_mode", "section_sequence"),
                        ("module_id", mid),
                        ("section_id", sid),
                    ])),
                ]))
            stats.append((sid, s["title"], len(lessons)))

        ex = old_exam.get(mid)
        if ex:
            day_no += 1
            new_days.append(OrderedDict([
                ("day", day_no),
                ("module_id", mid),
                ("section_id", f"_exam_{mid}"),
                ("lesson_title", f"{m['title']} — Final Exam"),
                ("activity_sequence", ["exam"]),
                ("content_selection", OrderedDict([
                    ("selection_mode", "module_exam"),
                    ("module_id", mid),
                    ("sample_size", ex["content_selection"].get("sample_size", 10)),
                ])),
                ("is_exam", True),
            ]))

    course["days"] = new_days

    # sort canonical_items keys back into the canonical order
    for i in content["canonical_items"]:
        pass

    print(f"items  {before_items} -> {len(content['canonical_items'])}")
    print(f"days   {before_days} -> {len(new_days)}")
    print(f"chapters {sum(len(m['sections']) for m in modules)}")
    print()
    print(f"{'section':22s} {'days':>5s}  title")
    for sid, title, n in stats:
        flag = "  <-- no lessons" if n == 0 else ""
        print(f"{sid:22s} {n:5d}  {title[:56]}{flag}")

    if dry_run:
        print("\n[dry run] nothing written")
        return

    for f, data in ((COURSE, course), (CONTENT, content)):
        with open(f, "w", encoding="utf-8", newline="\r\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    with open("tools/content_review/merge_manifest.json", "w", encoding="utf-8") as fh:
        json.dump(merge_manifest, fh, ensure_ascii=False, indent=1)
    print("\nwritten:", COURSE, CONTENT, "+ merge_manifest.json")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
