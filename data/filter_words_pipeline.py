#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tamil Morphological Classifier and Word Filter Pipeline
Filters Tamil words to identify nouns (பெயர்ச்சொற்கள்) and simple present tense words / root verbs (நிகழ்கால வினைச்சொற்கள் & ஏவல் வினை).
"""

import sys
import os
import re
import csv
import json
import argparse
from typing import List, Tuple, Optional, Set, Dict

# Standard Tamil Unicode regex patterns
# Matches any Tamil character block (U+0B80 - U+0BFF)
TAMIL_BLOCK_REGEX = re.compile(r"^[\u0b80-\u0bff]+$")

# Grapheme cluster regex: Base Tamil character optionally followed by vowel sign, virama, or au length mark
# Matches Uyir, Mei, Uyir-Mei, Ayudham, and Grantha characters
GRAPHEME_REGEX = re.compile(r"[\u0b80-\u0bff][\u0bbe-\u0bcd\u0bd7]?", re.IGNORECASE)

# --- Grammatical & Morphological Patterns ---

# 1. Present Tense Markers (நிகழ்கால வினைமுற்று மட்டும் - Finite verbs only)
# Weak verbs: -கிறு-, -கின்று-
# Strong verbs: -க்கிறு-, -க்கின்று-
PRESENT_TENSE_SUFFIXES = [
    # 3rd Person (படர்க்கை)
    "கிறான்", "க்கிறான்", "கின்றான்", "க்கின்றான்",      # Masculine singular
    "கிறாள்", "க்கிறாள்", "கின்றாள்", "க்கின்றாள்",      # Feminine singular
    "கிறார்", "க்கிறார்", "கின்றார்", "க்கின்றார்",      # Honorific singular
    "கிறார்கள்", "க்கிறார்கள்", "கின்றார்கள்", "க்கின்றார்கள்", # Plural
    "கின்றனர்", "க்கின்றனர்", "கின்றர்", "க்கின்றர்",     # Epicene plural
    "கிறது", "க்கிறது", "கின்றது", "க்கின்றது",          # Neuter singular
    "கின்றன", "க்கின்றன",                              # Neuter plural
    # 1st Person (தன்மை)
    "கிறேன்", "க்கிறேன்", "கின்றேன்", "க்கின்றேன்",      # 1st singular
    "கிறோம்", "க்கிறோம்", "கின்றோம்", "க்கின்றோம்",      # 1st plural
    # 2nd Person (முன்னிலை)
    "கிறாய்", "க்கிறாய்", "கின்றாய்", "க்கின்றாய்",      # 2nd singular
    "கிறீர்கள்", "க்கிறீர்கள்", "கின்றீர்கள்", "க்கின்றீர்கள்", # 2nd plural
    "கின்றீர்", "க்கின்றீர்", "கிறீர்", "க்கிறீர்",
]
PRESENT_TENSE_SUFFIXES.sort(key=len, reverse=True)

# 2. Past Tense Suffixes to Exclude (இறந்தகால வினைமுற்று & வினையெச்சம்)
PAST_TENSE_SUFFIXES = [
    # Weak/Strong past tense markers: த், ட், ற், இன், ந்த், ண்ட், ன்ற் + PNG endings
    "த்தான்", "த்தாள்", "த்தார்", "த்தார்கள்", "த்தனம்", "த்தனர்", "த்தது", "த்தன", "த்தேன்", "த்தோம்", "த்தாய்", "த்தீர்கள்", "த்தீர்",
    "ட்டான்", "ட்டாள்", "ட்டார்", "ட்டார்கள்", "ட்டனம்", "ட்டனர்", "ட்டது", "ட்டன", "ட்டேன்", "ட்டோம்", "ட்டாய்", "ட்டீர்கள்", "ட்டீர்",
    "ந்தான்", "ந்தாள்", "ந்தார்", "ந்தார்கள்", "ந்தனம்", "ந்தனர்", "ந்தது", "ந்தன", "ந்தேன்", "ந்தோம்", "ந்தாய்", "ந்தீர்கள்", "ந்தீர்",
    "ற்றான்", "ற்றாள்", "ற்றார்", "ற்றார்கள்", "ற்றனம்", "ற்றனர்", "ற்றது", "ற்றன", "ற்றேன்", "ற்றோம்", "ற்றாய்", "ற்றீர்கள்", "ற்றீர்",
    "ினான்", "ினாள்", "ினார்", "ினார்கள்", "ினம்", "ினர்", "ினது", "ின", "ினேன்", "ினோம்", "ினாய்", "ினீர்கள்", "ினீர்",
    "யான்", "யாள்", "யார்", "யார்கள்", "யது", "யன", "யேன்", "யோம்", "யாய்", "யீர்கள்", "யீர்",
    "ண்டான்", "ண்டாள்", "ண்டார்", "ண்டார்கள்", "ண்டனம்", "ண்டனர்", "ண்டது", "ண்டன", "ண்டேன்", "ண்டோம்", "ண்டாய்", "ண்டீர்கள்", "ண்டீர்",
    "ன்றான்", "ன்றாள்", "ன்றார்", "ன்றார்கள்", "ன்றனம்", "ன்றனர்", "ன்றது", "ன்றன", "ன்றேன்", "ன்றோம்", "ன்றாய்", "ன்றீர்கள்", "ன்றீர்",
    "தான்", "தாள்", "தார்", "தார்கள்", "தனம்", "தனர்", "தது", "தன", "தேன்", "தோம்", "தாய்", "தீர்கள்", "தீர்",
    # 1st person past forms (-னேன், -யேன், etc.)
    "போனேன்", "வந்தேன்", "சென்றேன்", "ஆனேன்", "கண்டேன்", "விட்டேன்", "செய்தேன்", "படித்தேன்",
    "னேன்", "யேன்", "தேன்", "த்தேன்", "ட்டேன்", "ந்தேன்", "ற்றேன்", "ண்டேன்", "ன்றேன்",
    "னோம்", "யோம்", "தோம்", "த்தோம்", "ட்டோம்", "ந்தோம்", "ற்றோம்", "ண்டோம்", "ன்றோம்",
    "னாய்", "யாய்", "தாய்", "த்தாய்", "ட்டாய்", "ந்தாய்", "ற்றாய்", "ண்டாய்", "ன்றாய்",
    # Specific past endings & forms
    "ஆனது", "ஆயிற்று", "போனது", "வந்தது", "இருந்தது", "சென்றது", "முடிந்தது", "பட்டது", "கொண்டது", "ஆனார்", "போனார்", "வந்தார்",
]
PAST_TENSE_SUFFIXES.sort(key=len, reverse=True)

# 3. Concessive Conditional Suffixes to Exclude (உம்மை எச்சம் & நிபந்தனை எச்சம்)
CONCESSIVE_CONDITIONAL_SUFFIXES = [
    "போதெல்லாம்", "இருந்தும்", "செய்தும்", "வந்தும்", "போயும்", "விடினும்", "ஆயினும்", "ஆனாலும்",
    "போதிலும்", "செய்தாலும்", "வந்தாலும்", "போனாலும்", "விட்டாலும்", "விடின்",
]
CONCESSIVE_CONDITIONAL_SUFFIXES.sort(key=len, reverse=True)

# 4. Adjectival & Adverbial Suffixes to Exclude (பெயரடை & வினையடை விகுதிகள்)
ADJECTIVE_SUFFIXES = [
    # -ஆன adjectival suffixes (18 consonants + clusters with -ஆன):
    "ட்டான", "ந்தான", "ற்றான", "க்கான", "ப்பான", "த்தான",
    "கான", "ஙான", "சான", "ஞான", "டான", "ணான", "தான", "நான", "பான", "மான",
    "யான", "ரான", "லான", "வான", "ழான", "ளான", "றான", "னான", "ஆன",
    # Adjectival markers (-உள்ள forms, -போன்ற, -ஆகிய, etc.)
    "கொண்டுள்ள", "ப்பட்டுள்ள", "வந்துள்ள", "மீதமுள்ள", "அன்புள்ள", "அறிவுள்ள",
    "ந்துள்ள", "த்துள்ள", "துள்ள", "முள்ள", "யுள்ள", "வுள்ள", "குள்ள", "சுள்ள", "உள்ள",
    "போன்ற", "ஆகிய", "கொண்ட", "தக்க", "வாய்ந்த", "உடைய", "பொருந்திய",
]
ADJECTIVE_SUFFIXES.sort(key=len, reverse=True)

ADVERB_SUFFIXES = [
    # -ஆக adverbial suffixes (18 consonants + clusters with -ஆக):
    "செய்ததாக", "வந்ததாக", "போனதாக", "பட்டதாக", "த்ததாக", "டதாக", "ந்ததாக", "வதற்காக",
    "க்காக", "ற்காக", "ட்டாக", "ந்தாக", "ற்றாக", "ப்பாக", "த்தாக",
    "காக", "ஙாக", "சாக", "ஞாக", "டாக", "ணாக", "தாக", "நாக", "பாக", "மாக",
    "யாக", "ராக", "லாக", "வாக", "ழாக", "ளாக", "றாக", "னாக", "ஆக",
]
ADVERB_SUFFIXES.sort(key=len, reverse=True)

# 5. Relative Participles to Exclude (பெயரெச்சங்கள் - நிகழ்கால & இறந்தகாலப் பெயரெச்சங்கள்)
RELATIVE_PARTICIPLE_SUFFIXES = [
    # Present relative participles
    "க்கின்ற", "கின்ற", "க்கிற", "கிற",
    # Past relative participles
    "செய்த", "படித்த", "நடந்த", "சொன்ன", "வந்த", "போன", "இருந்த", "சென்ற", "கடந்த", "அமைந்த",
    "பிறந்த", "சேர்ந்த", "வளர்ந்த", "முடிந்த", "சிறந்த", "கண்ட", "விட்ட", "தொட்ட", "இட்ட",
    "சுட்ட", "கேட்ட", "பெற்ற", "உற்ற", "விற்ற", "நின்ற", "வென்ற", "பட்ட", "தந்த", "கற்ற",
    "எடுத்த", "பார்த்த", "கொடுத்த", "வைத்த", "எழுதிய", "பாடிய", "ஓடிய", "பேசிய", "வாங்கிய",
    "சொல்லிய", "கூறிய", "ஆக்கிய", "மாற்றிய", "காட்டிய", "நேர்ந்த",
]
RELATIVE_PARTICIPLE_SUFFIXES.sort(key=len, reverse=True)

# Sandhi trailing consonants that cannot end a valid standalone Tamil word
INVALID_FINAL_CONSONANTS = {"க்", "ச்", "ட்", "த்", "ப்", "ற்", "ஃ", "ங்", "ந்"}

# 5. Future Tense Suffixes to Exclude (எதிர்கால வினைமுற்று)
FUTURE_TENSE_SUFFIXES = [
    "ப்பான்", "ப்பாள்", "ப்பார்", "ப்பார்கள்", "ப்பேன்", "ப்போம்", "ப்பாய்", "ப்பீர்கள்", "ப்பீர்", "ப்பார்", "ப்பர்",
    "வான்", "வாள்", "வார்", "வார்கள்", "வேன்", "வோம்", "வாய்", "வீர்கள்", "வீர்",
    "பான்", "பாள்", "பார்", "பார்கள்", "போம்",
]
FUTURE_TENSE_SUFFIXES.sort(key=len, reverse=True)

# Specific exempt nouns that might end in sequences looking like verb/future suffixes (e.g. -வர், -வார்)
KNOWN_BASE_NOUNS = {
    "தலைவர்", "மாணவர்", "ஆசிரியர்", "மருத்துவர்", "பேராசிரியர்", "அமைச்சர்", "முதல்வர்", "கவிஞர்",
    "அறிஞர்", "கலைஞர்", "நடிகர்", "எழுத்தாளர்", "படைப்பாளி", "விவசாயி", "ஊழியர்", "நண்பர்", "பெரியவர்",
    "சிறியவர்", "முதியவர்", "இளைஞர்", "மனிதர்", "தேவர்", "முனிவர்", "கடவுள்", "இயற்கை",
    "கதை", "விலை", "அலை", "மழை", "நிலை", "தவளை", "குதிரை", "பாவை", "வாழ்க்கை", "செய்கை",
    "பார்வை", "நம்பிக்கை", "படுக்கை", "வகை", "தொகை", "சுவை", "புகை", "பகை", "இறை",
    "தவம்", "மரம்", "சிங்கம்", "குழுமம்", "மந்திரம்", "சிஸ்டம்", "சட்டம்", "பட்டம்", "வட்டம்",
    "முத்து", "சொத்து", "சத்து", "வித்து", "பித்து",
    "பந்து", "மருந்து", "விருந்து", "சிந்து", "முந்து",
    "பாட்டு", "கூட்டு", "மூட்டு", "கோட்டு", "பூட்டு", "காட்டு", "போர்டு",
    "காற்று", "ஊற்று", "மாற்று", "சேற்று", "ஆற்று",
    "கன்று", "குன்று",
    "வண்டு", "துண்டு", "பண்டு", "பூண்டு", "சூரியன்", "சந்திரன்", "பூமி",
}


# Numerals and Ordinals to Exclude (எண்ணுப்பெயர்கள் மற்றும் வரிசைப்பெயர்கள்)
EXCLUDED_NUMERALS_AND_ORDINALS = {
    "ஒன்று", "இரண்டு", "மூன்று", "நான்கு", "ஐந்து", "ஆறு", "ஏழு", "எட்டு", "ஒன்பது", "பத்து",
    "இருபது", "முப்பது", "நாற்பது", "ஐம்பது", "அறுபது", "எழுபது", "எண்பது", "தொண்ணூறு", "நூறு",
    "ஆயிரம்", "லட்சம்", "கோடி", "பில்லியன்", "மில்லியன்",
    "முதலாம்", "இரண்டாம்", "மூன்றாம்", "நான்காம்", "ஐந்தாம்", "ஆறாம்", "ஏழாம்", "எட்டாம்", "ஒன்பதாம்", "பத்தாம்",
    "முதலாவது", "இரண்டாவது", "மூன்றாவது", "நான்காவது", "ஐந்தாவது", "ஆறாவது", "ஏழாவது", "எட்டாவது", "ஒன்பதாவது", "பத்தாவது",
    "ஒன்னு", "ரெண்டு", "ஒண்ணு", "இலட்சம்", "பதினாறு", "பதினெட்டு", "இருபதாம்", "ஒன்பதாம்", "ஐந்தாம்", "எட்டாம்",
    "ஏழாம்", "ஆறாம்",
}

# Adverbs, Discourse Markers & Non-Target Forms to Exclude (வினையெச்சங்கள் / இடைச்சொற்கள்)
EXCLUDED_ADVERBS_AND_DISCOURSE = {
    "முதல்", "இன்று", "அன்று", "என்று", "நேற்று", "முன்னர்", "இப்போது", "அப்போது", "எப்போது", "நாளை", "பிறகு", "பின்னர்", "முன்பு", "முன்னாள்", "முன்னாடி", "பிற்பாடு", "பின்பு", "பின்னாடி", "இனிமேல்", "அப்புறம்",
    "திடீர்", "திடீரென", "திடீரென்று", "சட்டென", "சட்டென்று", "நேற்றிரவு", "இன்றைய", "நேற்றைய", "நாளைய", "முந்தைய", "முதல்தர", "அன்றைய", "அன்றாட", "அன்றாடம்", "அப்போதைய", "இப்போதைய", "தற்போதைய",
    "அதிகம்", "கொஞ்சம்", "சற்று", "ரொம்ப", "நிறைய", "மிகவும்", "சுமார்", "ஏறத்தாழ", "ஓரளவு", "சிறிதளவு", "அதிகளவு", "ஏராளம்", "நல்லது", "சிறிது", "நீண்ட", "தவிர", "அல்ல", "அல்லவா", "இல்ல", "இல்லா", "உண்டு", "நன்கு", "மெல்ல", "சீக்கிரம்", "எளிது", "அரிது", "புதுசா", "அழகாய்", "தப்பா", "கண்டிப்பா", "தவறு", "சும்மா", "நல்லா", "நேரடி", "உள்பட", "இதையொட்டி", "இதுபற்றி", "இதுதவிர", "இதுபோல்", "இதுபோல", "இதுபோன்று", "அதேபோல்", "அதேபோல", "அதேபோன்று", "போன்று", "போன்ற", "போன்றவை", "போன்றோர்", "அதேநேரம்", "இதேபோல்", "இதேபோல", "இதேவேளை", "அதேவேளை", "ஒருவேளை", "என்றவாறு", "ஏற்றவாறு", "வருமாறு", "தருமாறு", "செய்யுமாறு", "நன்றி", "என்பதை", "என்பதன்", "என்பவன்", "என்பதோடு", "என்பது", "வேண்டாம்", "வராது", "ஆகாது", "செல்லாது", "கிடைக்காது", "நடக்காது", "இருக்காது", "பிடிக்காது", "ஏற்படாது", "முடியாது", "தெரியாது", "கூடாது",
    "தாண்டி", "திரும்ப", "அவளை", "எமது", "உமது", "அவரது", "தங்களது", "உங்களது", "எங்களது", "நம்முடைய", "தம்முடைய", "அவருடைய", "இவருடைய", "யாருடைய", "ஒருவரது", "இவனது",
}


def load_user_curated_whitelist() -> Set[str]:
    """Load user curated protected base nouns and allowed words."""
    words = set()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    whitelist_path = os.path.join(script_dir, "user_curated_whitelist_words.txt")
    if os.path.exists(whitelist_path):
        with open(whitelist_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    words.add(line)
    return words

USER_CURATED_WHITELIST = load_user_curated_whitelist()

VALID_REFERENCE_WORDS: Set[str] = set()

def load_valid_reference_words(input_csv_path: str, min_freq: int = 1):
    """Pre-scan the corpus to identify valid reference words ending in 'ம்' or 'து'."""
    global VALID_REFERENCE_WORDS
    if not os.path.exists(input_csv_path):
        return
    with open(input_csv_path, mode="r", encoding="utf-8") as fin:
        reader = csv.reader(fin)
        next(reader, None)
        for row in reader:
            if row and len(row) >= 2:
                word = row[0].strip()
                if word.endswith("ம்") or word.endswith("து") or word.endswith("ன்") or word.endswith("ள்"):
                    try:
                        if int(row[1].strip()) >= min_freq:
                            VALID_REFERENCE_WORDS.add(word)
                    except ValueError:
                        pass

# Pronouns to exclude (பிரதிப்பெயர்ச்சொற்கள்)
EXCLUDED_PRONOUNS = {
    "அவள்", "அவன்", "அவர்", "அவர்கள்", "நீங்கள்", "உங்கள்", "நாங்கள்", "எங்கள்",
    "இவர்", "இவர்கள்", "இவர்க", "எவர்", "எவர்கள்", "யார்", "யாரு", "எது", "எவை", "யாவை",
    "இதன்", "அதன்", "எதன்", "இதற்கு", "அதற்கு", "இதனை", "அதனை", "இதை", "அதை", "எதை",
    "இங்கு", "அங்கு", "எங்கு", "இங்கே", "அங்கே", "எங்கே", "என்ன", "எவ்வாறு", "எப்படி",
    "அவ்வாறு", "இவ்வாறு", "அப்படி", "இப்படி",
}

# Possessive pronouns (உடைமைப் பெயர்கள்)
POSSESSIVE_SUFFIXES = [
    "த்தினுடைய", "னுடைய", "த்துடைய", "உடைய", "யுடைய", "வுடைய",
    "தனது", "அவரது", "எனது", "உனது", "அவனது", "அவளது", "தமது", "நமது", "இவரது",
]
POSSESSIVE_SUFFIXES.sort(key=len, reverse=True)

# Proper Nouns to exclude (சிறப்புப் பெயர்ச்சொற்கள் - மக்கள் பெயர்கள், இடப்பெயர்கள், நாடுகள்)
EXCLUDED_PROPER_NOUNS = {
    # Countries, States, Cities
    "இந்தியா", "அமெரிக்கா", "சீனா", "ரஷ்யா", "பாகிஸ்தான்", "இலங்கை", "சென்னை", "டெல்லி", "மும்பை",
    "கொல்கத்தா", "பெங்களூரு", "ஹைதராபாத்", "மதுரை", "கோவை", "திருச்சி", "சேலம்", "ஈரோடு", "தஞ்சாவூர்",
    "திருநெல்வேலி", "கேரளா", "கர்நாடகா", "ஆந்திரா", "தெலுங்கானா", "மகாராஷ்டிரா", "குஜராத்", "பஞ்சாப்",
    "ஒடிசா", "பீகார்", "அசாம்", "ஐரோப்பா", "ஆசியா", "ஆப்பிரிக்கா", "ஆஸ்திரேலியா", "ஜெர்மனி", "ஜெர்மன்",
    "பிரான்ஸ்", "பிரிட்டன்", "லண்டன்", "டோக்கியோ", "சிங்கப்பூர்", "மலேசியா", "துபாய்", "சவூதி", "குவைத்",
    "கத்தார்", "பஹ்ரைன்", "ஜப்பான்", "கனடா", "பிரேசில்", "மெக்ஸிகோ", "இத்தாலி", "ஸ்பெயின்",
    # Celebrities, historical figures, politicians, names
    "ராமசாமி", "அசோகன்", "நெடுஞ்செழியன்", "செழியன்", "அகிலன்", "செல்லப்பா", "அபிராமி", "ராதிகா", "சுபாஷ்", "காயத்ரி", "முருகதாஸ்",
    "பாகுபலி", "கோபால்", "ஜடேஜா", "நாசர்", "லெனின்", "ஸ்டாலின்", "சிவகாமி", "இராமன்", "மனோகர்",
    "பானர்ஜி", "சாஸ்திரி", "ரஜினிகாந்த்", "கமலாஹாசன்", "விஜயகாந்த்", "சிவாஜி", "எம்ஜிஆர்", "கருணாநிதி",
    "ஜெயலலிதா", "காந்தி", "நேரு", "அம்பேத்கர்", "பெரியார்", "பாரதியார்", "பாரதிதாசன்", "கண்ணதாசன்",
    "வாலி", "வைரமுத்து", "இளையராஜா", "ரகுமான்", "மோடி", "ராகுல்", "விஜய்", "அஜித்", "சூர்யா",
    "விக்ரம்", "தனுஷ்", "சிம்பு", "கமல்", "ரஜினி", "ஜெயம்", "கபிலன்", "கம்பர்", "வள்ளுவர்", "இளங்கோ",
    "ஔவையார்", "ஔவை", "மாணிக்கவாசகர்", "சுந்தரர்", "அப்பர்", "சம்பந்தர்", "கரிகாலன்", "செங்குட்டுவன்", "வானதி", "குந்தவை", "பூங்குழலி", "கதிர்வேல்", "முத்துச்செல்வன்", "அருண்மொழி", "கன்னியாகுமரி", "கோயம்புத்தூர்", "தாமிரபரணி", "அனுராதா", "சடகோபன்", "ரமணன்", "அனுத்தமா", "நடேசன்",
    "சுஜாதா", "கண்ணன்", "குமார்", "கிருஷ்ணன்", "முருகன்", "கணேசன்", "கார்த்திக்", "சுரேஷ்", "தினேஷ்",
    "ரமேஷ்", "அருண்", "பிரபு", "மகேஷ்", "சதீஷ்", "விவேக்", "சந்தானம்", "வடிவேலு", "சிவா", "பாலா",
    "சங்கர்", "மணி", "ராஜா", "ரவி", "பாபு", "பிரகாஷ்", "செல்வம்", "முருகா",
    "சஞ்சய்", "அஜய்", "விஜய்", "ராகவ்", "சஞ்சீவ்", "ராஜீவ்", "ரஞ்சனி", "சுசித்ரா", "சந்திரா",
}


def load_gazetteer_proper_nouns() -> Set[str]:
    """Load proper names and geographic entities from gazetteer files."""
    names = set()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for fname in ("tamil_proper_names_gazetteer.txt", "ml_excluded_proper_nouns.txt", "user_curated_excluded_words.txt"):
        gazetteer_path = os.path.join(script_dir, fname)
        gazetteer_path = os.path.join(script_dir, fname)
        if os.path.exists(gazetteer_path):
            with open(gazetteer_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        names.add(line)
    names.difference_update(USER_CURATED_WHITELIST)
    return names

# Load and merge all gazetteer entities into proper nouns set
EXCLUDED_PROPER_NOUNS.update(load_gazetteer_proper_nouns())


# Proper Name Suffixes (ஆட்கள் பெயர்கள் விகுதிகள்)
PROPER_NAME_SUFFIXES = [
    "மூர்த்தி", "ஆனந்தன்", "ஆனந்தா", "நாதன்", "ராஜன்", "ராசன்", "ராஜா", "சாமி", "அப்பன்", "அப்பா",
    "அம்மாள்", "அம்மன்", "தேவி", "குமார்", "குமரன்", "சேகர்", "சேகரன்", "சந்திரன்", "சந்தர்",
    "சுந்தரம்", "சுந்தரி", "ராஜ்", "அழகன்", "ழகன்", "அரசன்", "வாணன்", "வண்ணன்", "வள்ளல்", "செல்வன்",
    "செல்வி", "மலர்", "பாண்டி", "பாண்டியன்", "தேவன்", "நாயகி", "வள்ளி", "அய்யா", "முத்து",
    "வேலன்", "கார்த்தி", "பிரகாசம்", "லிங்கம்", "நாயகம்", "பிரசாத்",
    "கோபன்", "ரமணன்", "த்தமா", "உத்தமா", "ேசன்", "ஏசன்", "ஈசன்", "வாசன்", "நிவாசன்",
    "தாசன்", "காந்தன்", "பாலன்", "ராமன்", "வர்மன்", "கோசலா", "வேல்", "கோபால்", "மோகன்",
    "கிருஷ்ணன்", "நாராயணன்", "சித்ரா", "த்ரா",
]
PROPER_NAME_SUFFIXES.sort(key=len, reverse=True)

# Acronyms and transliterated initialisms (சுருக்கக் குறியீடுகள்)
EXCLUDED_ACRONYMS = {
    "ஐஐடி", "ஐபிஎல்", "சிபிஐ", "பிசிசிஐ", "சிசிடிவி", "டிடிவி", "ஐசிசி", "சிபிசிஐடி", "எம்எல்ஏ", "எம்பி", "டிடி", "ஏடிஎம்", "ஐபோன்"
}

# Oblique Pronouns & Inflected Pronouns (மாற்றுப்பெயரின் உருபேற்ற வடிவங்கள்)
EXCLUDED_OBLIQUE_PRONOUNS = {
    "இவற்றுள்", "அவற்றுள்", "எவற்றுள்", "இவற்றை", "அவற்றை", "எவற்றை", "இவற்றின்", "அவற்றின்", "எவற்றின்",
    "இவற்றுக்கு", "அவற்றுக்கு", "எவற்றுக்கு", "இவற்றால்", "அவற்றால்", "எவற்றால்",
    "தன்னுடன்", "என்னுடன்", "உன்னுடன்", "அவருடன்", "இவருடன்", "எவருடன்",
    "தன்னை", "என்னை", "உன்னை", "தம்மை", "நம்மை", "எம்மை",
    "தன்னால்", "என்னால்", "உன்னால்", "தம்மால்", "நம்மால்", "எம்மால்",
    "தனக்கு", "எனக்கு", "உனக்கு", "தமக்கு", "நமக்கு", "எமக்கு",
    "தன்னிடம்", "என்னிடம்", "உன்னிடம்", "தம்மிடம்", "நம்மிடம்", "எம்மிடம்",
    "தன்னைவிட", "என்னைவிட", "உன்னைவிட",
}

# Combining Forms (சேர்க்கைச் சொல் முன்னொட்டு / அடைமொழிகள்)
EXCLUDED_COMBINING_FORMS = {
    "துணை", "மறு", "நல்", "செம்", "பெரு", "இடை", "முன்", "பின்", "உள்", "வெளி",
    "மேல்", "கீழ்", "அதி", "தொல்",
}

# Standalone Adjectives & Adjectival Stems (பெயரடை & பெயரடை அடிச்சொல்)
EXCLUDED_ADJECTIVES = {
    "பல்வேறு", "ஒவ்வொரு", "அனைத்து", "அதிக", "சமூக", "அதிவேக", "கரிம", "சமண", "ஆதார",
    "தூதரக", "அற்புத", "பல்லவ", "டகம", "அவன", "அமர", "நாடக", "பயங்கர", "ஒருசில",
    "சில", "பல", "பெரும்", "புதிய", "பழைய", "இனிய", "நல்ல", "பெரிய", "சிறிய", "முக்கிய",
    "மாநில", "தேசிய", "மத்திய", "பொருளாதார", "கலாச்சார", "வர்த்தக", "துறைமுக", "புகைப்பட",
    "தினவார", "அனைத்து", "அனைவரும்", "யாருக்கும்", "யாரும்", "ஒவ்வொரு",
    "உலக", "தமிழக", "தத்துவ", "அரசிய", "ஆசிய", "இயற்க", "கர்நாடக", "கேரள", "ஆந்திர", "தெலுங்கான",
    "மகாராஷ்டிர", "அமெரிக்க", "இந்திய", "வங்காள", "ஐரோப்பிய", "ஆப்பிரிக்க",
    "இணைய", "ராணுவ", "ஊரக", "இணையதள", "கிராம", "பிரபல", "சாதாரண", "மருத்துவ", "பன்னாட்டு",
    "உச்ச", "சின்ன", "அரச", "நகர", "சட்ட", "மனித", "குடும்ப", "புத்தக", "நாட்டு",
    "உத்தம", "பரத", "ஆத்ம", "இருதய", "கனரக", "சொற்ப", "உயர்தர", "முன்னைய", "பற்பல",
    "எல்லா", "சாசன", "தடகள", "ஆடம்பர", "மனிதநேய", "குழும", "தனிமனித", "பொதுநல", "இலக்கண", "சமகால", "பணக்கார", "தன்னார்வ", "மாநில", "மாவட்ட", "வட்டார", "மண்டல", "உள்ளாட்சி",
    "வெண்ணிற", "அசைவ", "சைவ", "கிரக", "பணியிட", "நிர்ணய", "சாந்த", "சமரச", "சம்பவ", "வியாபார",
    "அலங்கார", "கலாசார", "மனிதவள", "இராணுவ", "சாத்திய", "பிரதான", "முக்கிய", "துரித", "ரகசிய",
    "அபூர்வ", "மங்கள", "சம்பிரதாய", "பழங்கால", "நீண்டகால", "குறுகியகால", "சமீபகால", "எதிர்கால",
    "வருங்கால", "இடைக்கால", "அசாதாரண", "விநியோக", "சாதக", "பாதக", "செயலக", "சுந்தர", "திரைப்பட", "மற்றைய", "பின்னைய", "நேற்றைய", "நாணய", "கோபுர", "மவுன", "பாசிச", "கவன", "சாகச",
}

# Corrupted OCR Fragments & Spoken Slang Forms (பிழைத்துண்டுகள் & பேச்சு வழக்குகள்)
EXCLUDED_FRAGMENTS_AND_SPOKEN = {
    "அதற", "புள்ள", "ஏண்டா", "விட்டுட்டு", "பண்ணிட்டு", "களால்", "றனர்", "ளனர்", "படம", "ஐயர",
    "சொல்லிட்டு", "பார்த்துட்டு", "வந்துட்டு", "செஞ்சுட்டு", "போயிட்டு", "வெச்சு", "வச்சு",
    "சொன்னா", "பார்த்தா", "வந்தா", "போனா", "இருந்தா", "இல்லாம", "அதனால", "இதனால", "எதனால",
    "என்னா", "ஏன்னா", "சொன்னாங்க", "பண்ணுங்க", "சொல்லுங்க", "பாருங்க", "வீட்ல", "ஊர்ல", "தெரியல", "முடியல", "தெரியாம", "சொல்ற", "சொல்றேன்", "சொல்லு", "பண்ற", "பண்றது", "வர்ற", "போகுது", "வருது", "இருக்குது", "இருக்குற", "வயசுல", "மனசுல", "படத்துல", "வீட்டுல", "முதல்ல", "கண்டிப்பா",
}

# Conjunctions, Adverbs & Postpositions (இடைச்சொற்கள் / வினையடைகள்)
EXCLUDED_CONJUNCTIONS_AND_POSTPOSITIONS = {
    "அல்லது", "என்பது", "பற்றி", "குறித்து", "பொழுது", "போது", "எனவே", "ஆகவே", "ஆனால்",
    "என்று", "ஆகிய", "போன்ற", "கொண்டு", "விட்டு", "போட்டு", "உள்ளது",
}

# Negative finite verbs (எதிர்மறை வினைமுற்று)
NEGATIVE_MODAL_VERBS = {
    "முடியாது", "கூடாது", "தெரியாது", "புரியாது", "கிடையாது", "இல்லாது", "போதாது", "வாராது",
    "முடியாத", "கூடாத", "தெரியாத", "புரியாத", "இல்லாத", "முடியாதா", "தெரியாதா", "இருக்காதா", "கிடைக்காதா", "கூடாதா", "வேண்டாமா", "போதுமா", "வருமா", "முடியுமா",
}

# 6. Case Markers / Inflectional Endings to Exclude (வேற்றுமை உருபுகள்)
CASE_SUFFIXES = [
    # 6th Genitive
    "த்தினுடைய", "னுடைய", "த்துடைய", "உடைய", "யுடைய", "வுடைய",
    # 3rd Instrumental / Associative (-ஆல் and -உடன் variations)
    "த்தினால்", "த்தோடு", "த்துடன்", "ந்துடன்", "யுடன்", "வுடன்", "ருடன்", "ளுடன்", "னுடன்", "துடன்", "புடன்", "குடன்", "சுடன்", "முடன்", "ழுடன்", "லுடன்", "உடன்", "யோடு", "வோடு", "நோக்கி",
    "த்தால்", "தால்", "யால்", "வால்", "ரால்", "லால்", "ளால்", "ழால்", "றால்", "னால்",
    # 7th Locative
    "த்திலிருந்து", "லிருந்து", "இருந்து", "த்திடம்", "யிடம்", "விடம்", "னிடம்", "ரிடம்", "இடம்",
    # 4th Dative
    "த்துக்கு", "களுக்கு", "ளுக்கு", "க்குரிய", "உக்கு", "வுக்கு", "யுக்கு", "இற்கு", "ற்கு", "க்கு",
    # 5th Locative/Ablative (All consonant variations with -இல் and -இன்)
    "த்தில்", "ந்தில்", "ட்டில்", "ற்றில்", "ண்டில்", "ன்றில்", "கில்", "சில்", "டில்", "தில்", "பில்", "மில்",
    "யில்", "ரில்", "லில்", "வில்", "ழில்", "ளில்", "றில்", "னில்", "இல்",
    "த்தின்", "ந்தின்", "ட்டின்", "ற்றின்", "ண்டின்", "ன்றின்", "கின்", "சின்", "டின்", "தின்", "பின்", "மின்",
    "யின்", "ரின்", "லின்", "வின்", "ழின்", "ளின்", "றின்", "னின்", "இன்",
    # 2nd Accusative
    "த்தினை", "ங்களை", "களை", "த்தை",
]
CASE_SUFFIXES.sort(key=len, reverse=True)


# 7. Verbal Participles, Infinitives & Conditionals to Exclude (வினையெச்சங்கள் / இடைச்சொற்கள்)
PARTICIPLE_CONDITION_SUFFIXES = [
    # Infinitives (-க்க, -க, -ய, -ல)
    "பார்க்க", "செய்க", "இருக்க", "நடக்க", "எடுக்க", "கொடுக்க", "அழைக்க", "திறக்க", "படிக்க",
    "சிந்திக்க", "மீட்க", "கூட்ட", "ஆக்க", "நோக்க", "இயங்க", "ஆராய", "செய்ய", "செல்ல",
    # Habitual verbs / Participial (-க்கும், -கும்)
    "வாசிக்கும்", "குறைக்கும்", "பார்க்கும்", "இருக்கும்", "நடக்கும்", "போகும்", "செய்யும்", "எதற்கும்",
    # Verbal participles (-செய்து, -செய்தால், etc.)
    "செய்து", "செய்தால்", "செய்ததும்", "செய்கையில்",
    "விட்டால்", "ஆனால்", "என்றால்", "பொழுது", "போது",
    "படி", "தோறும்", "மட்டும்",
]
PARTICIPLE_CONDITION_SUFFIXES.sort(key=len, reverse=True)
# 8. Verbal Noun / Nominalizer Suffixes (தொழிற்பெயர் & பெயர்ச்சொல் விகுதிகள்)
NOUN_NOMINAL_SUFFIXES = [
    "வாழ்க்கை", "செய்கை", "பார்வை",
    "த்தல்", "தல்", "அல்", "மை", "வு", "கை", "வை", "பு", "தி", "சி", "டு",
    "அகம்", "ஆளன்", "ஆளி", "காரன்", "காரி", "காரர்", "சாலி",
    "அரசன்", "அரசி", "மாணவன்", "மாணவி",
]
NOUN_NOMINAL_SUFFIXES.sort(key=len, reverse=True)

# Accusative vowel sign check: ends with ai vowel sign (ை)
ACCUSATIVE_AI = "\u0bc8"
EMPHATIC_EE = "\u0bc7"
EMPHATIC_OO = "\u0bcb"


# In-Game Keyboard Supported Characters
KEYBOARD_VOWELS = set("அஆஇஈஉஊஎஏஐஒஓஔ")
KEYBOARD_CONSONANTS = set("கஙசஞடணதநபமயரலவழளறன")
KEYBOARD_SPECIAL = {"ஃ"}
KEYBOARD_SIGNS = set("\u0bbe\u0bbf\u0bc0\u0bc1\u0bc2\u0bc6\u0bc7\u0bc8\u0bca\u0bcb\u0bcc\u0bcd\u0bd7")


def is_keyboard_supported(word: str, graphemes: Optional[List[str]] = None) -> bool:
    """
    Checks if all constituent letters of the Tamil word can be typed on the in-game keyboard.
    Excludes Grantha characters (ஜ, ஷ, ஸ, ஹ, க்ஷ, ஶ) and unsupported code points.
    """
    if graphemes is None:
        graphemes = get_tamil_graphemes(word)
    if not graphemes or "".join(graphemes) != word:
        return False
    for g in graphemes:
        if g in KEYBOARD_VOWELS or g in KEYBOARD_SPECIAL:
            continue
        base = g[0]
        if base not in KEYBOARD_CONSONANTS:
            return False
        if len(g) > 1 and g[1] not in KEYBOARD_SIGNS:
            return False
    return True


def get_tamil_graphemes(word: str) -> List[str]:
    """
    Split a Tamil word into a list of constituent graphemes (letters).
    Returns empty list if the word contains non-Tamil characters.
    """
    if not isinstance(word, str):
        return []
    word = word.strip()
    if not word or not TAMIL_BLOCK_REGEX.match(word):
        return []
    return GRAPHEME_REGEX.findall(word)


def classify_tamil_word(word: str, graphemes: Optional[List[str]] = None) -> Tuple[str, str]:
    """
    Classifies a Tamil word into a linguistic category.
    Returns: (category, tag_detail)
    """
    if graphemes is None:
        graphemes = get_tamil_graphemes(word)
    
    num_letters = len(graphemes)
    if num_letters == 0:
        return "EXCLUDED_OTHER", "INVALID_TAMIL"

    # Reject words containing characters not supported on the in-game keyboard (e.g. Grantha: ஜ, ஷ, ஸ, ஹ)
    if not is_keyboard_supported(word, graphemes):
        return "EXCLUDED_OTHER", "UNSUPPORTED_KEYBOARD_CHARACTERS"

    # Reject corrupted OCR fragments, spoken slang forms, and broken sandhi tokens
    if word in EXCLUDED_ACRONYMS:
        return "EXCLUDED_OTHER", "ACRONYM_ABBREVIATION"

    if word in EXCLUDED_FRAGMENTS_AND_SPOKEN:
        return "EXCLUDED_OTHER", "CORRUPTED_FRAGMENT_OR_SPOKEN"

    # Reject words ending with invalid final consonants (sandhi joiners like -ப், -த், -க், -ச்)
    if graphemes[-1] in INVALID_FINAL_CONSONANTS:
        return "EXCLUDED_OTHER", f"SANDHI_FINAL_{graphemes[-1]}"

    # 1. Unconditionally exclude Numerals & Ordinals
    if word in EXCLUDED_NUMERALS_AND_ORDINALS:
        return "EXCLUDED_OTHER", "NUMERAL_OR_ORDINAL"

    # 2. Unconditionally exclude Adverbs, Discourse markers & particles
    if word in EXCLUDED_ADVERBS_AND_DISCOURSE:
        return "EXCLUDED_OTHER", "ADVERB_OR_DISCOURSE_MARKER"

    # 3. Unconditionally exclude Proper Nouns & entities
    if word in EXCLUDED_PROPER_NOUNS:
        return "EXCLUDED_OTHER", "PROPER_NOUN"

    # 4. Unconditionally exclude Pronouns
    if word in EXCLUDED_PRONOUNS:
        return "EXCLUDED_OTHER", "PRONOUN"

    # Known base / exempt nouns
    if word in KNOWN_BASE_NOUNS:
        return "NOUN", "KNOWN_BASE_NOUN"

    if num_letters >= 4:
        for suffix in PROPER_NAME_SUFFIXES:
            suffix_graphemes = get_tamil_graphemes(suffix)
            if word.endswith(suffix) and num_letters > len(suffix_graphemes):
                return "EXCLUDED_OTHER", f"PROPER_NOUN_{suffix}"

    # Oblique Pronouns & Inflected Pronouns (மாற்றுப்பெயரின் உருபேற்ற வடிவங்கள்) -> EXCLUDE
    if word in EXCLUDED_OBLIQUE_PRONOUNS:
        return "EXCLUDED_CASE", "OBLIQUE_PRONOUN"

    # Combining Forms (சேர்க்கைச் சொல் முன்னொட்டு) -> EXCLUDE
    if word in EXCLUDED_COMBINING_FORMS:
        return "EXCLUDED_PARTICIPLE", "COMBINING_FORM"

    # Non-finite Infinitive verbs (செயவென் வினையெச்சம் / வியங்கோள் - e.g. பரப்ப, நிரப்ப, அனுப்ப, கணக்கிட, ஏற்பட, கேட்க, பார்க்க, வாங்க, தொடங்க, வழங்க, சொல்ல, செய்ய) -> EXCLUDE
    if num_letters >= 3 and word not in KNOWN_BASE_NOUNS:
        if word.endswith((
            "கேட்க", "பார்க்க", "வாங்க", "தொடங்க", "வழங்க", "நடக்க", "இருக்க", "செய்க", "சொல்ல", "வெல்ல", "செய்ய",
            "அடைய", "பெற", "உணர", "இயங்க", "ஆராய", "காட்டி", "திரும்பி", "நோக்க", "பரப்ப", "நிரப்ப", "அனுப்ப",
            "கணக்கிட", "ஏற்பட", "வெளிப்பட", "பயன்பட", "உட்பட", "முன்னிட", "வளர்க்க", "தடுக்க", "கொடுக்க", "எடுக்க",
            "மறுக்க", "பிரிக்க", "கையாள", "செல்ல", "முற்பட", "நிலைநாட்ட", "உருவாக்க", "அறிவிக்க", "வெளியிட",
            "திருப்ப", "விளங்க", "தூங்க", "உறங்க", "முயல", "விரும்ப", "கற்க", "நிற்க", "கொல்ல", "வழிபட", "செயல்பட", "சாப்பிட"
        )):
            return "EXCLUDED_PARTICIPLE", "INFINITIVE_VERB"

    # Colloquial past relative participles (e.g. படிச்ச, பிடிச்ச, அடிச்ச, முடிச்ச, செஞ்ச, தெரிஞ்ச, முடிஞ்ச, வச்ச) -> EXCLUDE
    if num_letters >= 3 and word not in KNOWN_BASE_NOUNS:
        if word.endswith(("டிச்ச", "ளிச்ச", "ரிச்ச", "ழிச்ச", "திச்ச", "சிச்ச", "கிச்ச", "விச்ச", "ணிச்ச", "னிச்ச", "மிச்ச", "யிச்ச", "வச்ச", "செஞ்ச", "தெரிஞ்ச", "முடிஞ்ச", "நடஞ்ச", "அமைஞ்ச", "விழுஞ்ச")):
            return "EXCLUDED_PAST", "COLLOQUIAL_RELATIVE_PARTICIPLE"

    # Negative compound predicates ending in -அல்ல (e.g. சரியல்ல, உண்மையல்ல, புதிதல்ல, ஒன்றல்ல, கதையல்ல, தவறல்ல, பொய்யல்ல) -> EXCLUDE
    if num_letters >= 3 and word.endswith("அல்ல") and word not in KNOWN_BASE_NOUNS:
        return "EXCLUDED_OTHER", "NEGATIVE_PREDICATE_அல்ல"

    # Temporal & Demonstrative Adjectives in -ஐய / -ய (e.g. மற்றைய, முன்னைய, பின்னைய, நேற்றைய, இன்றைய, நாளைய) -> EXCLUDE
    if word in {"மற்றைய", "முன்னைய", "பின்னைய", "நேற்றைய", "இன்றைய", "நாளைய"}:
        return "EXCLUDED_OTHER", "TEMPORAL_DEMONSTRATIVE_ADJECTIVE"

    # Bound adjectival compound stems derived from -ம் nouns (e.g. இணையதள, குறுநில, புதுமுக, வம்ச, பாசிச, மவுன, கோபுர, சதுரங்க, கவன, சாகச, புராண, சிற்ப, துரித, நீண்டகால, அசாதாரண) -> EXCLUDE
    if num_letters >= 3 and word not in KNOWN_BASE_NOUNS:
        if word.endswith((
            "தள", "வலைத்தள", "செயல்தள", "நில", "குறுநில", "முக", "புதுமுக", "நிலைய", "கழக", "மன்ற", "மைய", "அங்க",
            "அரசாங்க", "அமைச்சக", "தூதரக", "அலுவலக", "பாடத்திட்ட", "வம்ச", "தேச", "நகர", "சமூக", "குடும்ப", "ஆவணக",
            "சரும", "கவுரவ", "கௌரவ", "மங்கள", "அபாய", "பாசிச", "மவுன", "கோபுர", "சதுரங்க", "கவன", "சாகச", "புராண",
            "சிற்ப", "துரித", "சாந்த", "அவசர", "இலவச", "சமரச", "சம்பிரதாய", "அபூர்வ", "ரகசிய", "நீண்டகால", "குறுகியகால",
            "சமீபகால", "பழங்கால", "எதிர்கால", "வருங்கால", "இடைக்கால", "சாதாரண", "அசாதாரண", "விநியோக", "சாதக", "பாதக", "செயலக", "சுந்தர", "திரைப்பட", "மற்றைய", "பின்னைய", "நேற்றைய", "நாணய",
            "சம்பவ", "வியாபார", "இராணுவ", "மனிதவள", "கலாசார", "அலங்கார", "நரசிம்ம"
        )):
            if not word.endswith((
                "தளம்", "நிலம்", "முகம்", "நிலையம்", "கழகம்", "மன்றம்", "மையம்", "அங்கம்", "அமைச்சகம்", "வம்சம்",
                "தேசம்", "நகரம்", "சமூகம்", "குடும்பம்", "ஆவணகம்", "சருமம்", "கவுரவம்", "கௌரவம்", "மங்களம்", "அபாயம்",
                "பாசிசம்", "மவுனம்", "மௌனம்", "கோபுரம்", "சதுரங்கம்", "கவனம்", "சாகசம்", "புராணம்", "சிற்பம்", "துரிதம்",
                "சாந்தம்", "அவசரம்", "இலவசம்", "சமரசம்", "சம்பிரதாயம்", "அபூர்வம்", "ரகசியம்", "நீண்டகாலம்", "குறுகியகாலம்",
                "சமீபகாலம்", "பழங்காலம்", "எதிர்காலம்", "வருங்காலம்", "இடைக்காலம்", "சாதாரணம்", "அசாதாரணம்", "விநியோகம்", "நாணயம்",
                "சம்பவம்", "வியாபாரம்", "இராணுவம்", "மனிதவளம்", "கலாசாரம்", "அலங்காரம்"
            )):
                return "EXCLUDED_PARTICIPLE", "ADJECTIVE_BOUND_STEM"

    # Colloquial vocatives / imperative clitics (e.g. சொல்லடா, நில்லடா, பாரடா, போடா, வாடா, என்னடா, சொல்லடி, பாரடி) -> EXCLUDE
    if num_letters >= 3 and (word.endswith("டா") or word.endswith("டி")):
        if word.endswith(("லடா", "ரடா", "க்கடா", "த்தடா", "ட்டடா", "ப்போடா", "வாடா", "போடா", "கடா", "யடா", "ளடா", "னடா", "மடா", "தடா", "ன்னடா")):
            return "EXCLUDED_OTHER", "COLLOQUIAL_VOCATIVE_ADA"
        if word.endswith(("லடி", "ரடி", "க்கடி", "த்தடி", "ப்போடி", "வாடி", "போடி", "கடி", "யடி", "ளடி", "னடி")) and word not in KNOWN_BASE_NOUNS and not word.endswith(("நேரடி", "அதிரடி", "பதிலடி", "காலடி", "கரடி", "முன்னோடி", "பின்னோடி", "மறுபடி", "தளபதி")):
            return "EXCLUDED_OTHER", "COLLOQUIAL_VOCATIVE_ADI"

    # Pronouns & pronominal stems (e.g. அவள், அவன், அவர், நீங்கள், உங்கள், இதன், அதன்) -> EXCLUDE
    if word in EXCLUDED_PRONOUNS:
        return "EXCLUDED_CASE", "PRONOUN"

    # Conjunctions, Postpositions & Particles (e.g. அல்லது, என்பது, பற்றி, குறித்து, எனவே, ஆகவே, ஆனால், கொண்டு, விட்டு) -> EXCLUDE
    if word in EXCLUDED_CONJUNCTIONS_AND_POSTPOSITIONS:
        return "EXCLUDED_PARTICIPLE", "CONJUNCTION_POSTPOSITION"

    # Dynamic Adjectival Stem Rule (The "ம்" Rule)
    # If word ends in inherent 'அ' sound and word+"ம்" or word+"ன்" or word+"ள்" is a valid high-freq base noun, it's a bound stem.
    if word not in USER_CURATED_WHITELIST and word:
        if '\u0b95' <= word[-1] <= '\u0bb9':
            if word + "ம்" in VALID_REFERENCE_WORDS or word + "ன்" in VALID_REFERENCE_WORDS or word + "ள்" in VALID_REFERENCE_WORDS:
                return "EXCLUDED_ADJECTIVAL_STEM", "STEM_M_N_L_NOUN"
                
        # Dynamic Verbal Noun Accusative Rule (The "வதை/பதை" -> "வது/பது" Rule)
        # Catches accusatives and interrogatives of verbal nouns/pronouns (e.g. இருப்பதை, சொல்வதை, உள்ளதா, நடந்ததை)
        VERBAL_NOUN_SUFFIXES = (
            "ந்ததா", "ந்ததை", "ட்டதா", "ட்டதை", "த்ததா", "த்ததை", 
            "ற்றதா", "ற்றதை", "ன்றதா", "ன்றதை", "ியதா", "ியதை", 
            "னதா", "னதை", "ளதா", "ளதை", "வதா", "வதை", 
            "பதா", "பதை", "ததா", "ததை", "ப்பதா", "ப்பதை"
        )
        if word.endswith(VERBAL_NOUN_SUFFIXES):
            root_thu = word[:-1] + "\u0bc1"  # replace \u0bc8 (ஐ) or \u0bbe (ஆ) with \u0bc1 (உ)
            if root_thu in VALID_REFERENCE_WORDS:
                return "EXCLUDED_CASE", "CASE_VERBAL_NOUN_ACCUSATIVE_OR_INTERROGATIVE"

    # Standalone Adjectives & Adjectival Stems (e.g. பல்வேறு, ஒவ்வொரு, அனைத்து, அதிக, சமூக, கரிம, சமண, உலக, தமிழக, தத்துவ) -> EXCLUDE
    if word in EXCLUDED_ADJECTIVES:
        return "EXCLUDED_PARTICIPLE", "ADJECTIVE_STEM"

    # Negative modal verbs (e.g. முடியாது, கூடாது, தெரியாது, புரியாது, இல்லாது) -> EXCLUDE
    if word in NEGATIVE_MODAL_VERBS:
        return "EXCLUDED_PAST", "NEGATIVE_MODAL"

    # Possessive pronouns (e.g. தனது, அவரது, எனது, உனது, அவனது, அவளது) -> EXCLUDE
    for suffix in POSSESSIVE_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "EXCLUDED_CASE", f"POSSESSIVE_{suffix}"

    # Neuter plural / participial verbs (e.g. உள்ளன, வந்தன, செய்தன, இருந்தன, பட்டன, ஆயின) -> EXCLUDE
    if num_letters >= 3:
        if (word.endswith("உள்ளன") or word.endswith("ள்ளன") or word.endswith("ப்பட்டன") or word.endswith("ந்தன") or word.endswith("த்தன") or word.endswith("ட்டன") or word.endswith("ன்றன")) and not (word.endswith("கின்றன") or word.endswith("க்கின்றன")):
            return "EXCLUDED_PARTICIPLE", "NEUTER_PLURAL_VERB"

    # 1. Check for Emphatic Clitics (தேற்ற ஏகாரம் / ஓகாரம் - e.g. அப்போதே, வைத்தே, போன்றே, வெறுமனே, யாருமே, என்னமோ, தானே, நானே) -> EXCLUDE
    if num_letters >= 2:
        if word.endswith(EMPHATIC_EE) or word.endswith("தானே") or word.endswith("மட்டுமே") or word.endswith("போதே"):
            return "EXCLUDED_EMPHATIC", "EMPHATIC_CLITIC_EE"
        if (num_letters >= 3 and word.endswith(EMPHATIC_OO)) or word.endswith("என்னமோ"):
            return "EXCLUDED_EMPHATIC", "EMPHATIC_CLITIC_OO"

    # 2. Check for Concessive Conditional Verbs (உம்மை எச்சம் / நிபந்தனை எச்சம் - e.g. போதெல்லாம், இருந்தும், செய்தும், ஆயினும்) -> EXCLUDE
    for suffix in CONCESSIVE_CONDITIONAL_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "EXCLUDED_CONCESSIVE", f"CONCESSIVE_{suffix}"

    # 3. Check for Inclusive Conjunction (உம்மை இடைச்சொல் - e.g. காலமும், படமும், பெண்ணும், எதிலும், மரங்களும், வழியும், அமைப்பும்) -> EXCLUDE
    if num_letters >= 3 and word.endswith("ம்"):
        # If preceding letter has u-vowel signs (\u0bc1 or \u0bc2), it is an inclusive conjunction / verbal -உம் form
        if len(word) >= 2 and (word[-2] in "\u0bc1\u0bc2" or any(c in "\u0bc1\u0bc2" for c in word[-3:])):
            if not (word.endswith("குழுமம்") or word == "வால்யூம்"):
                return "EXCLUDED_CONJUNCTION", "INCLUSIVE_CONJUNCTION_UM"

    # Check for modal / permissive verbs ending in -லாம் (e.g. கேட்கலாம், செய்யலாம், வரலாம், போகலாம்) -> EXCLUDE
    if num_letters >= 3 and word.endswith("லாம்"):
        return "EXCLUDED_PARTICIPLE", "MODAL_VERB_LAAM"

    # Check for negative verbal participles ending in -ஆமல் / -மல் (e.g. பெறாமல், அறியாமல், செய்யாமல்) -> EXCLUDE
    if num_letters >= 3 and (word.endswith("ாமல்") or word.endswith("யாமல்") or word.endswith("காமல்") or word.endswith("தாமல்")):
        return "EXCLUDED_PARTICIPLE", "NEGATIVE_PARTICIPLE_AAMAL"

    # 4. Check for Case Endings (வேற்றுமை உருபுகள் - Inflected Noun) -> EXCLUDE
    for suffix in CASE_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            # Allow root of 1+ grapheme for short accusative forms (e.g. உதட்டை → root உத = 2 graphemes)
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "EXCLUDED_CASE", f"CASE_{suffix}"

    # Check for Pronominal / Nominal Locative Case -உள் / -க்குள் (e.g. அதனுள், இதனுள், நமக்குள், அவற்றுள்)
    if num_letters >= 3 and (word.endswith("னுள்") or word.endswith("க்குள்") or word.endswith("ற்றுள்") or word.endswith("தனுள்")):
        if word not in USER_CURATED_WHITELIST:
            return "EXCLUDED_CASE", "CASE_LOCATIVE_UL"

    # Check for Accusative Case -ஐ ending on 3+ letter words (e.g. கேள்விகளை, என்பவரை, கோடியை, மரத்தை, கண்ணை, கல்லை, வழியை, நாக்கை, செல்வாக்கை, தலைப்பை, நெஞ்சை)
    if num_letters >= 3 and graphemes[-1].endswith(ACCUSATIVE_AI):
        if any(word.endswith(suffix) for suffix in ("த்தை", "த்தைக்", "த்தைப்", "த்தைச்", "க்களை", "ங்களை", "ன்களை", "களை", "வரை", "தனை")):
            return "EXCLUDED_CASE", "CASE_ACCUSATIVE_AI"
        if word.endswith("க்கை") and word not in USER_CURATED_WHITELIST:
            return "EXCLUDED_CASE", "CASE_ACCUSATIVE_AI"
        if word.endswith("ப்பை") and word not in USER_CURATED_WHITELIST:
            return "EXCLUDED_CASE", "CASE_ACCUSATIVE_AI"
        if word.endswith("ச்சை") and word not in USER_CURATED_WHITELIST:
            return "EXCLUDED_CASE", "CASE_ACCUSATIVE_AI"
        if word.endswith("ஞ்சை") and word not in USER_CURATED_WHITELIST:
            return "EXCLUDED_CASE", "CASE_ACCUSATIVE_AI"
        # -பை accusative: மார்பை, தேர்வை-type endings not in suffix list above
        if word.endswith("பை") and word not in USER_CURATED_WHITELIST:
            return "EXCLUDED_CASE", "CASE_ACCUSATIVE_AI"
        if any(word.endswith(s) for s in ("யை", "வை", "னை", "ளை", "லை", "டை", "றை", "ரை", "ணை")):
            if word not in USER_CURATED_WHITELIST:
                return "EXCLUDED_CASE", "CASE_ACCUSATIVE_AI"

    # Check for Locative/Ablative Case -இல் / -இன் on 3+ letter words (e.g. பாலில், தோளில், ஊரில், வானில், நோயின், நாட்டின்)
    if num_letters >= 3 and len(graphemes) >= 2:
        if graphemes[-1] == "ல்" and graphemes[-2].endswith("\u0bbf") and word not in USER_CURATED_WHITELIST:
            return "EXCLUDED_CASE", "CASE_LOCATIVE_IL"
        if graphemes[-1] == "ன்" and graphemes[-2].endswith("\u0bbf") and word not in USER_CURATED_WHITELIST:
            return "EXCLUDED_CASE", "CASE_ABLATIVE_IN"

    # Check for relative participles with -உள்ள (e.g. அதிலுள்ள, பட்டுள்ள, பெற்றுள்ள, கொண்டுள்ள)
    if num_letters >= 3 and (word.endswith("உள்ள") or word.endswith("ிலுள்ள") or word.endswith("இலுள்ள") or word.endswith("த்துள்ள") or word.endswith("ட்டுள்ள") or word.endswith("ப்பட்டுள்ள") or word.endswith("ந்துள்ள") or word.endswith("ண்டுள்ள") or word.endswith("ன்றுள்ள") or word.endswith("ற்றுள்ள") or word.endswith("கொண்டுள்ள") or word.endswith("பெற்றுள்ள") or word.endswith("வந்துள்ள") or word.endswith("யுள்ள") or word.endswith("வுள்ள") or word.endswith("முள்ள") or word.endswith("துள்ள") or word.endswith("குள்ள")):
        return "EXCLUDED_PARTICIPLE", "ADJECTIVE_POSTPOSITION_ULLA"

    # Check for negative relative participles ending in -ஆத (e.g. விரும்பாத, தெரியாத, புரியாத, செய்யாத, இல்லாத)
    if num_letters >= 3 and word.endswith("ாத"):
        return "EXCLUDED_PARTICIPLE", "NEGATIVE_PARTICIPLE_AATHA"

    # 5. Check for Relative Participles & Infinitives (பெயரெச்சங்கள் & வினையெச்சங்கள்) -> EXCLUDE
    for suffix in RELATIVE_PARTICIPLE_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "EXCLUDED_PARTICIPLE", f"RELATIVE_PARTICIPLE_{suffix}"

    # Check for past relative participles ending in -த்த, -ட்ட, -ந்த, -ற்ற, -ன்ற, -ிய
    if num_letters >= 2:
        if word.endswith("த்த") or word.endswith("ட்ட") or word.endswith("ந்த") or word.endswith("ற்ற") or word.endswith("ன்ற"):
            return "EXCLUDED_PARTICIPLE", "RELATIVE_PARTICIPLE_GEMINATE"
        if num_letters >= 3 and word.endswith("ய") and graphemes[-2].endswith("\u0bbf"):
            return "EXCLUDED_PARTICIPLE", "RELATIVE_PARTICIPLE_IYA"

    # Check for infinitive verbs (e.g. பார்க்க, படிக்க, செய்ய, வாழ்க, அணுக, ஆராய)
    # Also covers bare -ட infinitives: தூண்ட, நடமாட, தாண்ட, தேட, கணக்கிட, ஏற்பட
    if num_letters >= 3:
        if word.endswith("க்க") or word.endswith("குக") or word in ("செய்ய", "செல்ல", "சொல்ல", "கொள்ள", "வெல்ல", "கையாள", "அணுக", "இயங்க", "ஆராய", "பெய்ய", "வாழ்க", "செய்க", "வருக", "தருக", "சொடுக்குக", "காண்க", "துவங்க", "நெருங்க", "தப்ப", "பயில", "பழக", "விலக", "முன்னேற", "வெளிவர"):
            return "EXCLUDED_PARTICIPLE", "INFINITIVE_VERB"
        # Bare -ட infinitive: verb stems ending in bare ட grapheme (தூண்ட, நடமாட, தாண்ட, தேட)
        # Allow nouns legitimately ending in -ட: e.g. suffixes -ாடு, -ீடு handled elsewhere
        if graphemes[-1] == "ட" and num_letters >= 2:
            # Check it's a bare ட (no vowel sign) and not a known noun ending
            known_noun_ends_in_ta = ("கட", "நட", "வட", "கல்விட")  # placeholders for any allowed words
            if not any(word.endswith(n) for n in known_noun_ends_in_ta):
                return "EXCLUDED_PARTICIPLE", "INFINITIVE_VERB_TA"

    # Check for verbal participles ending in -பட்டு, -விட்டு, -இட்டு, -த்து, -ந்து, -த்தி, -சென்று, -செய்து (e.g. வைத்து, பார்த்து, செய்து, வந்து, சென்று, நின்று, கற்று, பெற்று, வழிபட்டு, ஒப்பிட்டு, கைவிட்டு, ஆதரித்து, இடிந்து, படுத்தி)
    if num_letters >= 3:
        if word.endswith("பட்டு") or word.endswith("விட்டு") or word.endswith("இட்டு") or word.endswith("யிட்டு") or word.endswith("ப்பட்டு"):
            return "EXCLUDED_PARTICIPLE", "VERBAL_PARTICIPLE_TTU"
        if word.endswith("த்து") or word.endswith("ந்து") or word.endswith("த்தி") or word.endswith("ங்கி") or word.endswith("சென்று") or word.endswith("நின்று") or word.endswith("வென்று") or word.endswith("கற்று") or word.endswith("பெற்று") or word.endswith("செய்து"):
            return "EXCLUDED_PARTICIPLE", "VERBAL_PARTICIPLE_SUF"

    # Check for comparative particle -விட (e.g. இதைவிட, அதைவிட)
    if word.endswith("விட") and num_letters >= 3:
        return "EXCLUDED_PARTICIPLE", "COMPARATIVE_VIDA"

    # Check for colloquial spoken present tense -உற / -ற (e.g. பேசுற, வருற, கொடுற, சொல்லுற)
    # These are colloquial contractions of -உகிற / -கிற
    if num_letters >= 3 and graphemes[-1] == "ற" and graphemes[-2].endswith("ு"):
        return "EXCLUDED_OTHER", "COLLOQUIAL_SPOKEN_REH"

    # Check for colloquial locative/genitive -ய ending (e.g. வேலைய, நாட்டுய, படத்துய)
    # Colloquial contraction of -இல்/இன் on nouns ending in vowel
    if num_letters >= 3 and graphemes[-1] == "ய" and graphemes[-2].endswith("ை"):
        return "EXCLUDED_OTHER", "COLLOQUIAL_LOCATIVE_YA"

    # Check for interrogative clitic -ஆ (வினா உருபு - e.g. அப்படியா, உண்மையா, சரியா, அப்பாவா, தானா, அவனா, அவளா)
    if num_letters >= 3:
        if word.endswith("யா") or word.endswith("தானா") or word.endswith("அப்பாவா") or word.endswith("உண்மையா") or word.endswith("சரியா") or word.endswith("வந்ததா") or word.endswith("செய்ததா"):
            return "EXCLUDED_OTHER", "INTERROGATIVE_AA"

    # 6. Check for Adjectival Suffixes (பெயரடை விகுதிகள் - e.g. உயரமான, அழகான, முக்கியமான) -> EXCLUDE
    for suffix in ADJECTIVE_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "EXCLUDED_PARTICIPLE", f"ADJECTIVE_SUFFIX_{suffix}"

    # 7. Check for Adverbial Suffixes (வினையடை விகுதிகள் - e.g. செய்ததாக, வேகமாக, நன்றாக) -> EXCLUDE
    for suffix in ADVERB_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "EXCLUDED_PARTICIPLE", f"ADVERB_SUFFIX_{suffix}"

    # 8. Check for Present Tense Verb Endings (நிகழ்கால வினைமுற்று மட்டும் - Finite verbs)
    for suffix in PRESENT_TENSE_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "PRESENT_TENSE", f"PRESENT_MARKER_{suffix}"

    # Single letter or short base words (ஏவல் வினை / சொல்)
    if num_letters <= 2:
        return "NOUN", "SHORT_BASE_WORD"

    # 6. Check for Past Tense Suffixes (இறந்தகால வினை) -> EXCLUDE
    for suffix in PAST_TENSE_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "EXCLUDED_PAST", f"PAST_MARKER_{suffix}"

    # 7. Check for Future Tense Suffixes (எதிர்கால வினை) -> EXCLUDE
    for suffix in FUTURE_TENSE_SUFFIXES:
        if word.endswith(suffix):
            root = word[:-len(suffix)]
            if len(get_tamil_graphemes(root)) >= 1 or word == suffix:
                return "EXCLUDED_FUTURE", f"FUTURE_MARKER_{suffix}"

    # 8. Check for Conditional / Participle Endings -> EXCLUDE
    for suffix in PARTICIPLE_CONDITION_SUFFIXES:
        if word.endswith(suffix):
            return "EXCLUDED_PARTICIPLE", f"PARTICIPLE_{suffix}"

    # 9. Check for Accusative Case -ஐ ending (e.g. மரத்தை, வீட்டினை, பூவை)
    if num_letters >= 4 and (word.endswith("த்தை") or word.endswith("த்தினை") or word.endswith("்களை")):
        return "EXCLUDED_CASE", "CASE_ACCUSATIVE_AI"

    # 10. Check for Verbal Nouns & Nominalizer Suffixes (தொழிற்பெயர் / ஆகுபெயர்)
    for suffix in NOUN_NOMINAL_SUFFIXES:
        if word.endswith(suffix):
            return "NOUN", f"NOMINAL_SUFFIX_{suffix}"

    # 11. Standard Nominative / Base Nouns
    last_grapheme = graphemes[-1]
    if last_grapheme in ("ம்", "ன்", "ர்", "ள்", "ல்", "ய்", "ழ்", "ண்"):
        return "NOUN", f"BASE_NOUN_CONSONANT_{last_grapheme}"
    
    if last_grapheme in ("து", "டு", "று", "பு", "வு", "மை", "கை", "வை", "சு", "கு", "ழி", "லி", "ளி", "ரி", "தி", "சி"):
        return "NOUN", f"BASE_NOUN_VOWEL_{last_grapheme}"

    # Default to base noun
    return "NOUN", "BASE_NOUN"


def process_tamil_word_pipeline(
    input_csv_path: str,
    output_csv_path: str,
    allowed_lengths: Optional[Set[int]] = None,
    min_frequency: int = 1,
    filter_mode: str = "keep",  # "keep" retains NOUN & PRESENT_TENSE; "remove" excludes them
    top_n: Optional[int] = None,
    top_n_output: Optional[str] = None,
    export_game_json: Optional[str] = None,
    json_lengths: Optional[List[int]] = None
) -> Dict[str, int]:
    """
    Main streaming pipeline to process the frequency CSV and filter words.
    """
    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"Input file not found: {input_csv_path}")

    print("Pre-loading valid '-ம்' and '-து' reference nouns...")
    load_valid_reference_words(input_csv_path)
    print(f"Loaded {len(VALID_REFERENCE_WORDS):,} valid reference nouns.")

    if json_lengths is None:
        json_lengths = [3, 4, 5]

    print(f"--- Tamil Word Filter Pipeline ---")
    print(f"Input File: {input_csv_path}")
    print(f"Output CSV: {output_csv_path}")
    print(f"Allowed Lengths: {sorted(allowed_lengths) if allowed_lengths else 'All'}")
    print(f"Min Frequency: {min_frequency}")
    print(f"Filter Mode: {filter_mode.upper()} (Target: NOUN & PRESENT_TENSE)")
    if top_n:
        print(f"Top N: {top_n:,}")
    if export_game_json:
        print(f"Export Game JSON: {export_game_json}")

    stats = {
        "total_rows_read": 0,
        "valid_tamil_words": 0,
        "passed_length_filter": 0,
        "passed_freq_filter": 0,
        "classified_noun": 0,
        "classified_present_tense": 0,
        "classified_excluded_past": 0,
        "classified_excluded_future": 0,
        "classified_excluded_case": 0,
        "classified_excluded_participle": 0,
        "classified_excluded_other": 0,
        "final_output_count": 0,
    }

    # Data structures for game export if requested
    words_by_len: Dict[int, Dict[str, int]] = {l: {} for l in json_lengths}
    filtered_results: List[Tuple[str, int, int, str, str]] = []

    # Ensure output directories exist
    os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)
    if export_game_json:
        os.makedirs(os.path.dirname(os.path.abspath(export_game_json)), exist_ok=True)
    if top_n_output:
        os.makedirs(os.path.dirname(os.path.abspath(top_n_output)), exist_ok=True)

    with open(input_csv_path, mode="r", encoding="utf-8") as fin:
        reader = csv.reader(fin)
        # Skip header if present
        header = next(reader, None)

        for row in reader:
            if not row:
                continue
            stats["total_rows_read"] += 1
            word = row[0].strip()
            freq = int(row[1]) if len(row) > 1 and row[1].isdigit() else 0

            # Grapheme extraction & validation
            graphemes = get_tamil_graphemes(word)
            if not graphemes:
                continue
            stats["valid_tamil_words"] += 1

            length = len(graphemes)
            if allowed_lengths and length not in allowed_lengths:
                continue
            stats["passed_length_filter"] += 1

            if freq < min_frequency:
                continue
            stats["passed_freq_filter"] += 1

            # Classification
            category, tag_detail = classify_tamil_word(word, graphemes)

            if category == "NOUN":
                stats["classified_noun"] += 1
            elif category == "PRESENT_TENSE":
                stats["classified_present_tense"] += 1
            elif category == "EXCLUDED_PAST":
                stats["classified_excluded_past"] += 1
            elif category == "EXCLUDED_FUTURE":
                stats["classified_excluded_future"] += 1
            elif category == "EXCLUDED_CASE":
                stats["classified_excluded_case"] += 1
            elif category == "EXCLUDED_PARTICIPLE":
                stats["classified_excluded_participle"] += 1
            else:
                stats["classified_excluded_other"] += 1

            # Determine acceptance based on filter_mode
            is_target_pos = category in ("NOUN", "PRESENT_TENSE")
            accept = is_target_pos if filter_mode == "keep" else not is_target_pos

            if accept:
                stats["final_output_count"] += 1
                filtered_results.append((word, freq, length, category, tag_detail))
                if length in words_by_len:
                    if word not in words_by_len[length] or freq > words_by_len[length][word]:
                        words_by_len[length][word] = freq

            if stats["total_rows_read"] % 1000000 == 0:
                print(f"Processed {stats['total_rows_read']:,} rows... Found {stats['final_output_count']:,} target words.")

    # Sort results by frequency descending
    filtered_results.sort(key=lambda x: x[1], reverse=True)

    # Write primary output CSV
    print(f"Writing {len(filtered_results):,} records to {output_csv_path}...")
    with open(output_csv_path, mode="w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["word", "frequency", "length", "category", "tag_detail"])
        for record in filtered_results:
            writer.writerow(record)

    # Export Top N CSV if requested
    if top_n and top_n > 0:
        top_n_records = filtered_results[:top_n]
        top_n_records.sort(key=lambda x: x[0])  # Sort alphabetically
        n_out_path = top_n_output or output_csv_path.replace(".csv", f"_top_{top_n}.csv")
        print(f"Writing top {len(top_n_records):,} records alphabetically to {n_out_path}...")
        with open(n_out_path, mode="w", encoding="utf-8", newline="") as fnout:
            writer = csv.writer(fnout)
            writer.writerow(["word", "frequency", "length", "category", "tag_detail"])
            for record in top_n_records:
                writer.writerow(record)

    # Optional Game JSON Export
    if export_game_json:
        print(f"Generating Wordle game JSON assets...")
        sorted_by_len = {}
        for l in json_lengths:
            sorted_by_len[l] = sorted(words_by_len[l].items(), key=lambda x: x[1], reverse=True)
            print(f"  Length {l} words available: {len(sorted_by_len[l]):,}")

        # Top target secret words list: use top_n_records if available, else top 1500
        target_source = top_n_records if (top_n and top_n > 0) else filtered_results[:1500]
        main_words = []
        for record in target_source:
            word_str = record[0]
            letters = get_tamil_graphemes(word_str)
            main_words.append(letters)

        top_entire = []
        for l in json_lengths:
            for word, freq in sorted_by_len[l][:10000]:
                top_entire.append(word)

        with open(export_game_json, "w", encoding="utf-8") as f:
            json.dump({
                "tamilMainWordList": main_words,
                "tamilEntireWordList": top_entire
            }, f, ensure_ascii=False, separators=(',', ':'))

        # Also write fallback words.json
        json_dir = os.path.dirname(export_game_json)
        words_fallback_path = os.path.join(json_dir, "words.json")
        with open(words_fallback_path, "w", encoding="utf-8") as f:
            json.dump({
                "tamilMainWordList": main_words,
                "tamilEntireWordList": top_entire
            }, f, ensure_ascii=False, separators=(',', ':'))

        # Also write individual length files if in public folder
        for l in json_lengths:
            per_len_path = os.path.join(json_dir, f"words_{l}.json")
            with open(per_len_path, "w", encoding="utf-8") as f:
                json.dump([w for w, _ in sorted_by_len[l]], f, ensure_ascii=False, separators=(',', ':'))

    print("--- Summary Statistics ---")
    for key, value in stats.items():
        print(f"  {key}: {value:,}")
    print("--------------------------")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Tamil Wordle Noun & Present Tense Word Filter Pipeline")
    parser.add_argument(
        "--input", "-i",
        default="/Users/kokulapalan/projects/tamilwordle/data/aviiciii-tamil-words-frequency.csv",
        help="Path to master input CSV (default: data/aviiciii-tamil-words-frequency.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        default="/Users/kokulapalan/projects/tamilwordle/data/filtered_tamil_words.csv",
        help="Path to output filtered CSV (default: data/filtered_tamil_words.csv)"
    )
    parser.add_argument(
        "--lengths", "-l",
        default="3,4,5",
        help="Comma-separated list of allowed letter lengths or 'all' (default: 3,4,5)"
    )
    parser.add_argument(
        "--min-freq", "-f",
        type=int,
        default=2,
        help="Minimum frequency threshold (default: 2)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["keep", "remove"],
        default="keep",
        help="'keep': Retain nouns and simple present tense words. 'remove': Exclude them. (default: keep)"
    )
    parser.add_argument(
        "--top-n", "-n",
        type=int,
        default=1500,
        help="Extract top N most frequent words from the filtered list (default: 1500)"
    )
    parser.add_argument(
        "--top-n-output",
        default="/Users/kokulapalan/projects/tamilwordle/data/top_1500_filtered_words.csv",
        help="Path to export top N CSV (default: data/top_1500_filtered_words.csv)"
    )
    parser.add_argument(
        "--export-game-json",
        default="/Users/kokulapalan/projects/tamilwordle/frontend/public/top_words.json",
        help="Path to export game JSON (e.g. frontend/public/top_words.json)"
    )

    args = parser.parse_args()

    allowed_lengths = None
    if args.lengths.lower() != "all":
        allowed_lengths = {int(x.strip()) for x in args.lengths.split(",") if x.strip().isdigit()}

    process_tamil_word_pipeline(
        input_csv_path=args.input,
        output_csv_path=args.output,
        allowed_lengths=allowed_lengths,
        min_frequency=args.min_freq,
        filter_mode=args.mode,
        top_n=args.top_n,
        top_n_output=args.top_n_output,
        export_game_json=args.export_game_json
    )


if __name__ == "__main__":
    main()