"""Give every lesson the teacher-led shape, across all modules.

For each lesson that still renders as one paragraph:
  * split it into short lines — aligned with the existing natural Tamil, so no
    line loses its translation;
  * tag explanatory lines as NOTE and the rest as EXAMPLE, which is what the
    lesson screen renders as labelled cards, one line per card;
  * open each chapter with a teacher's note, so the chapter reads as a teacher
    introducing the work and then taking the student through it.

The item's `text` is never changed, so grading, TTS and the exam pools are
untouched — only the way the lesson is displayed.

Run:  python tools/content_review/structure_all.py [--dry-run]
"""
import json
import re
import sys
from collections import OrderedDict

ASSETS = "app/src/main/assets"

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

# ── the teacher's opening line for each chapter ──────────────────────────────
NOTE_SENTENCE = "Read this passage aloud sentence by sentence, then say what it means in your own words."
NOTE_SENTENCE_TA = "இந்தப் பத்தியை வாக்கியம் வாக்கியமாகச் சத்தமாக வாசியுங்கள். பிறகு அதன் பொருளை உங்கள் சொந்த வார்த்தையில் சொல்லுங்கள்."
WORD_UNIT = ("Say each word aloud and clap once for every speech unit.",
             "ஒவ்வொரு சொல்லையும் சத்தமாகச் சொல்லி, ஒவ்வொரு அசைக்கும் ஒரு தட்டு தட்டுங்கள்.")

TEACHER_NOTES = {
    "m1_condolences": ("When someone has lost a dear one, your words matter. Say each line slowly and gently.",
                       "யாராவது தங்களுக்குப் பிரியமானவரை இழந்திருக்கும்போது உங்கள் வார்த்தைகள் முக்கியம். ஒவ்வொரு வரியையும் மெதுவாக, அன்பாகச் சொல்லுங்கள்."),
    "m1_farewell": ("Here you learn to take leave politely, and to ask for a favour or help.",
                    "இங்கே நீங்கள் பணிவாக விடைபெறுவது, உதவி கேட்பது எப்படி என்று கற்பீர்கள்."),
    "m1_expressions": ("Say how you feel. Each line is short — say it aloud until it sounds natural.",
                       "உங்கள் உணர்வுகளைச் சொல்லுங்கள். ஒவ்வொரு வரியும் சிறியது — இயல்பாக ஒலிக்கும் வரை சத்தமாகச் சொல்லுங்கள்."),
    "m1_framing_q": ("A question opens a conversation. Notice the word order, then ask each question aloud.",
                     "ஒரு கேள்விதான் உரையாடலைத் தொடங்குகிறது. வார்த்தை வரிசையைக் கவனித்து, ஒவ்வொரு கேள்வியையும் சத்தமாகக் கேளுங்கள்."),
    "m1_common_q": ("These are the questions people ask every day. Listen, then answer as if you were asked.",
                    "இவை தினமும் மக்கள் கேட்கும் கேள்விகள். கேட்டு, யாராவது உங்களைக் கேட்டதாக நினைத்துப் பதில் சொல்லுங்கள்."),
    "m1_profession": ("Say what you do for a living. Replace the example with your own work.",
                      "நீங்கள் என்ன வேலை செய்கிறீர்கள் என்று சொல்லுங்கள். உதாரணத்திற்குப் பதிலாக உங்கள் வேலையைச் சொல்லுங்கள்."),
    "m1_casual_talk": ("Two friends are talking. Read both parts aloud, then take one part yourself.",
                       "இரண்டு நண்பர்கள் பேசுகிறார்கள். இரண்டு பகுதிகளையும் சத்தமாக வாசியுங்கள், பிறகு ஒரு பாத்திரமாக நீங்கள் பேசுங்கள்."),
    "m1_games": ("Talk about games and hobbies. Say each answer aloud as your own.",
                 "விளையாட்டு, பொழுதுபோக்கு பற்றிப் பேசுங்கள். ஒவ்வொரு பதிலையும் உங்களுடையதாகச் சொல்லுங்கள்."),
    "m1_holidays": ("Describe your holidays. The model answer shows how to build a paragraph.",
                    "உங்கள் விடுமுறையை விவரியுங்கள். மாதிரி பதில் ஒரு பத்தியை எப்படிக் கட்டுவது என்று காட்டுகிறது."),
    "m1_impression": ("Describe a place you know well. Use the clues and speak in full sentences.",
                      "உங்களுக்கு நன்கு தெரிந்த ஒரு இடத்தை விவரியுங்கள். குறிப்புகளை வைத்து முழு வாக்கியங்களில் பேசுங்கள்."),
    "m1_political": ("Speak about a leader you like. Carry the model on with your own sentences.",
                     "உங்களுக்குப் பிடித்த ஒரு தலைவரைப் பற்றிப் பேசுங்கள். மாதிரியை உங்கள் சொந்த வாக்கியங்களில் தொடருங்கள்."),
    "m1_dialogues": ("These are real conversations. You take one part and say it aloud; the app takes the other.",
                     "இவை உண்மையான உரையாடல்கள். ஒரு பாத்திரமாக நீங்கள் சத்தமாகப் பேசுங்கள்; மற்றதை app பேசும்."),

    "m2_introduction": ("Listen to what this chapter is for, then begin with the words.",
                        "இந்த அத்தியாயம் எதற்கு என்று கேளுங்கள், பிறகு சொற்களில் தொடங்குங்கள்."),
    "m2_monosyllabic": WORD_UNIT,
    "m2_disyllabic": WORD_UNIT,
    "m2_trisyllabic": WORD_UNIT,
    "m2_tetrasyllabic": WORD_UNIT,
    "m2_pentasyllabic": WORD_UNIT,
    "m2_silent_letters": ("Some letters are not pronounced. Say each word aloud and notice the silent letter.",
                          "சில எழுத்துகள் உச்சரிக்கப்படுவதில்லை. ஒவ்வொரு சொல்லையும் சத்தமாகச் சொல்லி, உச்சரிக்காத எழுத்தைக் கவனியுங்கள்."),
    "m2_easier_vocab": ("Say the easier word instead of the difficult one.",
                        "கடினமான சொல்லுக்குப் பதிலாக எளிய சொல்லைச் சொல்லுங்கள்."),
    "m2_figurative": ("These expressions mean more than the words say. Read each one with its meaning.",
                      "இந்த வெளிப்பாடுகள் சொற்களுக்கு அப்பால் பொருள் தரும். ஒவ்வொன்றையும் அதன் பொருளுடன் வாசியுங்கள்."),
    "m2_categories": ("Words are grouped by topic. Say the word, then say what it means.",
                      "சொற்கள் தலைப்பு வாரியாகத் தொகுக்கப்பட்டுள்ளன. சொல்லைச் சொல்லி, பிறகு அதன் பொருளைச் சொல்லுங்கள்."),
    "m2_young_ones": ("Learn the special names for the young of animals. Say each pair aloud.",
                      "விலங்குகளின் குட்டிகளுக்கான சிறப்புப் பெயர்களைக் கற்போம். ஒவ்வொரு ஜோடியையும் சத்தமாகச் சொல்லுங்கள்."),
    "m2_confusables": ("These words are easy to confuse. Say both, and notice the difference in meaning.",
                       "இந்தச் சொற்களைக் குழப்பிக்கொள்வது எளிது. இரண்டையும் சொல்லி, பொருள் வேறுபாட்டைக் கவனியுங்கள்."),
    "m2_troublesome": ("Say each word clearly, then say what it means.",
                       "ஒவ்வொரு சொல்லையும் தெளிவாகச் சொல்லி, பிறகு அதன் பொருளைச் சொல்லுங்கள்."),
    "m2_fun_words": ("These are word games. Read the instruction, then try each puzzle aloud.",
                     "இவை சொல் விளையாட்டுகள். வழிமுறையை வாசித்து, ஒவ்வொரு புதிரையும் சத்தமாக முயற்சி செய்யுங்கள்."),

    "m3_sentence": ("A sentence must give complete sense. Say each example aloud, then put the mixed words in order.",
                    "ஒரு வாக்கியம் முழுப் பொருள் தர வேண்டும். ஒவ்வொரு உதாரணத்தையும் சத்தமாகச் சொல்லி, குழம்பிய சொற்களை வரிசைப்படுத்துங்கள்."),
    "m3_kinds_sentence": ("There are five kinds of sentence. Say one example of each aloud.",
                          "ஐந்து வகை வாக்கியங்கள் உள்ளன. ஒவ்வொரு வகைக்கும் ஒரு உதாரணத்தைச் சத்தமாகச் சொல்லுங்கள்."),
    "m3_pos_intro": ("Eight parts of speech. Say each name clearly.",
                     "எட்டுப் பேச்சுப் பகுதிகள். ஒவ்வொரு பெயரையும் தெளிவாகச் சொல்லுங்கள்."),
    "m3_nouns": ("A noun names a person, a place or a thing. Say each kind aloud with an example.",
                 "பெயர்ச்சொல் ஒரு நபர், இடம் அல்லது பொருளின் பெயர். ஒவ்வொரு வகையையும் உதாரணத்துடன் சொல்லுங்கள்."),
    "m3_pronouns": ("A pronoun stands in place of a noun. Say each sentence aloud.",
                    "பிரதிபெயர் பெயர்ச்சொல்லுக்குப் பதிலாக வரும். ஒவ்வொரு வாக்கியத்தையும் சத்தமாகச் சொல்லுங்கள்."),
    "m3_adjectives": ("An adjective describes a noun. Say each sentence and point out the adjective.",
                      "பெயரடை ஒரு பெயர்ச்சொல்லை விவரிக்கும். ஒவ்வொரு வாக்கியத்தையும் சொல்லி, பெயரடையைச் சுட்டுங்கள்."),
    "m3_exercise_pos": ("Fill in the missing form of each word. Say the whole family aloud.",
                        "ஒவ்வொரு சொல்லின் விடுபட்ட வடிவை நிரப்புங்கள். முழுக் குடும்பத்தையும் சத்தமாகச் சொல்லுங்கள்."),
    "m3_verbs": ("A verb tells us the action. Say each sentence aloud.",
                 "வினைச்சொல் செயலைச் சொல்கிறது. ஒவ்வொரு வாக்கியத்தையும் சத்தமாகச் சொல்லுங்கள்."),
    "m3_subject_verb": ("The verb must agree with the subject. Say the correct sentence aloud each time.",
                        "வினைச்சொல் எழுவாயுடன் ஒத்திருக்க வேண்டும். ஒவ்வொரு முறையும் சரியான வாக்கியத்தைச் சத்தமாகச் சொல்லுங்கள்."),
    "m3_tenses": ("Tense tells us the time of the action. Say each example aloud and notice the time.",
                  "காலம் செயலின் நேரத்தைச் சொல்கிறது. ஒவ்வொரு உதாரணத்தையும் சத்தமாகச் சொல்லி, நேரத்தைக் கவனியுங்கள்."),
    "m3_sequence": ("When two actions share a sentence, their tenses must match. Read each rule and example aloud.",
                    "ஒரு வாக்கியத்தில் இரண்டு செயல்கள் இருந்தால், காலங்கள் பொருந்த வேண்டும். ஒவ்வொரு விதியையும் உதாரணத்தையும் சத்தமாக வாசியுங்கள்."),
    "m3_voice": ("Active voice shows the doer, passive voice shows what was done. Read both aloud and compare.",
                 "செய்வினை செய்பவரைக் காட்டும்; செயப்பாட்டு வினை என்ன செய்யப்பட்டது எனக் காட்டும். இரண்டையும் வாசித்து ஒப்பிடுங்கள்."),
    "m3_adverb": ("An adverb tells us how, when or where. Say each kind aloud with an example.",
                  "வினையடை எப்படி, எப்போது, எங்கே என்று சொல்கிறது. ஒவ்வொரு வகையையும் உதாரணத்துடன் சொல்லுங்கள்."),
    "m3_clauses": ("A clause has a subject and a verb. Say each example aloud and notice the clause.",
                   "ஒரு பகுதியில் எழுவாயும் வினையும் இருக்கும். ஒவ்வொரு உதாரணத்தையும் சொல்லி, பகுதியைக் கவனியுங்கள்."),
    "m3_prepositions": ("A preposition shows the relation between words. Say each sentence and stress the preposition.",
                        "முன்னிடைச்சொல் சொற்களுக்கு இடையிலான தொடர்பைக் காட்டும். ஒவ்வொரு வாக்கியத்தையும் சொல்லி, முன்னிடைச்சொல்லை அழுத்திச் சொல்லுங்கள்."),
    "m3_articles": ("a, an and the are small words with big rules. Say each sentence aloud.",
                    "a, an, the சிறிய சொற்கள், ஆனால் முக்கிய விதிகள். ஒவ்வொரு வாக்கியத்தையும் சத்தமாகச் சொல்லுங்கள்."),
    "m3_question_tags": ("A question tag turns a statement into a question. Say the statement, then add the tag.",
                         "கேள்வித் தொடர் ஒரு கூற்றைக் கேள்வியாக மாற்றும். கூற்றைச் சொல்லி, பிறகு தொடரைச் சேர்க்கவும்."),

    "m4_passages": ("Read the passage aloud first, then answer the questions in your own words.",
                    "முதலில் பத்தியைச் சத்தமாக வாசியுங்கள், பிறகு கேள்விகளுக்கு உங்கள் சொந்த வார்த்தையில் பதில் சொல்லுங்கள்."),

    "m5_corruption": (NOTE_SENTENCE, NOTE_SENTENCE_TA),
    "m5_mother_teresa": (NOTE_SENTENCE, NOTE_SENTENCE_TA),
    "m5_rural_managers": (NOTE_SENTENCE, NOTE_SENTENCE_TA),
    "m5_women": (NOTE_SENTENCE, NOTE_SENTENCE_TA),
    "m5_conflicts": (NOTE_SENTENCE, NOTE_SENTENCE_TA),
    "m5_letters": ("Read the model letter aloud, then write your own with your details.",
                   "மாதிரிக் கடிதத்தைச் சத்தமாக வாசியுங்கள், பிறகு உங்கள் விவரங்களுடன் சொந்தக் கடிதம் எழுதுங்கள்."),
    "m5_story_hints": ("Turn each hint into a story. Say it aloud first, then write it.",
                       "ஒவ்வொரு குறிப்பையும் ஒரு கதையாக மாற்றுங்கள். முதலில் சத்தமாகச் சொல்லுங்கள், பிறகு எழுதுங்கள்."),
}

SENT = re.compile(r"(?<=[.!?])\s+")
NOTE_HINT = re.compile(r"^(The following|There are|Note:|Directions:|Exercise|Observe|Remember)", re.I)
NOTE_MARK = (" is called ", " is known as ", " means ", " is a word ", " is a sentence",
             " is a term ", " are called ", " is used ")


def is_meta_intro(t):
    if len(t) < 200:
        return False
    low = t.lower()
    if t.count("?") >= 3 or t.count("!") >= 2:
        return False
    if low.split("i am ").__len__() - 1 >= 3:
        return False
    if low.split("congratulations").__len__() - 1 >= 2:
        return False
    if t.count("\u2013") >= 5 or t.count("\u2014") >= 5:
        return False
    return any(mk in low for mk in META_MARKERS)


def candidates(text):
    t = text.strip()
    if "\n" in t:
        yield [p.strip() for p in t.split("\n") if p.strip()]
    if " – " in t:
        yield [p.strip() for p in t.split(" – ") if p.strip()]
    if "; " in t:
        yield [p.strip() for p in t.split("; ") if p.strip()]
    if SENT.search(t):
        yield [p.strip() for p in SENT.split(t) if p.strip()]


def split_aligned(en, ta):
    """Split English and Tamil the same way, or return (None, None)."""
    if ta is None:
        return None, None
    for parts in candidates(en):
        if len(parts) < 2:
            continue
        for tparts in candidates(ta):
            if len(tparts) == len(parts):
                return parts, tparts
    return None, None


def block_kind(piece):
    p = piece.strip()
    if p.endswith(":") or NOTE_HINT.match(p) or any(m in p for m in NOTE_MARK):
        return "note"
    return "example" if len(p) <= 220 else "body"


def main(dry_run=False):
    content = json.load(open(f"{ASSETS}/content.json", encoding="utf-8"),
                        object_pairs_hook=OrderedDict)
    course = json.load(open(f"{ASSETS}/course.json", encoding="utf-8"),
                       object_pairs_hook=OrderedDict)
    tr = json.load(open(f"{ASSETS}/translations.json", encoding="utf-8"),
                  object_pairs_hook=OrderedDict)
    strings = tr["strings"]
    items = {i["content_id"]: i for i in content["canonical_items"]}

    lessons_by_section = OrderedDict()
    for d in course["days"]:
        if not d.get("is_exam"):
            lessons_by_section.setdefault(d["section_id"], []).append(d)

    structured = noted = 0

    # resolve each day to its item the same way the runtime does
    def section_items(sid):
        lst = [i for i in content["canonical_items"]
               if i.get("section_id") == sid and i["type"] != "heading"]
        if sid == "m1_dialogues":
            lst = [i for i in lst if i["type"] == "dialogue"]
        if sid in META_INTRO_SECTIONS:
            lst = [i for i in lst if not (i["type"] == "text" and is_meta_intro(i["text"]))]
        return sorted(lst, key=lambda i: i["source_order"])[:400]

    for sid, days in lessons_by_section.items():
        its = section_items(sid)
        if not its:
            continue
        # The teacher's note opens the chapter — but it can only live on a
        # lesson that renders as blocks, so it goes on the first such lesson.
        note = TEACHER_NOTES.get(sid)
        for n, day in enumerate(days):
            it = its[n] if n < len(its) else its[-1]
            if it["type"] == "dialogue":
                continue
            if it.get("parts"):
                if note and it["parts"].get("kind") == "blocks":
                    it["parts"]["blocks"].insert(
                        0, OrderedDict([("kind", "note"), ("text", note[0])]))
                    strings.setdefault(note[0], note[1])
                    noted += 1
                    note = None
                continue
            en = it["text"].strip()
            ta = strings.get(en)
            parts, tparts = split_aligned(en, ta)
            blocks, new_tr = [], {}

            if note:
                blocks.append(OrderedDict([("kind", "note"), ("text", note[0])]))
                new_tr[note[0]] = note[1]
                noted += 1
                note = None

            if parts:
                for p, tp in zip(parts, tparts):
                    blocks.append(OrderedDict([("kind", block_kind(p)), ("text", p)]))
                    new_tr[p] = tp
            else:
                blocks.append(OrderedDict([("kind", block_kind(en)), ("text", en)]))
                if ta:
                    new_tr[en] = ta

            for k, v in new_tr.items():
                strings.setdefault(k, v)
            it["parts"] = OrderedDict([("kind", "blocks"), ("blocks", blocks)])
            structured += 1

    print(f"lessons structured : {structured}")
    print(f"chapters given a teacher's note: {noted}")
    print(f"translations       : {len(strings)}")
    if dry_run:
        print("[dry run] nothing written")
        return
    for path, data, indent, nl in (
        (f"{ASSETS}/content.json", content, 2, "\r\n"),
        (f"{ASSETS}/translations.json", tr, None, ""),
    ):
        with open(path, "w", encoding="utf-8", newline=nl) as fh:
            if indent:
                json.dump(data, fh, ensure_ascii=False, indent=indent)
            else:
                json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    print("written")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
