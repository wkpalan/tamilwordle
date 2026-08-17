# Tamil Wordle - Agent Guidelines & Project Rules

This document defines core conventions, execution rules, and domain-specific knowledge for AI agents working in this codebase.

---

## 1. Core Policies & Constraints

- **Command Execution Policy**:
  - Agents **MAY** run commands proactively (without asking permission) if they:
    - Modify files **within** this project directory (`/Users/kokulapalan/projects/tamilwordle/`), **OR**
    - Are **read-only / non-destructive** (e.g. inspecting files, checking classifications, running unit tests).
  - Agents **MUST NOT** run commands that modify files **outside** this project directory without explicit user approval.
- **Git Execution Policy**: 
  - Do **NOT** run `git push` automatically.
  - Do **NOT** run any `git` commands automatically unless explicitly requested by the user.
- **Python Environment**:
  - Always use the project's dedicated Python virtual environment:
    ```bash
    /Users/kokulapalan/mamba/envs/tamilwordle/bin/python
    ```
- **Language & Linguistic Precision**:
  - Tamil words must always be handled using proper Unicode grapheme clustering (`[\u0b80-\u0bff][\u0bbe-\u0bcd\u0bd7]?`).
  - Standard character lengths for Tamil Wordle refer to **grapheme / syllable count** (e.g. `மரம்` = 3 letters, `வாழ்க்கை` = 4 letters), **NOT** UTF-8 byte or raw code unit length.

---

## 2. Repository Layout & Key Paths

- **Data Pipeline**:
  - Master frequency dataset: `data/aviiciii-tamil-words-frequency.csv` (4.59M words)
  - Word filtering script: `data/filter_words_pipeline.py`
  - Morphology unit tests: `data/test_tamil_morphology.py`
  - Excluded POS specifications: `data/excluded-word-parts-of-speech.txt`
  - Filtered master dictionary: `data/filtered_tamil_words.csv`
  - Top 1,500 frequent word list: `data/top_1500_filtered_words.csv`
- **Frontend & Game Assets**:
  - `frontend/public/top_words.json`
  - `frontend/public/words_3.json`, `words_4.json`, `words_5.json`
  - `frontend/src/` (React / Next.js / Vite web application)
- **Backend**:
  - `backend/` (FastAPI / Node API if applicable)

---

## 3. Linguistic Rules & Target Parts of Speech

The Tamil Wordle word list is restricted to:
1. **Base Nouns (பெயர்ச்சொற்கள்)**: Root nouns, verbal nouns/gerunds (`-தல்`, `-மை`, `-வு`, `-கை`, `-வை`, `-பு`, `-தி`, `-சி`), agent/honorific nouns (`-அன்`, `-அள்`, `-அர்`, `-ஆளன்`, `-காரன்`), and standard nominative stems.
2. **Simple Present Tense Verbs (நிகழ்கால வினைச்சொற்கள் & ஏவல் வினை)**: Finite present tense verbs (`-கிறான்`, `-கிறாள்`, `-கிறார்`, `-கிறது`, `-கிறேன்`, `-கிறோம்`, `-கின்றனர்`, etc.) and root imperative forms.

### Excluded Parts of Speech (Must be Filtered Out)
Reference `data/excluded-word-parts-of-speech.txt`:
1. **Relative Participle (பெயரெச்சம்)**: `-கிற`, `-க்கிற`, `-கின்ற`, `-க்கின்ற` (e.g., `செய்கிற`, `படிக்கிற`, `வருகின்ற`).
2. **Derived Adjective (ஆக்கப்பெயரடை)**: Suffix `-ஆன` (`-மான`, `-யான`, `-வான`, `-ரான`, `-லான`, `-தான`, etc., e.g., `உயரமான`, `அழகான`, `முக்கியமான`).
3. **Inclusive Conjunction (எண்ணும்மை / உம்மை இடைச்சொல்)**: Conjunction `-உம்` (`\u0bc1` / `\u0bc2` phonological markers on all consonants: `-களும்`, `-யும்`, `-வும்`, `-லும்`, `-தும்`, `-றும்`, `-டும்`, `-ணும்`, `-னும்`, `-மும்`, `-ப்பும்`, e.g., `காலமும்`, `படமும்`, `பெண்ணும்`, `எதிலும்`, `அமைப்பும்`, `நாடுகளும்`).
4. **Past Relative Participle (இறந்தகாலப் பெயரெச்சம்)**: `-த்த`, `-ட்ட`, `-ந்த`, `-ற்ற`, `-ன்ற`, `-ிய`, `-ஆத` (e.g., `செய்த`, `வந்த`, `போன`, `கடந்த`, `கட்டிய`, `ஓடிய`, `பாடிய`, `பேசிய`, `எழுதிய`, `விரும்பாத`).
5. **Concessive Conditional Verb (உம்மை எச்சம் / நிபந்தனை எச்சம்)**: `-போதெல்லாம்`, `-இருந்தும்`, `-செய்தும்`, `-வந்தும்`, `-போயும்`, `-ஆயினும்`, `-ஆனாலும்`, `-போதிலும்`, `-விட்டாலும்`, `-விடினும்`, `-விடின்`.
6. **Inflected Noun (வேற்றுமை உருபேற்ற பெயர்ச்சொற்கள்)**: 2nd–7th case inflections (Accusative `-ஐ`, `-களை`, `-வரை`, `-த்தை`, Instrumental/Associative `-ஆல்`, `-உடன்`, `-த்துடன்`, `-யுடன்`, `-வுடன்`, `-ருடன்`, `-ளுடன்`, Dative `-க்கு`, `-களுக்கு`, Locative/Ablative `-இல்`, `-இன்`, `-த்தில்`, `-லிருந்து`, `-இருந்து`, Genitive `-உடைய`, `-னுடைய`).
7. **Emphatic Clitic (தேற்ற ஏகாரம் / ஓகாரம்)**: Suffixes `-ஏ` (`\u0bc7`), `-ஓ` (`\u0bcb`), `-தானே`, `-மட்டுமே`, `-போதே`, `-என்னமோ`.
8. **Adjective (பெயரடை)**: Adjectival markers `-போன்ற`, `-ஆகிய`, `-உள்ள`, `-முள்ள`, `-யுள்ள`, `-கொண்ட`, `-தக்க`, `-வாய்ந்த`, `-உடைய`, `-பொருந்திய`.
9. **Adjectival Stem (பெயரடை அடிச்சொல்)**: Bound / adjectival stems (`அதிவேக`, `கரிம`, `சமண`, `ஆதார`, `தூதரக`, `அற்புத`, `பல்லவ`, `டகம`, `அவன`, `அமர`, `நாடக`, `பயங்கர`, `உலக`, `தமிழக`, `தத்துவ`, `மாநில`, `தேசிய`, `மத்திய`).
10. **Proper Adjective (சிறப்புப் பெயரடை)**: Proper adjectival forms (`இந்திய`, `ஜெர்மன்`, `அரசிய`, `ஆசிய`).
11. **Interrogative Pronoun (வினாப் பெயர்ச்சொல் / பிரதிப்பெயர்)**: `எவர்`, `யாரு`, `எது`, `எவை`, `யாவை`, `என்ன`, `எங்கு`, `எங்கே`, `எவ்வாறு`, `எப்படி`.
12. **Past Adverbial Participle (இறந்தகால வினையெச்சம்)**: `-த்து`, `-ந்து`, `-சென்று`, `-செய்து`, `-நின்று`, `-கற்று`, `-பெற்று`, `-விட்டு`, `-போட்டு`, `-கொண்டு` (e.g., `வைத்து`, `பார்த்து`, `செய்து`, `வந்து`, `சென்று`, `நின்று`, `வரவேற்று`, `நீங்கி`, `கழுவி`, `விரட்டி`).
13. **Possessive (ஆறாம் வேற்றுமை உடைமைப் பெயர்)**: `-தனது`, `-அவரது`, `-எனது`, `-உனது`, `-அவனது`, `-அவளது`, `-தமது`, `-நமது`, `-இவரது`, `-உடைய`, `-னுடைய`.
14. **Combining Form (சேர்க்கைச் சொல் முன்னொட்டு)**: `துணை-`, `மறு-`, `நல்-`, `செம்-`, `பெரு-`, `இடை-`, `முன்-`, `பின்-`, `உள்-`, `வெளி-`, `மேல்-`, `கீழ்-`, `அதி-`, `தொல்-`.
15. **Infinitive Verb (செயவென் வினையெச்சம் / வியங்கோள் / Non-finite Infinitive)**: `-க்க`, `-க`, `-ய`, `-ல`, `-ள`, `-ப்ப`, `-ட` (e.g., `பார்க்க`, `படிக்க`, `செய்ய`, `செல்ல`, `சொல்ல`, `வாழ்க`, `அணுக`, `இயங்க`, `ஆராய`, `பெய்ய`, `கையாள`, `பரப்ப`, `நிரப்ப`, `அனுப்ப`, `கணக்கிட`, `ஏற்பட`).
16. **Proper Noun (சிறப்புப் பெயர்ச்சொற்கள்)**: ஆட்கள் பெயர்கள், நாடுகள், மாநிலங்கள், நகரங்கள், பிரபலங்கள் (e.g., `ராமசாமி`, `அசோகன்`, `அகிலன்`, `செல்லப்பா`, `அபிராமி`, `சுபாஷ்`, `காயத்ரி`, `இந்தியா`, `சென்னை`, `அமெரிக்கா`, `சுஜாதா`, `கண்ணன்`, `குமார்`).
17. **Oblique Pronoun (சாரியை உருபேற்ற மாற்றுப்பெயர்கள்)**: `இவற்றுள்`, `அவற்றுள்`, `எவற்றுள்`, `இவற்றை`, `அவற்றை`, `எவற்றை`, `இவற்றின்`, `அவற்றின்`, `தன்னுடன்`, `என்னுடன்`, `தன்னை`, `என்னை`, `உன்னை`, `தனக்கு`, `எனக்கு`.
18. **Past & Future Tense Verbs**: Past finite verbs (`-த்தான்`, `-ட்டான்`, `-ந்தான்`, `-ினான்`, `-னேன்`, `-தேன்`, `-ட்டேன்`, etc.) and Future finite verbs (`-வான்`, `-வாள்`, `-வார்`, `-பான்`, etc.).
19. **Sandhi Fragments & Participles**: Words ending in virama stop consonants (`-ப்`, `-த்`, `-க்`, `-ச்`, `-ஃ`) or trailing nasals (`-ங்`), modal verbs (`-லாம்`), and negative participles (`-ஆமல்`).
20. **Grantha & Non-Keyboard Characters (கிரந்த எழுத்துக்கள் & விசைப்பலகையில் இல்லாதவை)**: Any word containing Grantha consonants (`ஜ`, `ஷ`, `ஸ`, `ஹ`, `க்ஷ`, `ஶ`) or letters not physically present on the in-game keyboard (e.g., `சர்வீஸ்`, `நிதிஷ்`, `பிரான்சிஸ்`, `ஜனவரி`, `ஹோட்டல்`). All words must strictly be composable using the 12 independent vowels (`அ`–`ஔ`), 18 base consonants (`க`–`ன`), and the Aytham letter (`ஃ`).

---

## 4. Verification Workflow

Whenever updating dictionary filtering logic or word lists:
1. **Run Unit Tests**:
   ```bash
   /Users/kokulapalan/mamba/envs/tamilwordle/bin/python data/test_tamil_morphology.py
   ```
   Ensure all test cases pass with 0 failures.
2. **Execute Streaming Pipeline**:
   ```bash
   /Users/kokulapalan/mamba/envs/tamilwordle/bin/python data/filter_words_pipeline.py \
     --input data/aviiciii-tamil-words-frequency.csv \
     --output data/filtered_tamil_words.csv \
     --top-n 1500 \
     --top-n-output data/top_1500_filtered_words.csv \
     --lengths 3,4,5 \
     --min-freq 2 \
     --mode keep
   ```
3. **Verify Sample Outputs**: Inspect `data/top_1500_filtered_words.csv` and game JSON files in `frontend/public/` to ensure high quality and absence of inflected or non-target forms.
