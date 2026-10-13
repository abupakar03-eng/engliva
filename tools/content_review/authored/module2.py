"""Module 2 (Vocabulary): practice questions with the answers supplied.

Each chapter already teaches its words as NOTE/EXAMPLE cards with Tamil. What the
book never gives is an answer key, so every chapter gains a
"Practice: …" Q&A lesson here — the spoken drill a teacher would run, with the
model answer printed so the student can check themselves.

`qa` entries are (question, answer, question_tamil, answer_tamil).
Conversations are deliberately not forced onto word-list chapters; where a
dialogue genuinely helps (grammar, composition) it is authored in those modules.
"""

ADDITIONS = {
    "m2_introduction": dict(qa=[
        ("What is the most vital part of learning a language?",
         "Vocabulary is the most vital part of learning a language.",
         "மொழி கற்பதில் மிக முக்கியமான பகுதி எது?",
         "சொல்லகராதிதான் மொழி கற்பதில் மிக முக்கியமான பகுதி."),
        ("What does R.P. stand for?",
         "R.P. stands for Received Pronunciation.",
         "R.P. என்பதன் விரிவாக்கம் என்ன?",
         "R.P. என்றால் Received Pronunciation."),
        ("Why is standard pronunciation important?",
         "Only standard pronunciation helps you communicate clearly with everyone.",
         "தரமான உச்சரிப்பு ஏன் முக்கியம்?",
         "தரமான உச்சரிப்பு மட்டுமே எல்லோரிடமும் தெளிவாகத் தொடர்பு கொள்ள உதவும்."),
        ("What is a syllable?",
         "A syllable is a single speech unit, like the word ‘cut’.",
         "Syllable என்றால் என்ன?",
         "Syllable என்பது ஒரு பேச்சு அலகு — உதாரணம் ‘cut’ என்ற சொல்."),
    ]),

    "m2_monosyllabic": dict(qa=[
        ("How many speech units are there in the word ‘day’?", "One.",
         "‘day’ என்ற சொல்லில் எத்தனை பேச்சு அலகுகள்?", "ஒன்று."),
        ("Is ‘silk’ a monosyllabic word?", "Yes. It has one speech unit.",
         "‘silk’ ஒரு monosyllabic சொல்லா?", "ஆமாம். அதில் ஒரு பேச்சு அலகு உள்ளது."),
        ("Say three words with one speech unit.", "Ace, bay, cow.",
         "ஒரு பேச்சு அலகு உள்ள மூன்று சொற்களைச் சொல்லுங்கள்.", "Ace, bay, cow."),
    ]),

    "m2_disyllabic": dict(qa=[
        ("How many speech units are there in ‘forward’?", "Two.",
         "‘forward’ என்ற சொல்லில் எத்தனை பேச்சு அலகுகள்?", "இரண்டு."),
        ("Divide ‘birthday’ into speech units.", "Birth – day. Two units.",
         "‘birthday’ சொல்லைப் பேச்சு அலகுகளாகப் பிரிக்கவும்.", "Birth – day. இரண்டு அலகுகள்."),
        ("Is ‘about’ a disyllabic word?", "Yes. It has two speech units.",
         "‘about’ ஒரு disyllabic சொல்லா?", "ஆமாம். அதில் இரண்டு பேச்சு அலகுகள் உள்ளன."),
    ]),

    "m2_trisyllabic": dict(qa=[
        ("How many speech units are there in ‘bicycle’?", "Three.",
         "‘bicycle’ என்ற சொல்லில் எத்தனை பேச்சு அலகுகள்?", "மூன்று."),
        ("Divide ‘accident’ into speech units.", "Ac – ci – dent. Three units.",
         "‘accident’ சொல்லைப் பேச்சு அலகுகளாகப் பிரிக்கவும்.", "Ac – ci – dent. மூன்று அலகுகள்."),
        ("Is ‘understand’ trisyllabic?", "Yes. It has three speech units.",
         "‘understand’ trisyllabic-ஆ?", "ஆமாம். அதில் மூன்று பேச்சு அலகுகள் உள்ளன."),
    ]),

    "m2_tetrasyllabic": dict(qa=[
        ("How many speech units are there in ‘caterpillar’?", "Four.",
         "‘caterpillar’ என்ற சொல்லில் எத்தனை பேச்சு அலகுகள்?", "நான்கு."),
        ("Divide ‘unfortunate’ into speech units.", "Un – for – tu – nate. Four units.",
         "‘unfortunate’ சொல்லைப் பேச்சு அலகுகளாகப் பிரிக்கவும்.", "Un – for – tu – nate. நான்கு அலகுகள்."),
        ("Is ‘melancholy’ tetrasyllabic?", "Yes. It has four speech units.",
         "‘melancholy’ tetrasyllabic-ஆ?", "ஆமாம். அதில் நான்கு பேச்சு அலகுகள் உள்ளன."),
    ]),

    "m2_pentasyllabic": dict(qa=[
        ("How many speech units are there in ‘irregular’?", "Five.",
         "‘irregular’ என்ற சொல்லில் எத்தனை பேச்சு அலகுகள்?", "ஐந்து."),
        ("Say a word with more than five speech units.", "Particularization.",
         "ஐந்துக்கு மேல் பேச்சு அலகுகள் உள்ள ஒரு சொல்லைச் சொல்லுங்கள்.", "Particularization."),
        ("How many speech units are there in ‘Tiruchirappalli’?", "Six.",
         "‘Tiruchirappalli’ என்ற சொல்லில் எத்தனை பேச்சு அலகுகள்?", "ஆறு."),
    ]),

    "m2_silent_letters": dict(qa=[
        ("Which letter is silent in ‘comb’?", "The letter ‘b’.",
         "‘comb’ என்ற சொல்லில் எந்த எழுத்து உச்சரிக்கப்படுவதில்லை?", "‘b’ என்ற எழுத்து."),
        ("Which letter is silent in ‘know’ and ‘knife’?", "The letter ‘k’.",
         "‘know’, ‘knife’ ஆகியவற்றில் எந்த எழுத்து உச்சரிக்கப்படுவதில்லை?", "‘k’ என்ற எழுத்து."),
        ("Which letter is silent in ‘hour’ and ‘honest’?", "The letter ‘h’.",
         "‘hour’, ‘honest’ ஆகியவற்றில் எந்த எழுத்து உச்சரிக்கப்படுவதில்லை?", "‘h’ என்ற எழுத்து."),
        ("Which letter is silent in ‘castle’ and ‘christmas’?", "The letter ‘t’.",
         "‘castle’, ‘christmas’ ஆகியவற்றில் எந்த எழுத்து உச்சரிக்கப்படுவதில்லை?", "‘t’ என்ற எழுத்து."),
        ("How is ‘gh’ pronounced in ‘rough’ and ‘cough’?", "It is pronounced like ‘f’.",
         "‘rough’, ‘cough’ ஆகியவற்றில் ‘gh’ எப்படி உச்சரிக்கப்படுகிறது?", "‘f’ போல உச்சரிக்கப்படுகிறது."),
    ]),

    "m2_easier_vocab": dict(qa=[
        ("What is an easier word for ‘eschew’?", "Avoid.",
         "‘eschew’ என்பதற்கு எளிய சொல் என்ன?", "Avoid."),
        ("What is an easier word for ‘derelict’?", "Abandoned.",
         "‘derelict’ என்பதற்கு எளிய சொல் என்ன?", "Abandoned."),
        ("What is an easier word for ‘deleterious’?", "Hurtful.",
         "‘deleterious’ என்பதற்கு எளிய சொல் என்ன?", "Hurtful."),
        ("What is an easier word for ‘garrulous’?", "Talkative.",
         "‘garrulous’ என்பதற்கு எளிய சொல் என்ன?", "Talkative."),
        ("What is an easier word for ‘tardy’?", "Slow.",
         "‘tardy’ என்பதற்கு எளிய சொல் என்ன?", "Slow."),
    ]),

    "m2_figurative": dict(qa=[
        ("What does ‘above board’ mean?",
         "Not open to question — honest and straight forward.",
         "‘above board’ என்பதன் பொருள் என்ன?",
         "கேள்விக்கு இடமில்லாதது — நேர்மையானது, வெளிப்படையானது."),
        ("What does ‘to let the cat out of the bag’ mean?",
         "To expose the trick; to let out the secret beforehand.",
         "‘to let the cat out of the bag’ என்பதன் பொருள் என்ன?",
         "தந்திரத்தை வெளிப்படுத்துவது; ரகசியத்தை முன்பே சொல்லிவிடுவது."),
        ("What does ‘at the eleventh hour’ mean?", "At the last moment.",
         "‘at the eleventh hour’ என்பதன் பொருள் என்ன?", "கடைசி நேரத்தில்."),
        ("What does ‘a red-letter day’ mean?",
         "A memorable day; a day of great importance.",
         "‘a red-letter day’ என்பதன் பொருள் என்ன?",
         "நினைவில் நிற்கும் நாள்; மிக முக்கியமான நாள்."),
        ("What does ‘to be on tenterhooks’ mean?",
         "To be in a state of suspense and anxiety.",
         "‘to be on tenterhooks’ என்பதன் பொருள் என்ன?",
         "பரபரப்புடனும் கவலையுடனும் காத்திருக்கும் நிலை."),
    ]),

    "m2_categories": dict(qa=[
        ("What do we call a number of lions or monkeys together?", "A troop.",
         "சிங்கங்கள் அல்லது குரங்குகள் கூட்டமாக இருப்பதை என்ன என்பார்கள்?", "A troop."),
        ("What is a ‘kennel’?", "A house or shelter for a dog.",
         "‘kennel’ என்றால் என்ன?", "நாய்க்கான வீடு அல்லது தங்குமிடம்."),
        ("What is an ‘oculist’?", "One who attends to the diseases of the eye.",
         "‘oculist’ என்றால் யார்?", "கண் நோய்களுக்கு சிகிச்சை அளிப்பவர்."),
        ("What is a ‘fugitive’?", "One who runs away from justice or the law.",
         "‘fugitive’ என்றால் யார்?", "நீதியிலிருந்து அல்லது சட்டத்திலிருந்து தப்பி ஓடுபவர்."),
        ("What does ‘democracy’ mean?",
         "Government of the people, for the people and by the people.",
         "‘democracy’ என்பதன் பொருள் என்ன?",
         "மக்களால், மக்களுக்காக, மக்களுடைய ஆட்சி."),
        ("What does ‘elope’ mean?",
         "To run away with a lover in order to get married secretly.",
         "‘elope’ என்பதன் பொருள் என்ன?",
         "ரகசியமாகத் திருமணம் செய்ய ஒரு காதலனுடன் ஓடிவிடுவது."),
    ]),

    "m2_young_ones": dict(qa=[
        ("What is the young of an eagle called?", "An eaglet.",
         "கழுகின் குட்டியை என்ன என்பார்கள்?", "Eaglet."),
        ("What is the young of a swan called?", "A cygnet.",
         "அன்னப்பறவையின் குட்டியை என்ன என்பார்கள்?", "Cygnet."),
        ("What is the young of a frog called?", "A tadpole.",
         "தவளையின் குட்டியை என்ன என்பார்கள்?", "Tadpole."),
        ("What is the young of a sheep called?", "A lamb.",
         "ஆட்டின் குட்டியை என்ன என்பார்கள்?", "Lamb."),
        ("What is the young of a horse called?", "A foal.",
         "குதிரையின் குட்டியை என்ன என்பார்கள்?", "Foal."),
    ]),

    "m2_confusables": dict(qa=[
        ("What is the difference between ‘contagious’ and ‘infectious’?",
         "A contagious disease is transmitted by physical contact; an infectious disease can be communicated through the air.",
         "‘contagious’–‘infectious’ வித்தியாசம் என்ன?",
         "தொற்று நோய் உடல் தொடர்பால் பரவும்; infectious நோய் காற்றின் வழியாகப் பரவும்."),
        ("What does ‘to dispose of’ something mean?", "To throw it away.",
         "ஏதாவது ஒன்றை ‘dispose of’ செய்வது என்றால் என்ன?", "அதைத் தூக்கி எறிவது."),
        ("What does ‘to dispense with’ something mean?", "To do without it.",
         "ஏதாவது ஒன்றை ‘dispense with’ செய்வது என்றால் என்ன?", "அது இல்லாமல் செயல்படுவது."),
        ("What does ‘explicit’ mean?", "Stated directly.",
         "‘explicit’ என்பதன் பொருள் என்ன?", "நேரடியாகச் சொல்லப்பட்டது."),
        ("What does ‘implicit’ mean?", "Stated indirectly.",
         "‘implicit’ என்பதன் பொருள் என்ன?", "மறைமுகமாகச் சொல்லப்பட்டது."),
        ("What does ‘to flout’ a rule mean?",
         "To deliberately ignore a rule or an accepted standard of behaviour.",
         "ஒரு விதியை ‘flout’ செய்வது என்றால் என்ன?",
         "ஒரு விதியையோ ஏற்றுக்கொள்ளப்பட்ட நடத்தைத் தரத்தையோ வேண்டுமென்றே மீறுவது."),
    ]),

    "m2_troublesome": dict(qa=[
        ("What does ‘alter’ mean?", "To change.",
         "‘alter’ என்பதன் பொருள் என்ன?", "மாற்றுவது."),
        ("What is an ‘altar’?", "A structure used in worship.",
         "‘altar’ என்றால் என்ன?", "வழிபாட்டில் பயன்படுத்தும் ஒரு அமைப்பு."),
        ("What does ‘cite’ mean?", "To use as an example.",
         "‘cite’ என்பதன் பொருள் என்ன?", "உதாரணமாகக் குறிப்பிடுவது."),
        ("What is a ‘site’?", "A location.",
         "‘site’ என்றால் என்ன?", "ஒரு இடம்."),
        ("What is the difference between ‘graceful’ and ‘gracious’?",
         "‘Graceful’ describes attractive bearing and ease of movement; ‘gracious’ implies kindness or courtesy from a superior.",
         "‘graceful’–‘gracious’ வித்தியாசம் என்ன?",
         "‘Graceful’ என்பது அழகான தோற்றமும் எளிதான அசைவும்; ‘gracious’ என்பது மேலதிகாரியின் கனிவையும் பணிவையும் குறிக்கும்."),
    ]),

    "m2_fun_words": dict(qa=[
        ("Which word does not belong: spring, winter, summer, autumn, cold?",
         "Cold — it is not a season.",
         "எந்தச் சொல் பொருந்தவில்லை: spring, winter, summer, autumn, cold?",
         "Cold — அது ஒரு பருவம் அல்ல."),
        ("Which word does not belong: eyes, ears, nose, tongue, talk?",
         "Talk — it is not a part of the body.",
         "எந்தச் சொல் பொருந்தவில்லை: eyes, ears, nose, tongue, talk?",
         "Talk — அது உடலின் ஒரு பகுதி அல்ல."),
        ("Unjumble ‘esroh’.", "Horse.",
         "‘esroh’ என்பதைச் சரிசெய்யுங்கள்.", "Horse."),
        ("Unjumble ‘oellyw’.", "Yellow.",
         "‘oellyw’ என்பதைச் சரிசெய்யுங்கள்.", "Yellow."),
        ("Which currency is used in Japan?", "The Yen.",
         "ஜப்பானில் எந்த நாணயம் பயன்படுத்தப்படுகிறது?", "Yen."),
    ]),
}
