"""Author a lesson as information + lesson + question/answer + conversation.

The app already knows how to render all four — `parts.kind="blocks"` gives a
labelled RULE/EXAMPLE/NOTE card per line (each with its own Tamil line),
`parts.kind="questions"` gives a Q1…Qn / A list, and `turns` drives the role-play
screen. The shipped content just never used them: 383 of 473 items render as a
single paragraph.

A lesson here is one of:
  blocks    — [(kind, english, tamil), ...]   kind in rule|example|note|exception|body
  questions — [(q_en, a_en, q_ta, a_ta), ...]
  turns     — [(speaker, role, english, tamil), ...]
Each lesson also carries the activity wires the lesson should run, and every
lesson must contain at least one graded activity (read_aloud / listen_repeat /
speak / assessment / discussion) or it can never reach the 80% pass mark.
"""

# ── reusable activity sequences ──────────────────────────────────────────────
LISTEN = ["listen"]
TEACH = ["listen", "listen_repeat", "read_aloud"]
SPEAK = ["listen", "listen_repeat", "speak", "read_aloud"]
PRACTICE = ["listen", "read_aloud", "assessment"]
TALK = ["discussion"]


def note(en, ta):
    return ("note", en, ta)


def rule(en, ta):
    return ("rule", en, ta)


def eg(en, ta):
    return ("example", en, ta)


CHAPTERS = [
    # ══ 1 ═════════════════════════════════════════════════════════════════════
    dict(
        section_id="m1_greetings",
        title="Greetings and Introductions",
        module_id="m1_conversation",
        intro=[
            ("While speaking English — or in the spoken form of English — certain expressions are to be used because the English language is very formal and official. As learners and users of English it is necessary that the formal British idiom is learnt to make official deals, and transactions absolutely formal communicative and clear.",
             "ஆங்கிலம் பேசும்போது — அல்லது பேச்சு வடிவ ஆங்கிலத்தில் — சில வெளிப்பாடுகளைப் பயன்படுத்த வேண்டும், ஏனெனில் ஆங்கில மொழி மிகவும் formal ஆனதும் official ஆனதும். ஆங்கிலம் கற்பவர்களாகவும் பயன்படுத்துபவர்களாகவும், அதிகாரப்பூர்வ ஒப்பந்தங்களையும் பரிவர்த்தனைகளையும் முழுமையாக formal ஆகவும் தெளிவாகவும் தொடர்பு கொள்ள, formal British idiom-ஐக் கற்றுக்கொள்வது அவசியம்."),
            ("In the course of any conversation it is necessary to use the correct idiom, expression and usage without the influence of the mother tongue or vernacular, which includes manners and etiquette. You are expected to be very formal, and behave courteously with manners in any situation, especially while in group discussions etc.",
             "எந்த உரையாடலிலும், தாய்மொழி அல்லது வட்டார மொழியின் தாக்கம் இல்லாமல் சரியான idiom, வெளிப்பாடு, usage ஆகியவற்றைப் பயன்படுத்துவது அவசியம்; இதில் பண்பும் நாகரிகமும் அடங்கும். எந்தச் சூழ்நிலையிலும், குறிப்பாக group discussion இத்யாதியில், நீங்கள் மிகவும் formal ஆக இருக்க வேண்டும்; பணிவாகவும் நல்ல நடத்தையுடனும் நடந்து கொள்ள வேண்டும்."),
        ],
        lessons=[
            dict(title="Greeting People at Different Times", acts=TEACH, blocks=[
                note("The greeting changes with the time of day. It is the first thing you say when you meet someone.",
                     "நாளின் நேரத்தைப் பொறுத்து வாழ்த்து மாறும். ஒருவரைச் சந்திக்கும்போது நீங்கள் முதலில் சொல்வது இதுதான்."),
                eg("Good morning, Sir. / Good morning, Madam.",
                   "காலை வணக்கம், ஐயா. / காலை வணக்கம், அம்மா."),
                eg("Good afternoon, Sir. / Good afternoon, Madam.",
                   "மதிய வணக்கம், ஐயா. / மதிய வணக்கம், அம்மா."),
                eg("Good evening, Sir. / Good evening, Madam.",
                   "மாலை வணக்கம், ஐயா. / மாலை வணக்கம், அம்மா."),
                eg("Good morning, Raju. How are you?",
                   "காலை வணக்கம், ராஜு. எப்படி இருக்கிறீர்கள்?"),
                eg("Hello Remi, how are you?",
                   "ஹலோ ரெமி, எப்படி இருக்கிறீர்கள்?"),
            ]),
            dict(title="Meeting Someone for the First Time", acts=SPEAK, blocks=[
                note("Use these when you meet a person for the first time, or when a common friend introduces someone to you. The other person answers in the same way.",
                     "ஒருவரை முதல் முறையாகச் சந்திக்கும்போது, அல்லது ஒரு பொதுவான நண்பர் அறிமுகப்படுத்தும்போது இவற்றைப் பயன்படுத்துங்கள். எதிரே இருப்பவரும் அதே மாதிரியே பதில் சொல்வார்."),
                eg("I'm glad to meet you.", "உங்களைச் சந்தித்ததில் மகிழ்ச்சி."),
                eg("Glad to meet you, Sir.", "உங்களைச் சந்தித்ததில் மகிழ்ச்சி, ஐயா."),
                eg("Nice meeting you.", "உங்களைச் சந்தித்தது மகிழ்ச்சி."),
                eg("Pleased to meet you.", "உங்களைச் சந்திப்பதில் மகிழ்ச்சி."),
                eg("How do you do?", "எப்படி இருக்கிறீர்கள்? (முதல் அறிமுகத்தில்)"),
            ]),
            dict(title="Asking How Someone Is", acts=SPEAK, blocks=[
                note("When a friend greets you with 'Hello, how are you?', answer politely and ask the same question back.",
                     "ஒரு நண்பர் 'Hello, how are you?' என்று வாழ்த்தும்போது, பணிவாகப் பதில் சொல்லி, அதே கேள்வியைத் திருப்பிக் கேளுங்கள்."),
                eg("I'm fine, thank you. How are you?",
                   "நான் நலமாக இருக்கிறேன், நன்றி. நீங்கள் எப்படி இருக்கிறீர்கள்?"),
                eg("I'm very well, thank you.", "நான் நலமாக இருக்கிறேன், நன்றி."),
                eg("It's a long time since we met. How are things?",
                   "நாம் சந்தித்து ரொம்ப நாளாகிவிட்டது. எல்லாம் எப்படி இருக்கிறது?"),
                eg("How is everything?", "எல்லாம் எப்படி இருக்கிறது?"),
            ]),
            dict(title="Saying Goodbye", acts=TEACH, blocks=[
                note("When you leave, wish the person you are with.",
                     "நீங்கள் கிளம்பும்போது, உங்களுடன் இருப்பவருக்கு வாழ்த்துச் சொல்லுங்கள்."),
                eg("Goodbye, Sir. / Goodbye, Madam.", "பை பை, ஐயா. / பை பை, அம்மா."),
                eg("Bye-bye, friends.", "பை பை, நண்பர்களே."),
                eg("See you later.", "பிறகு பார்க்கலாம்."),
                eg("Good night.", "இரவு வணக்கம். (இரவில் பிரியும்போது)"),
            ]),
            dict(title="Practice: Greetings", acts=PRACTICE, questions=[
                ("How do you greet your teacher at nine in the morning?",
                 "Good morning, Sir.",
                 "காலை ஒன்பது மணிக்கு உங்கள் ஆசிரியரை எப்படி வாழ்த்துவீர்கள்?",
                 "காலை வணக்கம், ஐயா."),
                ("How do you greet a friend in the afternoon?",
                 "Good afternoon, Remi. How are you?",
                 "மதியம் ஒரு நண்பரை எப்படி வாழ்த்துவீர்கள்?",
                 "மதிய வணக்கம், ரெமி. எப்படி இருக்கிறாய்?"),
                ("What do you say when you meet someone for the first time?",
                 "I'm glad to meet you.",
                 "ஒருவரை முதல் முறையாகச் சந்திக்கும்போது என்ன சொல்வீர்கள்?",
                 "உங்களைச் சந்தித்ததில் மகிழ்ச்சி."),
                ("A friend says 'How are you?' What do you answer?",
                 "I'm fine, thank you. How are you?",
                 "ஒரு நண்பர் 'How are you?' என்று கேட்டால் என்ன பதில் சொல்வீர்கள்?",
                 "நான் நலமாக இருக்கிறேன், நன்றி. நீங்கள் எப்படி இருக்கிறீர்கள்?"),
                ("What do you say when you leave at night?",
                 "Good night, Sir.",
                 "இரவில் கிளம்பும்போது என்ன சொல்வீர்கள்?",
                 "இரவு வணக்கம், ஐயா."),
            ]),
            dict(title="Conversation: Meeting an Old Friend", acts=TALK, turns=[
                ("Roy", "friend", "Hello Remi! How are you?", "ஹலோ ரெமி! எப்படி இருக்கிறாய்?"),
                ("Remi", "friend", "I'm fine, thank you. How are you, Roy?", "நான் நலமாக இருக்கிறேன், நன்றி. நீங்கள் எப்படி இருக்கிறீர்கள், ராய்?"),
                ("Roy", "friend", "I'm very well. It's a long time since we met.", "நான் நலமாக இருக்கிறேன். நாம் சந்தித்து ரொம்ப நாளாகிவிட்டது."),
                ("Remi", "friend", "Yes, almost two years. How is everything with you?", "ஆமாம், கிட்டத்தட்ட இரண்டு வருடம். உங்களுக்கு எல்லாம் எப்படி இருக்கிறது?"),
                ("Roy", "friend", "Everything is fine. I'm working in Chennai now.", "எல்லாம் நல்லா இருக்கு. நான் இப்போ சென்னையில் வேலை பார்க்கிறேன்."),
                ("Remi", "friend", "That's nice to hear. See you later, Roy.", "கேட்க சந்தோஷமா இருக்கு. பிறகு பார்க்கலாம், ராய்."),
                ("Roy", "friend", "See you later. Goodbye!", "பிறகு பார்க்கலாம். பை பை!"),
            ]),
        ],
    ),

    # ══ 2 ═════════════════════════════════════════════════════════════════════
    dict(
        section_id="m1_gratitude",
        title="Gratitude",
        module_id="m1_conversation",
        intro=[],
        lessons=[
            dict(title="Saying Thank You", acts=SPEAK, blocks=[
                note("Thanking people is a vital part of British manners. Say it clearly and look at the person.",
                     "நன்றி சொல்வது British பண்பாட்டின் மிக முக்கியமான பகுதி. தெளிவாகச் சொல்லி, அவர் முகத்தைப் பார்த்துச் சொல்லுங்கள்."),
                eg("Thank you, Sir. / Thank you, Madam.", "நன்றி, ஐயா. / நன்றி, அம்மா."),
                eg("That is very kind of you, Raju.", "நீங்கள் ரொம்ப கனிவானவர், ராஜு."),
                eg("I'm really grateful to you, Sir, for your timely help.",
                   "சரியான நேரத்தில் உதவியதற்கு நான் உங்களுக்கு மிகவும் கடமைப்பட்டிருக்கிறேன், ஐயா."),
                eg("Thank you so much.", "மிக்க நன்றி."),
            ]),
            dict(title="Responding to Thanks", acts=TEACH, blocks=[
                note("When someone thanks you, answer in one of these standard ways. Do not invent your own answer.",
                     "யாராவது உங்களுக்கு நன்றி சொன்னால், இந்த standard வழிகளில் ஒன்றில் பதில் சொல்லுங்கள். உங்கள் சொந்த பதிலை உருவாக்காதீர்கள்."),
                eg("That's all right, Sekar.", "பரவாயில்லை, சேகர்."),
                eg("Not at all, Sekar.", "இல்லவே இல்லை, சேகர்."),
                eg("It's a pleasure.", "இது ஒரு சந்தோஷம்."),
                eg("Don't mention it.", "அதைப் பற்றிப் பேச வேண்டாம்."),
                eg("You are most welcome.", "மிகவும் வரவேற்கிறேன்."),
            ]),
            dict(title="Practice: Thanking and Responding", acts=PRACTICE, questions=[
                ("Your friend helps you with your homework. What do you say?",
                 "Thank you, Remi. That is very kind of you.",
                 "உங்கள் நண்பர் வீட்டுப்பாடத்தில் உதவுகிறார். என்ன சொல்வீர்கள்?",
                 "நன்றி, ரெமி. நீங்கள் ரொம்ப கனிவானவர்."),
                ("Someone says 'Thank you, Raju.' How do you reply?",
                 "Not at all.",
                 "யாராவது 'Thank you, Raju' என்று சொன்னால் எப்படிப் பதில் சொல்வீர்கள்?",
                 "இல்லவே இல்லை."),
                ("Your teacher gives you extra time to finish. What do you say?",
                 "Thank you, Madam. I'm really grateful to you.",
                 "உங்கள் ஆசிரியர் முடிக்க கூடுதல் நேரம் தருகிறார். என்ன சொல்வீர்கள்?",
                 "நன்றி, அம்மா. நான் உங்களுக்கு மிகவும் கடமைப்பட்டிருக்கிறேன்."),
                ("A stranger holds the door open for you. What do you say?",
                 "Thank you very much.",
                 "ஒரு அந்நியர் உங்களுக்காகக் கதவைப் பிடித்து வைத்திருக்கிறார். என்ன சொல்வீர்கள்?",
                 "மிக்க நன்றி."),
            ]),
            dict(title="Conversation: Thanking a Colleague", acts=TALK, turns=[
                ("Sekar", "colleague", "Raju, could you send me the report today?", "ராஜு, இன்று அந்த report-ஐ எனக்கு அனுப்ப முடியுமா?"),
                ("Raju", "colleague", "Of course, Sekar. I'll send it before five o'clock.", "கண்டிப்பா, சேகர். ஐந்து மணிக்கு முன்னாடி அனுப்பிடுறேன்."),
                ("Sekar", "colleague", "Thank you, Raju. That is very kind of you.", "நன்றி, ராஜு. நீங்கள் ரொம்ப கனிவானவர்."),
                ("Raju", "colleague", "Not at all, Sekar. It's a pleasure.", "இல்லவே இல்லை, சேகர். இது ஒரு சந்தோஷம்."),
                ("Sekar", "colleague", "Goodbye, Raju.", "பை பை, ராஜு."),
                ("Raju", "colleague", "Goodbye, Sekar. See you tomorrow.", "பை பை, சேகர். நாளை பார்க்கலாம்."),
            ]),
        ],
    ),

    # ══ 3 ═════════════════════════════════════════════════════════════════════
    dict(
        section_id="m1_wishes_festive",
        title="Wishes at Celebrations and Festive Occasions",
        module_id="m1_conversation",
        intro=[],
        lessons=[
            dict(title="Wishing on Happy Occasions", acts=TEACH, blocks=[
                note("Use 'Congratulations' for good news — a wedding, an examination result, a new baby, or an election win.",
                     "நல்ல செய்திக்கு — திருமணம், தேர்வு முடிவு, குழந்தை பிறப்பு, அல்லது தேர்தல் வெற்றி — 'Congratulations' என்று சொல்லுங்கள்."),
                eg("Congratulations! Wish you a happy married life.",
                   "வாழ்த்துகள்! மகிழ்ச்சியான தாம்பத்ய வாழ்க்கை வாழ்த்துகிறேன்."),
                eg("Congratulations on your success in the examination!",
                   "தேர்வில் வெற்றி பெற்றதற்கு வாழ்த்துகள்!"),
                eg("Congratulations on the new arrival!",
                   "குழந்தை பிறந்ததற்கு வாழ்த்துகள்!"),
                eg("Congratulations on your winning the election!",
                   "தேர்தலில் வெற்றி பெற்றதற்கு வாழ்த்துகள்!"),
            ]),
            dict(title="Practice: Wishing People", acts=PRACTICE, questions=[
                ("Your friend is getting married. What do you say?",
                 "Congratulations! Wish you a happy married life.",
                 "உங்கள் நண்பர் திருமணம் செய்கிறார். என்ன சொல்வீர்கள்?",
                 "வாழ்த்துகள்! மகிழ்ச்சியான தாம்பத்ய வாழ்க்கை வாழ்த்துகிறேன்."),
                ("Your sister has passed her examination. What do you say?",
                 "Congratulations on your success!",
                 "உங்கள் சகோதரி தேர்வில் வெற்றி பெற்றிருக்கிறார். என்ன சொல்வீர்கள்?",
                 "வெற்றிக்கு வாழ்த்துகள்!"),
                ("Your neighbour has a baby girl. What do you say?",
                 "Congratulations on the new arrival!",
                 "உங்கள் அண்டை வீட்டாருக்கு பெண் குழந்தை பிறந்திருக்கிறது. என்ன சொல்வீர்கள்?",
                 "குழந்தை பிறந்ததற்கு வாழ்த்துகள்!"),
                ("Your uncle has won the election. What do you say?",
                 "Congratulations on your winning the election!",
                 "உங்கள் மாமா தேர்தலில் வெற்றி பெற்றிருக்கிறார். என்ன சொல்வீர்கள்?",
                 "தேர்தல் வெற்றிக்கு வாழ்த்துகள்!"),
            ]),
        ],
    ),

    # ══ 4 ═════════════════════════════════════════════════════════════════════
    dict(
        section_id="m1_wishes_exams",
        title="Wishes Before an Examination",
        module_id="m1_conversation",
        intro=[],
        lessons=[
            dict(title="Wishing Someone Good Luck", acts=SPEAK, blocks=[
                note("Before an examination, an interview or an election, wish the person success.",
                     "தேர்வு, நேர்காணல் அல்லது தேர்தலுக்கு முன், அந்த நபருக்கு வெற்றியை வாழ்த்துங்கள்."),
                eg("I wish you success.", "உங்கள் வெற்றியை வாழ்த்துகிறேன்."),
                eg("I wish you all the best.", "எல்லா நல்வாழ்த்துகளும்."),
                eg("All the best for your interview.", "உங்கள் நேர்காணலுக்கு வாழ்த்துகள்."),
                eg("Good luck!", "நல்ல அதிர்ஷ்டம்!"),
            ]),
            dict(title="Practice: Good Wishes", acts=PRACTICE, questions=[
                ("Your friend is writing an examination tomorrow. What do you say?",
                 "I wish you all the best.",
                 "உங்கள் நண்பர் நாளை தேர்வு எழுதுகிறார். என்ன சொல்வீர்கள்?",
                 "எல்லா நல்வாழ்த்துகளும்."),
                ("Your brother is going for an interview. What do you say?",
                 "All the best for your interview.",
                 "உங்கள் சகோதரர் நேர்காணலுக்குச் செல்கிறார். என்ன சொல்வீர்கள்?",
                 "உங்கள் நேர்காணலுக்கு வாழ்த்துகள்."),
                ("Your colleague is contesting an election. What do you say?",
                 "I wish you success.",
                 "உங்கள் சக ஊழியர் தேர்தலில் போட்டியிடுகிறார். என்ன சொல்வீர்கள்?",
                 "உங்கள் வெற்றியை வாழ்த்துகிறேன்."),
            ]),
        ],
    ),
]
