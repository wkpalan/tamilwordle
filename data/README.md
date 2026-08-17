# Tamil Wordle Data Pipeline

This directory contains the data processing pipeline responsible for converting raw Tamil word frequencies into a pristine, grammatically correct dictionary suitable for a Wordle-style game.

## Pipeline Architecture

The pipeline (`run_pipeline.sh`) executes a multi-stage filtering process to extract valid 3, 4, and 5-letter base words from a raw corpus of 4.5 million entries. Because Tamil is highly agglutinative, the pipeline heavily focuses on stripping grammatical inflections.

### 1. Structural & Sanity Filtering
- **Input:** `aviiciii-tamil-words-frequency.csv` (Raw frequency list).
- **Rules:** 
  - Validates character sets (rejects English, Grantha consonants, numbers).
  - Parses words into valid Unicode Grapheme clusters to determine true visual length.
  - Filters to lengths of exactly 3, 4, or 5 graphemes.

### 2. Morphological Grammar Engine (`filter_words_pipeline.py`)
- Acts as a reverse-stemmer to reject inflected forms.
- Rejects case markers (e.g., `-ஐ`, `-ஆல்`), tense inflections, participles, infinitives, and clitics.
- Target: Base Nouns (பெயர்ச்சொற்கள்) and Simple Present Tense Verbs (நிகழ்கால வினை).

### 3. ML Named Entity Audit
- Rule-based grammar checks cannot detect semantic meaning (e.g., proper nouns like "இந்தியா" or phonetically spelled English words).
- The pipeline utilizes a neural NLP model (Stanford Stanza) to perform Named Entity Recognition (NER) on high-frequency candidates.
- Any word flagged as a Proper Noun (`PROPN`) is added to an automated blacklist.

### 4. Generation
- Outputs the master filtered list (`filtered_tamil_words.csv`) and a top-N target list (`top_1500_filtered_words.csv`).
- Generates JSON assets for the frontend.

---

## Important Configuration Files: Whitelists & Blacklists

The pipeline relies on several lists to handle edge cases, false positives, and false negatives. 

### 🚫 Blacklists (Exclusions)
These files contain words that structurally pass grammar rules but are semantically invalid for the game (e.g., names, loanwords, typos).

1. **`user_curated_excluded_words.txt`**
   - **Type:** Human-curated Blacklist.
   - **Purpose:** The absolute source of truth for manual deletions. If you see a bad word in the game, add it here.
2. **`ml_excluded_proper_nouns.txt`**
   - **Type:** Automated Blacklist (Gazetteer).
   - **Purpose:** Generated dynamically by the ML audit script. Contains proper nouns caught by the neural model.
3. **`tamil_proper_names_gazetteer.txt`**
   - **Type:** Static Blacklist.
   - **Purpose:** A legacy static list of known names and places.

### ✅ Whitelists (Protected Words)
Because the grammar engine aggressively strips suffixes (like the `-ஐ` accusative case), it can accidentally delete valid root words that happen to end in those letters (e.g., `குதிரை`, `மாலை`). Whitelists protect these valid roots.

1. **`user_curated_whitelist_words.txt`**
   - **Type:** Human-curated Whitelist.
   - **Purpose:** Protects essential, common base nouns from being accidentally flagged by the ML proper noun detector or aggressive grammar rules. If a valid word is missing or being wrongly deleted by the pipeline, add it here. The Python pipeline dynamically loads this file at runtime.

---

## How to Run

To regenerate the dictionaries and update the frontend JSON assets after modifying any blacklists or rules:

```bash
./run_pipeline.sh
```
