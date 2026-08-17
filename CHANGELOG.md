# Changelog

All notable changes, pipeline upgrades, dictionary filtering rules, and dataset generations for the Tamil Wordle project are documented in this file.

---

## [Unreleased] - 2026-08-16

### Added
- **User Word History Tracking & Interactive History Modal (`frontend/`)**:
  - Persistent client-side history logging in `localStorage` under `tamilWordleHistory`.
  - Captures target word, syllable length, date/day count, win/loss status, number of attempts, time taken, and guess sequence.
  - Interactive **History Modal (`சொல் வரலாறு`)** with summary metrics (Total Played, Win %, Avg Tries), filter chips (All, 3-letter, 4-letter, 5-letter, Won, Lost), game cards, and direct Agarathi.com dictionary lookup links.
  - Data export functionality (CSV / JSON) and history reset controls.
- **Morphological Word Filtering Pipeline (`data/filter_words_pipeline.py`)**:
  - High-performance, streaming rule engine capable of classifying and filtering large-scale Tamil frequency datasets (4.59M words).
  - Exact Tamil Unicode grapheme clustering (`[\u0b80-\u0bff][\u0bbe-\u0bcd\u0bd7]?`) for accurate syllable-based length calculation.
  - Multi-length partitioning (`3, 4, 5` graphemes) and frequency thresholding (`min-freq >= 2`).
  - Automated export of Wordle game JSON assets (`top_words.json`, `words_3.json`, `words_4.json`, `words_5.json`).
- **Comprehensive Excluded Parts of Speech Engine**:
  - Implemented morphological classification rules across 19 categories based on `data/excluded-word-parts-of-speech.txt`:
    1. **Relative Participles (பெயரெச்சம்)**: `-கிற`, `-க்கிற`, `-கின்ற`, `-க்கின்ற` (e.g. `செய்கிற`, `படிக்கிற`, `வருகின்ற`).
    2. **Derived Adjectives (ஆக்கப்பெயரடை)**: Suffix `-ஆன` (`-மான`, `-யான`, `-வான`, `-ரான`, `-லான`, `-தான`, etc., e.g. `உயரமான`, `அழகான`, `முக்கியமான`).
    3. **Inclusive Conjunctions (எண்ணும்மை / உம்மை இடைச்சொல்)**: Phonological u-vowel signs (`\u0bc1`/`\u0bc2`) before `ம்` (`-களும்`, `-யும்`, `-வும்`, `-லும்`, `-தும்`, `-றும்`, `-டும்`, `-ணும்`, `-னும்`, `-மும்`, `-ப்பும்`, e.g. `காலமும்`, `படமும்`, `பெண்ணும்`, `நாடுகளும்`).
    4. **Past Relative Participles (இறந்தகாலப் பெயரெச்சம்)**: `-த்த`, `-ட்ட`, `-ந்த`, `-ற்ற`, `-ன்ற`, `-ிய`, `-ஆத` (e.g. `செய்த`, `வந்த`, `போன`, `கடந்த`, `கட்டிய`, `ஓடிய`, `விரும்பாத`).
    5. **Concessive Conditionals (உம்மை எச்சம் / நிபந்தனை எச்சம்)**: `-போதெல்லாம்`, `-இருந்தும்`, `-செய்தும்`, `-ஆயினும்`, `-ஆனாலும்`, `-போதிலும்`, `-விடின்`.
    6. **Inflected Nouns (வேற்றுமை உருபேற்ற பெயர்ச்சொற்கள்)**: 2nd–7th case inflections (Accusative `-ஐ`, `-களை`, `-வரை`, `-த்தை`, Instrumental/Associative `-ஆல்`, `-உடன்`, `-த்துடன்`, Dative `-க்கு`, `-களுக்கு`, Locative/Ablative `-இல்`, `-இன்`, `-த்தில்`, `-லிருந்து`, Genitive `-உடைய`, `-னுடைய`).
    7. **Emphatic Clitics (தேற்ற ஏகாரம் / ஓகாரம்)**: Suffixes `-ஏ` (`\u0bc7`), `-ஓ` (`\u0bcb`), `-தானே`, `-மட்டுமே`, `-போதே`, `-என்னமோ`.
    8. **Adjectives & Adjectival Markers (பெயரடை)**: `-போன்ற`, `-ஆகிய`, `-உள்ள`, `-முள்ள`, `-யுள்ள`, `-கொண்ட`, `-தக்க`, `-வாய்ந்த`.
    9. **Adjectival Stems (பெயரடை அடிச்சொல்)**: Bound stems (`அதிவேக`, `கரிம`, `சமண`, `ஆதார`, `தூதரக`, `அற்புத`, `பல்லவ`, `டகம`, `அவன`, `அமர`, `நாடக`, `பயங்கர`, `உலக`, `தமிழக`, `தத்துவ`, `மாநில`, `தேசிய`, `மத்திய`).
    10. **Proper Adjectives (சிறப்புப் பெயரடை)**: `இந்திய`, `ஜெர்மன்`, `அரசிய`, `ஆசிய`.
    11. **Interrogative Pronouns (வினாப் பெயர்ச்சொல் / பிரதிப்பெயர்)**: `எவர்`, `யாரு`, `எது`, `எவை`, `யாவை`, `என்ன`, `எங்கு`, `எங்கே`, `எவ்வாறு`, `எப்படி`.
    12. **Past Adverbial Participles (இறந்தகால வினையெச்சம்)**: `-த்து`, `-ந்து`, `-சென்று`, `-செய்து`, `-நின்று`, `-கற்று`, `-பெற்று`, `-விட்டு`, `-போட்டு`, `-கொண்டு` (e.g. `வைத்து`, `பார்த்து`, `செய்து`, `வந்து`, `சென்று`, `நின்று`, `வரவேற்று`, `நீங்கி`, `கழுவி`, `விரட்டி`).
    13. **Possessives (ஆறாம் வேற்றுமை உடைமைப் பெயர்)**: `-தனது`, `-அவரது`, `-எனது`, `-உனது`, `-அவனது`, `-அவளது`, `-தமது`, `-நமது`, `-இவரது`, `-உடைய`, `-னுடைய`.
    14. **Combining Forms (சேர்க்கைச் சொல் முன்னொட்டு)**: `துணை-`, `மறு-`, `நல்-`, `செம்-`, `பெரு-`, `இடை-`, `முன்-`, `பின்-`, `உள்-`, `வெளி-`, `மேல்-`, `கீழ்-`, `அதி-`, `தொல்-`.
    15. **Infinitive Verbs (செயவென் வினையெச்சம் / வியங்கோள்)**: `-க்க`, `-க`, `-ய`, `-ல`, `-ள` (e.g. `பார்க்க`, `படிக்க`, `செய்ய`, `செல்ல`, `சொல்ல`, `வாழ்க`, `அணுக`, `இயங்க`, `ஆராய`, `பெய்ய`, `கையாள`).
    16. **Proper Nouns (சிறப்புப் பெயர்ச்சொற்கள்)**: Places, countries, historical/celebrity names, and name suffixes (`ராமசாமி`, `அசோகன்`, `அகிலன்`, `செல்லப்பா`, `அபிராமி`, `சுபாஷ்`, `காயத்ரி`, `இந்தியா`, `சென்னை`, `அமெரிக்கா`, `சுஜாதா`, `கண்ணன்`, `குமார்`).
    17. **Oblique Pronouns (சாரியை உருபேற்ற மாற்றுப்பெயர்கள்)**: `இவற்றுள்`, `அவற்றுள்`, `எவற்றுள்`, `இவற்றை`, `அவற்றை`, `எவற்றை`, `இவற்றின்`, `அவற்றின்`, `தன்னுடன்`, `என்னுடன்`, `தன்னை`, `என்னை`, `உன்னை`, `தனக்கு`, `எனக்கு`.
    18. **Past & Future Tense Verbs**: Past finite verbs (`-த்தான்`, `-ட்டான்`, `-ந்தான்`, `-ினான்`, `-னேன்`, `-தேன்`) and Future finite verbs (`-வான்`, `-வாள்`, `-வார்`, `-பான்`).
    19. **Sandhi Fragments & Particles**: Final stop consonants (`-ப்`, `-த்`, `-க்`, `-ச்`, `-ஃ`), modal verbs (`-லாம்`), and negative participles (`-ஆமல்`).
    20. **Grantha & Non-Keyboard Characters (கிரந்த எழுத்துக்கள் & விசைப்பலகையில் இல்லாதவை)**: Excluded all words containing Grantha consonants (`ஜ`, `ஷ`, `ஸ`, `ஹ`, `க்ஷ`, `ஶ`) and characters not physically present on the in-game Tamil keyboard (e.g. `சர்வீஸ்`, `நிதிஷ்`, `பிரான்சிஸ்`, `ஜனவரி`, `ஹோட்டல்`).
- **Target Part of Speech Engine**:
  - **Base Nouns (பெயர்ச்சொற்கள்)**: Nominative stems, verbal nouns/gerunds (`-தல்`, `-மை`, `-வு`, `-கை`, `-வை`, `-பு`, `-தி`, `-சி`, `-டு`), agent/honorific nouns (`-அன்`, `-அள்`, `-அர்`, `-ஆளன்`, `-காரன்`, `-காரர்`).
  - **Simple Present Tense Verbs (நிகழ்கால வினைமுற்று & ஏவல் வினை)**: `-கிறான்`, `-கிறாள்`, `-கிறார்`, `-கிறது`, `-கிறேன்`, `-கிறோம்`, `-கின்றனர்`, `-கின்றன`, `-க்கின்றன`.
- **Morphology Unit Test Suite (`data/test_tamil_morphology.py`)**:
  - 14 comprehensive unit test suites validating grapheme clustering, case inflections, conjunctions, emphatic clitics, concessives, adjectival stems, pronouns, proper nouns, obliques, infinitives, non-keyboard characters, and target noun/verb forms (100% test pass rate).
- **Tamil Proper Nouns & Personal Names Gazetteer (`data/tamil_proper_names_gazetteer.txt`)**:
  - Ingested 830+ categorized entities covering pure-Tamil given names (Sangam, historical, literary, and modern), deities, districts, towns, states, nations, and rivers.
  - Expanded compound name suffixes (`-அழகன்`, `-அரசன்`, `-வாணன்`, `-வண்ணன்`, `-வள்ளல்`, `-செல்வன்`, `-செல்வி`, `-மலர்`, `-குமரன்`, `-பாண்டி`, `-பாண்டியன்`, `-தேவன்`, `-நாயகி`, `-வள்ளி`, `-சுந்தரி`, `-அய்யா`, `-முத்து`, `-வேலன்`, `-கார்த்தி`, `-பிரகாசம்`, `-லிங்கம்`, `-நாயகம்`, `-பிரசாத்`).
- **Agent Guidelines & Knowledge Base (`AGENTS.md` & `.agents/AGENTS.md`)**:
  - Detailed conventions covering Git execution policies, dedicated Python virtual environments, linguistic precision, dictionary filtering schemas, and verification workflows.

### Changed
- **Master Filtered Dictionary (`data/filtered_tamil_words.csv`)**:
  - Filtered from 4.59M raw frequency entries down to **205,387 pure, keyboard-typable base nouns and simple present tense verbs**.
- **Top 1,500 Frequent Words (`data/top_1500_filtered_words.csv`)**:
  - Filtered top 1,500 frequent Tamil target words across lengths 3, 4, and 5 (verified 0 non-keyboard characters and 0 gazetteer proper names).
- **Frontend Wordle Game Assets (`frontend/public/`)**:
  - `top_words.json`: `tamilMainWordList` updated with top 1,500 secret target puzzle words; `tamilEntireWordList` populated with 30,000 valid keyboard guess words.
  - `words_3.json`: Refreshed with **38,320** valid 3-letter nouns and present tense words.
  - `words_4.json`: Refreshed with **74,734** valid 4-letter nouns and present tense words.
  - `words_5.json`: Refreshed with **92,333** valid 5-letter nouns and present tense words.
