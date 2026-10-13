"""End-of-lesson checks, written for the lessons whose content is prose.

Each entry is the lesson's `content_id` -> list of (question, model answer,
question Tamil, answer Tamil). A lesson gets one or two, drawn from what it just
taught, so the app can ask and mark it. Table-shaped lessons are generated in
author_checks.py from the book's own rows and do not appear here.
"""


def c(q, a, qta, ata):
    return (q, a, qta, ata)


HAND = {
    # ── Module 1 — Conversation ──────────────────────────────────────────────
    "a900003": [
        c("How do you greet someone in the morning?",
          "Good morning, Sir. / Good morning, Madam.",
          "காலையில் ஒருவரை எப்படி வாழ்த்துவீர்கள்?",
          "காலை வணக்கம், ஐயா. / காலை வணக்கம், அம்மா."),
        c("How do you greet someone in the evening?",
          "Good evening, Sir. / Good evening, Madam.",
          "மாலையில் ஒருவரை எப்படி வாழ்த்துவீர்கள்?",
          "மாலை வணக்கம், ஐயா. / மாலை வணக்கம், அம்மா."),
    ],
    "a900004": [
        c("What do you say when you meet a person for the first time?",
          "I'm glad to meet you.", "ஒருவரை முதல் முறையாகச் சந்திக்கும்போது என்ன சொல்வீர்கள்?",
          "உங்களைச் சந்தித்ததில் மகிழ்ச்சி."),
    ],
    "a900005": [
        c("A friend asks ‘How are you?’ What do you answer?",
          "I'm fine, thank you. How are you?", "நண்பர் ‘How are you?’ என்று கேட்டால் என்ன பதில்?",
          "நான் நலமாக இருக்கிறேன், நன்றி. நீங்கள் எப்படி இருக்கிறீர்கள்?"),
    ],
    "a900009": [
        c("How do you thank a teacher who helped you?",
          "Thank you, Sir. That is very kind of you.", "உதவிய ஆசிரியருக்கு எப்படி நன்றி சொல்வீர்கள்?",
          "நன்றி, ஐயா. நீங்கள் ரொம்ப கனிவானவர்."),
    ],
    "a900013": [
        c("Your friend is getting married. What do you say?",
          "Congratulations! Wish you a happy married life.", "நண்பர் திருமணம் செய்கிறார். என்ன சொல்வீர்கள்?",
          "வாழ்த்துகள்! மகிழ்ச்சியான தாம்பத்ய வாழ்க்கை வாழ்த்துகிறேன்."),
    ],
    "a900017": [
        c("What do you say when a friend loses a dear one?",
          "I am sorry about your loss. Please accept my heartfelt condolences.",
          "நண்பர் பிரியமானவரை இழந்தால் என்ன சொல்வீர்கள்?",
          "உங்கள் இழப்புக்கு நான் வருந்துகிறேன். என் ஆழ்ந்த இரங்கலை ஏற்றுக்கொள்ளுங்கள்."),
    ],
    "a900021": [
        c("How do you politely ask someone to help you?",
          "Could you please help me?", "பணிவாக ஒருவரிடம் உதவி எப்படிக் கேட்பீர்கள்?",
          "தயவுசெய்து எனக்கு உதவ முடியுமா?"),
    ],
    "a900022": [
        c("How do you introduce yourself on the telephone?",
          "Hello, this is Raju speaking.", "தொலைபேசியில் உங்களை எப்படி அறிமுகப்படுத்துவீர்கள்?",
          "ஹலோ, நான் ராஜு பேசுகிறேன்."),
    ],
    "a900025": [
        c("You have not eaten since morning. What do you say?",
          "I am hungry.", "காலையிலிருந்து சாப்பிடவில்லை. என்ன சொல்வீர்கள்?",
          "எனக்குப் பசிக்கிறது."),
    ],
    "a900030": [
        c("How do you politely offer someone a cup of coffee?",
          "Would you like to have a cup of coffee?", "பணிவாக ஒரு கப் காபி எப்படிக் கொடுப்பீர்கள்?",
          "ஒரு கப் காபி சாப்பிட விருப்பமா?"),
    ],
    "a900031": [
        c("Which question would you use to ask permission to come in?",
          "May I come in?", "உள்ளே வர அனுமதி கேட்க எந்தக் கேள்வியைப் பயன்படுத்துவீர்கள்?",
          "நான் உள்ளே வரலாமா?"),
    ],
    "a900034": [
        c("Ask a friend what time he will meet you tomorrow.",
          "At what time will you meet me tomorrow?", "நாளை எத்தனை மணிக்குச் சந்திக்கிறாய் என்று கேளுங்கள்.",
          "நாளை எத்தனை மணிக்கு என்னைச் சந்திக்கிறாய்?"),
    ],
    "a900035": [
        c("A friend asks you to lunch but you are busy. What do you say?",
          "I am sorry, I will not be able to come.", "நண்பர் மதிய உணவுக்கு அழைக்கிறார், நீங்கள் வேலையாக இருக்கிறீர்கள். என்ன சொல்வீர்கள்?",
          "மன்னிக்கவும், என்னால் வர முடியாது."),
    ],
    "a900039": [
        c("Ask a friend how he rates a film.",
          "How do you rate the film?", "ஒரு படத்தை எப்படி மதிப்பிடுகிறாய் என்று நண்பரிடம் கேளுங்கள்.",
          "படத்திற்கு எவ்வளவு மதிப்பு தருவாய்?"),
    ],
    "a900041": [
        c("What is your favourite game?",
          "My favourite game is football.", "உங்களுக்குப் பிடித்த விளையாட்டு என்ன?",
          "எனக்குப் பிடித்த விளையாட்டு கால்பந்து."),
    ],
    "a900043": [
        c("How do you spend your holidays?",
          "I normally go to my uncle's home in a village near Kodaikanal.",
          "உங்கள் விடுமுறையை எப்படிக் கழிக்கிறீர்கள்?",
          "நான் வழக்கமாக கொடைக்கானல் அருகில் ஒரு கிராமத்தில் என் மாமா வீட்டிற்குச் செல்வேன்."),
    ],
    "a900046": [
        c("Where is Tiruchy situated?",
          "Tiruchy is an ancient city on the river Cauvery.", "திருச்சி எங்கே அமைந்திருக்கிறது?",
          "திருச்சி காவிரி ஆற்றங்கரையில் உள்ள பழமையான நகரம்."),
    ],
    "a900048": [
        c("Why do you like your favourite leader?",
          "I like him because he keeps his word.", "உங்களுக்குப் பிடித்த தலைவர் ஏன் பிடிக்கும்?",
          "அவர் சொன்னதை நிறைவேற்றுவதால் எனக்குப் பிடிக்கும்."),
    ],

    # ── Module 2 — Vocabulary (the prose lessons; tables are generated) ──────
    "c0100": [
        c("What is a syllable?", "A single speech unit, like the word ‘cut’.",
          "Syllable என்றால் என்ன?", "ஒரு பேச்சு அலகு — உதாரணம் ‘cut’ என்ற சொல்."),
    ],
    "c0116": [
        c("How is ‘c’ pronounced in ‘cell’?", "As ‘s’.",
          "‘cell’ என்ற சொல்லில் ‘c’ எப்படி உச்சரிக்கப்படுகிறது?", "‘s’ போல."),
        c("How is ‘c’ pronounced in ‘cord’?", "As ‘k’.",
          "‘cord’ என்ற சொல்லில் ‘c’ எப்படி உச்சரிக்கப்படுகிறது?", "‘k’ போல."),
    ],
    "c0162": [
        c("What is the feminine of ‘author’?", "Authoress.",
          "‘author’-இன் பெண்பால் என்ன?", "Authoress."),
    ],
    "c0181": [
        c("Which word does not belong: cold, spring, winter, summer?",
          "Cold — it is not a season.", "எந்தச் சொல் பொருந்தவில்லை: cold, spring, winter, summer?",
          "Cold — அது ஒரு பருவம் அல்ல."),
    ],
    "c0188": [
        c("Rearrange ‘esroh’.", "Horse.", "‘esroh’-ஐச் சரிசெய்யுங்கள்.", "Horse."),
    ],
    "c0207": [
        c("Which word is closest in meaning to ‘educate’?", "Instruct.",
          "‘educate’-க்கு அருகில் பொருள் தரும் சொல் எது?", "Instruct."),
    ],
    "c0213": [
        c("Which word is opposite in meaning to ‘voluntary’?", "Compulsory.",
          "‘voluntary’-க்கு எதிர்ப் பொருள் தரும் சொல் எது?", "Compulsory."),
    ],
    "c0223": [
        c("Which word does not belong: talk, eyes, ears, nose?",
          "Talk — it is not a part of the body.", "எந்தச் சொல் பொருந்தவில்லை: talk, eyes, ears, nose?",
          "Talk — அது உடலின் ஒரு பகுதி அல்ல."),
    ],
    "c0231": [
        c("Catch, runout, wicket and pitch are words used in which game?",
          "Cricket.", "Catch, runout, wicket, pitch — இவை எந்த விளையாட்டுச் சொற்கள்?",
          "கிரிக்கெட்."),
    ],

    # ── Module 3 — Grammar ───────────────────────────────────────────────────
    "c0256": [
        c("What is a sentence?",
          "A group of words that conveys meaning, with a subject and a verb.",
          "வாக்கியம் என்றால் என்ன?",
          "எழுவாயும் வினையும் உள்ள, பொருள் தரும் சொற்களின் தொகுப்பு."),
    ],
    "c0264": [
        c("What is an assertive sentence?", "A sentence which gives us information about something.",
          "Assertive வாக்கியம் என்றால் என்ன?", "ஏதோ ஒன்றைப் பற்றித் தகவல் தரும் வாக்கியம்."),
    ],
    "c0266": [
        c("What is an interrogative sentence?",
          "A sentence which raises a question to get some information.",
          "Interrogative வாக்கியம் என்றால் என்ன?", "தகவல் பெற ஒரு கேள்வி கேட்கும் வாக்கியம்."),
    ],
    "c0268": [
        c("What is an imperative sentence?",
          "A sentence which gives orders, makes requests or gives advice.",
          "Imperative வாக்கியம் என்றால் என்ன?", "கட்டளை, வேண்டுகோள் அல்லது ஆலோசனை தரும் வாக்கியம்."),
    ],
    "c0287": [
        c("What is the plural of ‘enemy’?", "Enemies.",
          "‘enemy’-இன் பன்மை என்ன?", "Enemies."),
    ],
    "c0298": [
        c("Which is correct: ‘The members of his family have come’ or ‘has come’?",
          "The members of his family have come.",
          "எது சரி: ‘The members of his family have come’-ஆ ‘has come’-ஆ?",
          "The members of his family have come."),
    ],
    "c0300": [
        c("Say correctly: ‘Mathematics (is / are) a difficult subject.’",
          "Mathematics is a difficult subject.",
          "சரியாகச் சொல்லுங்கள்: ‘Mathematics (is / are) a difficult subject.’",
          "Mathematics is a difficult subject."),
    ],
    "c0305": [
        c("Name the demonstrative pronouns.", "This, that, these, those and such.",
          "Demonstrative pronouns-ஐச் சொல்லுங்கள்.", "This, that, these, those, such."),
    ],
    "c0313": [
        c("In ‘Each woman carried a basket’, which word is the distributive adjective?",
          "Each.", "‘Each woman carried a basket’ — distributive adjective எது?", "Each."),
    ],
    "c0330": [
        c("What is a verb of incomplete predication?",
          "A verb that does not have a complete sense and needs a word after it.",
          "Verb of incomplete predication என்றால் என்ன?",
          "முழுப் பொருள் இல்லாமல், பின் ஒரு சொல் தேவைப்படும் வினைச்சொல்."),
    ],
    "c0332": [
        c("Say correctly: ‘Two and two (make / makes) four.’", "Two and two makes four.",
          "சரியாகச் சொல்லுங்கள்: ‘Two and two (make / makes) four.’", "Two and two makes four."),
    ],
    "c0357": [
        c("Which tense do we use for an action happening now?",
          "The simple present tense.", "இப்போது நடக்கும் செயலுக்கு எந்தக் காலம்?",
          "Simple present tense."),
    ],
    "c0362": [
        c("Which tense is used for an action just over in the recent past?",
          "The present perfect tense.", "சமீபத்தில் முடிந்த செயலுக்கு எந்தக் காலம்?",
          "Present perfect tense."),
    ],
    "c0366": [
        c("Which tense shows an action completed before another past action?",
          "The past perfect tense.", "மற்றொரு இறந்த காலச் செயலுக்கு முன் முடிந்த செயலை எந்தக் காலம் காட்டும்?",
          "Past perfect tense."),
    ],
    "c0367": [
        c("Which tense is used when two past actions were going on together?",
          "The past perfect continuous tense.", "இரண்டு இறந்த காலச் செயல்கள் தொடர்ந்தால் எந்தக் காலம்?",
          "Past perfect continuous tense."),
    ],
    "c0370": [
        c("Which tense shows an action that will be completed before another future action?",
          "The future perfect tense.", "மற்றொரு எதிர் காலச் செயலுக்கு முன் முடியும் செயலை எந்தக் காலம் காட்டும்?",
          "Future perfect tense."),
    ],
    "c0371": [
        c("Which tense shows an action still in progress at a future time?",
          "The future perfect continuous tense.", "எதிர் காலத்தில் தொடர்ந்து நடக்கும் செயலை எந்தக் காலம் காட்டும்?",
          "Future perfect continuous tense."),
    ],
    "c0406": [
        c("State Rule 1 of the sequence of tenses.",
          "A past tense in the main clause is followed by a past tense in the subordinate clause.",
          "Sequence of tenses-இன் முதல் விதியைச் சொல்லுங்கள்.",
          "முதன்மைப் பகுதியில் இறந்த காலம் இருந்தால், துணைப் பகுதியிலும் இறந்த காலம் வரும்."),
    ],
    "c0407": [
        c("What tense does a universal truth take in the subordinate clause?",
          "The present tense.", "பொதுவான உண்மை துணைப் பகுதியில் எந்தக் காலத்தில் இருக்கும்?",
          "நிகழ் காலம்."),
    ],
    "c0408": [
        c("Which conjunction lets the subordinate clause keep any tense?",
          "Than.", "எந்த இணைப்புச் சொல் துணைப் பகுதியை எந்தக் காலத்திலும் வைக்க அனுமதிக்கும்?",
          "Than."),
    ],
    "c0409": [
        c("State Rule 2 of the sequence of tenses.",
          "A present or future tense in the main clause may be followed by any tense.",
          "Sequence of tenses-இன் இரண்டாம் விதியைச் சொல்லுங்கள்.",
          "முதன்மைப் பகுதி நிகழ் அல்லது எதிர் காலத்தில் இருந்தால், எந்தக் காலமும் வரலாம்."),
    ],
    "c0412": [
        c("In the active voice, what is the subject?", "The doer of the action.",
          "செய்வினையில் எழுவாய் யார்?", "செயலைச் செய்பவர்."),
    ],
    "c0421": [
        c("How many objects do certain verbs take in the active voice?", "Two.",
          "சில வினைச்சொற்கள் செய்வினையில் எத்தனை objects எடுக்கும்?", "இரண்டு."),
    ],
    "c0463": [
        c("What introduces an adjective clause?",
          "A relative pronoun or a relative adverb.", "Adjective clause-ஐ எது அறிமுகப்படுத்துகிறது?",
          "Relative pronoun அல்லது relative adverb."),
    ],
    "c0465": [
        c("Which conjunctions introduce an adverb clause of time?",
          "When, whenever, while, after and before.",
          "Adverb clause of time-ஐ எந்த இணைப்புச் சொற்கள் அறிமுகப்படுத்துகின்றன?",
          "When, whenever, while, after, before."),
    ],
    "c0466": [
        c("Which conjunctions introduce an adverb clause of place?",
          "Where, wherever and whither.",
          "Adverb clause of place-ஐ எந்த இணைப்புச் சொற்கள் அறிமுகப்படுத்துகின்றன?",
          "Where, wherever, whither."),
    ],
    "c0467": [
        c("Which conjunctions introduce an adverb clause of purpose?",
          "Because, as, since and that.",
          "Adverb clause of purpose-ஐ எந்த இணைப்புச் சொற்கள் அறிமுகப்படுத்துகின்றன?",
          "Because, as, since, that."),
    ],
    "c0468": [
        c("Which conjunctions introduce an adverb clause of condition?",
          "If, whether and unless.",
          "Adverb clause of condition-ஐ எந்த இணைப்புச் சொற்கள் அறிமுகப்படுத்துகின்றன?",
          "If, whether, unless."),
    ],
    "c0469": [
        c("Which conjunction introduces an adverb clause of result?", "So.",
          "Adverb clause of result-ஐ எந்த இணைப்புச் சொல் அறிமுகப்படுத்துகிறது?", "So."),
    ],
    "c0472": [
        c("Which conjunctions introduce an adverb clause of supposition or contrast?",
          "Though and although.", "Adverb clause of supposition அல்லது contrast-ஐ எந்த இணைப்புச் சொற்கள் அறிமுகப்படுத்துகின்றன?",
          "Though, although."),
    ],
    "c0500": [
        c("When do we use the article ‘a’?",
          "Before a noun beginning with the sound of a consonant.",
          "‘a’ என்ற article-ஐ எப்போது பயன்படுத்துவோம்?",
          "மெய் ஒலியில் தொடங்கும் பெயர்ச்சொல்லுக்கு முன்."),
    ],
    "c0501": [
        c("Give an idiomatic use of ‘a few’.", "A few, a little.",
          "‘a few’-இன் idiomatic பயன்பாட்டைச் சொல்லுங்கள்.", "A few, a little."),
    ],
    "c0502": [
        c("When do we use the definite article ‘the’?",
          "When we refer to some particular person or thing.",
          "‘the’ என்ற definite article-ஐ எப்போது பயன்படுத்துவோம்?",
          "ஒரு குறிப்பிட்ட நபர் அல்லது பொருளைக் குறிக்கும்போது."),
    ],
    "c0507": [
        c("What is a question tag?", "A short question attached to a statement.",
          "Question tag என்றால் என்ன?", "ஒரு கூற்றுடன் இணைக்கப்படும் சிறிய கேள்வி."),
    ],
    "c0293": [
        c("Say a sentence with ‘deer’ in the plural.",
          "These deer have beautiful horns.",
          "‘deer’-ஐப் பன்மையில் வைத்து ஒரு வாக்கியம் சொல்லுங்கள்.",
          "These deer have beautiful horns."),
    ],
    "c0553": [
        c("How is our reaction to conflict also based?",
          "On how we experienced conflicts while growing up.",
          "மோதலுக்கான நம் எதிர்வினை எதன் அடிப்படையில் இருக்கிறது?",
          "வளரும்போது மோதல்களை எப்படி அனுபவித்தோம் என்பதன் அடிப்படையில்."),
    ],

    # ── Module 4 — Comprehension ─────────────────────────────────────────────
    "c0522": [
        c("What had happened to the old lady?", "She became blind.",
          "அந்தப் பழைய பெண்மைக்கு என்ன ஆயிற்று?", "அவர் பார்வையிழந்தார்."),
    ],
    "c0523": [
        c("Why did the jackal want to go to the other side of the river?",
          "To eat the crabs found there.", "நரி ஆற்றின் மறுகரைக்கு ஏன் செல்ல விரும்பியது?",
          "அங்கிருந்த நண்டுகளைச் சாப்பிட."),
    ],
    "c0524": [
        c("Who was appointed to take care of the king's son?",
          "A young mother with a baby.", "அரசனின் மகனைப் பராமரிக்க யார் நியமிக்கப்பட்டார்?",
          "ஒரு கைக்குழந்தையுடன் இருந்த இளம் தாய்."),
    ],
    "c0525": [
        c("Why did the miser become sad?",
          "He lost a purse of a hundred pieces of gold.", "கஞ்சன் ஏன் வருத்தப்பட்டான்?",
          "நூறு பொன் காசுகள் இருந்த பணப்பையை இழந்ததால்."),
    ],
    "c0526": [
        c("What was the king's plan to teach his people?",
          "He put a very big stone in the middle of the road.",
          "மக்களுக்குப் பாடம் கற்பிக்க அரசன் என்ன திட்டம் வைத்தார்?",
          "சாலையின் நடுவில் ஒரு மிகப் பெரிய கல்லை வைத்தார்."),
    ],
    "c0527": [
        c("Why did the ant come to the stream?", "To drink water.",
          "எறும்பு ஏன் ஆற்றங்கரைக்கு வந்தது?", "நீர் அருந்த."),
    ],

    # ── Module 5 — Composition ───────────────────────────────────────────────
    "c0537": [
        c("What does corruption affect?", "Human rights and the rule of law.",
          "ஊழல் எதைப் பாதிக்கிறது?", "மனித உரிமைகளையும் சட்டத்தின் ஆட்சியையும்."),
    ],
    "c0540": [
        c("How did Mother Teresa remain all her life?",
          "Humble, simple and in many senses an ordinary woman.",
          "மதர் தெரசா வாழ்நாள் முழுவதும் எப்படி இருந்தார்?",
          "பணிவாக, எளிமையாக, பல வகைகளில் ஒரு சாதாரண பெண்ணாக."),
    ],
    "c0544": [
        c("Where is IRMA situated?", "In Anand, Gujarat.",
          "IRMA எங்கே அமைந்திருக்கிறது?", "குஜராத் மாநிலம் ஆனந்தில்."),
    ],
    "c0545": [
        c("What does IRMA offer besides research and consultancy?",
          "Post-graduate programmes in rural management.",
          "ஆராய்ச்சி, ஆலோசனை தவிர IRMA என்ன தருகிறது?",
          "ஊரக மேலாண்மையில் முதுகலைப் பட்டப்படிப்புகள்."),
    ],
    "c0547": [
        c("What do most studies show about women?",
          "That women have more difficulty establishing their singularity than men.",
          "பெண்கள் பற்றி பெரும்பாலான ஆய்வுகள் என்ன காட்டுகின்றன?",
          "ஆண்களை விடப் பெண்கள் தனித்துவத்தை நிலைநாட்டுவதில் அதிக சிரமம் கொள்கிறார்கள்."),
    ],
    "c0549": [
        c("Are women by nature weaker and more dependent?",
          "Not at all. It has to do with how small children are brought up.",
          "பெண்கள் இயற்கையிலேயே பலவீனமானவர்களா?",
          "இல்லவே இல்லை. சிறு குழந்தைகள் வளர்க்கப்படும் முறையே காரணம்."),
    ],
    "c0550": [
        c("Whose illuminating work does the passage mention?", "Nancy Chodorow's.",
          "பத்தியில் யாருடைய ஆய்வு குறிப்பிடப்படுகிறது?", "Nancy Chodorow."),
    ],
    "c0552": [
        c("How do people react to conflicts?",
          "Differently — some calmly and others with an explosive response.",
          "மக்கள் மோதல்களுக்கு எப்படி எதிர்வினை ஆற்றுகிறார்கள்?",
          "வேறுபடுகிறார்கள் — சிலர் அமைதியாக, சிலர் வெடிக்கும் விதத்தில்."),
    ],
    "c0554": [
        c("When were our reactions to conflicts learned?", "Early in our lives.",
          "மோதலுக்கான நம் எதிர்வினைகள் எப்போது கற்றுக்கொள்ளப்பட்டன?", "நம் சிறுவயதிலேயே."),
    ],
    "c0555": [
        c("What is another piece of the puzzle for understanding conflict?",
          "Reviewing the ways you react to conflict.",
          "மோதலைப் புரிந்துகொள்ள உதவும் இன்னொரு பகுதி என்ன?",
          "மோதலுக்கு நீங்கள் எதிர்வினை ஆற்றும் விதங்களை மறுபரிசீலனை செய்வது."),
    ],
    "c0567": [
        c("What is the first model letter asking for?", "A bonafide certificate.",
          "முதல் மாதிரிக் கடிதம் எதைக் கேட்கிறது?", "Bonafide சான்றிதழ்."),
    ],
    "c0576": [
        c("What is the second model letter asking for?",
          "A conduct certificate or transfer certificate.",
          "இரண்டாவது மாதிரிக் கடிதம் எதைக் கேட்கிறது?", "நடத்தைச் சான்றிதழ் அல்லது இடமாற்றுச் சான்றிதழ்."),
    ],
    "c0591": [
        c("What does the father give the boy?", "Some apples.",
          "தந்தை மகனுக்கு என்ன கொடுக்கிறார்?", "சில ஆப்பிள்கள்."),
    ],
    "c0592": [
        c("What do two men travelling through a forest agree to do?",
          "To help each other in danger.", "காட்டில் பயணிக்கும் இரண்டு பேர் என்ன ஒப்புக்கொள்கிறார்கள்?",
          "ஆபத்தில் ஒருவருக்கொருவர் உதவுவது."),
    ],
    "c0593": [
        c("Who came to visit King Solomon?", "The queen of Sheba.",
          "சாலமன் அரசனைப் பார்க்க யார் வந்தார்?", "ஷீபா ராணி."),
    ],
}
