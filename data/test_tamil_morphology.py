#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Tamil morphological classifier and word filter pipeline.
"""

import unittest
from filter_words_pipeline import get_tamil_graphemes, classify_tamil_word


class TestTamilMorphology(unittest.TestCase):

    def test_grapheme_segmentation(self):
        """Test Unicode grapheme segmentation across various Tamil character combinations."""
        # 1. Base consonant + vowel sign: 'வணக்கம்' -> ['வ', 'ண', 'க்', 'க', 'ம்'] (5 letters)
        letters = get_tamil_graphemes("வணக்கம்")
        self.assertEqual(letters, ["வ", "ண", "க்", "க", "ம்"])
        self.assertEqual(len(letters), 5)

        # 2. Uyir + Mei: 'அம்மா' -> ['அ', 'ம்', 'மா'] (3 letters)
        self.assertEqual(get_tamil_graphemes("அம்மா"), ["அ", "ம்", "மா"])

        # 3. Ayutha ezhuthu: 'அஃது' -> ['அ', 'ஃ', 'து'] (3 letters)
        self.assertEqual(get_tamil_graphemes("அஃது"), ["அ", "ஃ", "து"])

        # 4. Invalid input
        self.assertEqual(get_tamil_graphemes("hello"), [])
        self.assertEqual(get_tamil_graphemes("1234"), [])
        self.assertEqual(get_tamil_graphemes("தமிழ்123"), [])

    def test_base_and_derived_nouns(self):
        """Test classification of base and derived nouns."""
        nouns = [
            ("மரம்", "NOUN"),
            ("புத்தகம்", "NOUN"),
            ("அரசன்", "NOUN"),
            ("அரசி", "NOUN"),
            ("தலைவர்", "NOUN"),
            ("நன்மை", "NOUN"),
            ("வாழ்க்கை", "NOUN"),
            ("அன்பு", "NOUN"),
            ("படித்தல்", "NOUN"),
            ("செயல்", "NOUN"),
            ("பார்வை", "NOUN"),
            ("ஆசிரியர்", "NOUN"),
            ("கவிஞர்", "NOUN"),
            ("அறிஞர்", "NOUN"),
            ("விவசாயி", "NOUN"),
            ("மருத்துவர்", "NOUN"),
            ("சூரியன்", "NOUN"),
            ("நிலவு", "NOUN"),
            ("வானம்", "NOUN"),
            ("பாட்டு", "NOUN"),
            ("காட்சி", "NOUN"),
        ]
        for word, expected_cat in nouns:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, expected_cat, f"Failed for word: {word}, got: {cat} ({tag})")

    def test_present_tense_verbs(self):
        """Test classification of simple finite present tense verbs."""
        present_verbs = [
            ("செய்கிறான்", "PRESENT_TENSE"),
            ("படிக்கிறாள்", "PRESENT_TENSE"),
            ("பாடுகிறார்", "PRESENT_TENSE"),
            ("நடக்கிறது", "PRESENT_TENSE"),
            ("வருகின்றன", "PRESENT_TENSE"),
            ("எழுதுகிறேன்", "PRESENT_TENSE"),
            ("செய்கிறோம்", "PRESENT_TENSE"),
            ("பார்க்கிறாய்", "PRESENT_TENSE"),
            ("செய்கின்றனர்", "PRESENT_TENSE"),
            ("படிக்கின்றார்", "PRESENT_TENSE"),
            ("வாழ்கிறான்", "PRESENT_TENSE"),
            ("பேசுகிறார்", "PRESENT_TENSE"),
        ]
        for word, expected_cat in present_verbs:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, expected_cat, f"Failed for word: {word}, got: {cat} ({tag})")

    def test_excluded_relative_participles(self):
        """Test exclusion of present and past relative participles."""
        participles = [
            "கட்டிய", "ஓடிய", "பாடிய", "பேசிய", "வாங்கிய", "எழுதிய",
            "செய்கிற", "படிக்கிற", "வருகின்ற", "என்கிற",
            "செய்த", "படித்த", "வந்த", "போன", "இருந்த", "கடந்த", "சொன்ன",
        ]
        for word in participles:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, "EXCLUDED_PARTICIPLE", f"Participle '{word}' was not excluded! Got {cat} ({tag})")

    def test_excluded_adjectives_and_adverbs(self):
        """Test exclusion of adjectival suffixes (-ஆன) and adverbial suffixes (-ஆக)."""
        adj_adv = [
            "உயரமான", "அழகான", "முக்கியமான", "சிறப்பான", "சரியான",
            "செய்ததாக", "வந்ததாக", "வேகமாக", "நன்றாக",
        ]
        for word in adj_adv:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, "EXCLUDED_PARTICIPLE", f"Adjective/Adverb '{word}' was not excluded! Got {cat} ({tag})")

    def test_excluded_past_tense(self):
        """Test detection and exclusion of past tense verb forms."""
        past_verbs = [
            "செய்தான்",
            "படித்தாள்",
            "வந்தார்",
            "ஓடியது",
            "சென்றான்",
            "ஆனது",
            "ஆயிற்று",
            "போனது",
            "இருந்தது",
            "முடிந்தது",
            "பாடினார்",
            "கொடுத்தான்",
            "கற்றார்",
            "கண்டான்",
            "போனேன்",
            "வந்தேன்",
            "செய்தேன்",
            "ஆனேன்",
        ]
        for word in past_verbs:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, "EXCLUDED_PAST", f"Past verb '{word}' was not excluded! Got {cat} ({tag})")

    def test_excluded_future_tense(self):
        """Test detection and exclusion of future tense verb forms."""
        future_verbs = [
            "செய்வான்",
            "படிப்பாள்",
            "வருவார்",
            "பாடுபான்",
            "நடப்பார்",
            "காண்பான்",
            "வாழ்வார்",
        ]
        for word in future_verbs:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, "EXCLUDED_FUTURE", f"Future verb '{word}' was not excluded! Got {cat} ({tag})")

    def test_excluded_case_inflections(self):
        """Test detection and exclusion of case-inflected noun forms (Inflected Noun)."""
        inflected = [
            "மரத்தை",
            "மரத்தால்",
            "மரத்துக்கு",
            "மரத்தில்",
            "மரத்தினுடைய",
            "மரத்தோடு",
            "அவரிடம்",
            "வீட்டிலிருந்து",
            "நாட்டிற்கு",
            "கேள்விகளை",
            "என்பவரை",
            "கண்ணை",
        ]
        for word in inflected:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, "EXCLUDED_CASE", f"Inflected form '{word}' was not excluded! Got {cat} ({tag})")

    def test_excluded_inclusive_conjunctions(self):
        """Test detection and exclusion of inclusive conjunctions (-உம் / எண்ணும்மை)."""
        conjunctions = [
            "காலமும்",
            "படமும்",
            "பெண்ணும்",
            "எதிலும்",
            "மரங்களும்",
            "வழியும்",
            "நாடுகளும்",
            "அமைதியும்",
        ]
        for word in conjunctions:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, "EXCLUDED_CONJUNCTION", f"Inclusive conjunction '{word}' was not excluded! Got {cat} ({tag})")

    def test_excluded_emphatic_clitics(self):
        """Test detection and exclusion of emphatic clitics (-ஏ / -ஓ / தேற்ற ஏகாரம்)."""
        emphatics = [
            "அப்போதே",
            "வைத்தே",
            "போன்றே",
            "வெறுமனே",
            "யாருமே",
            "என்னமோ",
            "தானே",
        ]
        for word in emphatics:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, "EXCLUDED_EMPHATIC", f"Emphatic clitic '{word}' was not excluded! Got {cat} ({tag})")

    def test_excluded_adjectival_stems_and_pronouns(self):
        """Test detection and exclusion of adjectival stems, pronouns, possessives, and participles."""
        adjectival_and_participles = [
            "உள்ளன",
            "வைத்து",
            "சென்று",
            "செய்து",
            "பார்த்து",
            "சமூக",
            "பல்வேறு",
            "ஒவ்வொரு",
            "அதிக",
            "அவள்",
            "அவன்",
            "அவர்",
            "நீங்கள்",
            "உங்கள்",
            "இதன்",
            "தனது",
            "முடியாது",
            "இணையதள",
            "பல்கலைக்கழக",
            "சட்டமன்ற",
            "அரசாங்க",
            "இணைய",
            "ராணுவ",
            "ஊரக",
            "கிராம",
            "பிரபல",
            "கேட்க",
            "பரப்ப",
            "கணக்கிட",
            "நிரப்ப",
            "குறுநில",
            "புதுமுக",
            "வம்ச",
            "தொடங்",
            "திருப்ப",
            "விளங்க",
            "ஆவணக",
            "சரும",
            "படிச்ச",
            "பாசிச",
            "மவுன",
            "கோபுர",
            "கவன",
            "சாகச",
            "சதுரங்க",
            "நீண்டகால",
            "அசாதாரண",
            "வழிபட",
            "விநியோக",
            "நாணய",
        ]
        for word in adjectival_and_participles:
            cat, tag = classify_tamil_word(word)
            self.assertIn(
                cat,
                ("EXCLUDED_PARTICIPLE", "EXCLUDED_CASE", "EXCLUDED_PAST", "EXCLUDED_OTHER"),
                f"Word '{word}' should have been excluded! Got {cat} ({tag})"
            )

    def test_excluded_proper_nouns(self):
        """Test detection and exclusion of proper nouns (மக்கள்/இடங்களின் பெயர்கள்)."""
        proper_nouns = [
            "ராமசாமி",
            "செல்லப்பா",
            "அசோகன்",
            "அகிலன்",
            "அபிராமி",
            "ராதிகா",
            "சுபாஷ்",
            "காயத்ரி",
            "முருகதாஸ்",
            "ஜெர்மன்",
            "அசாம்",
            "ஐரோப்பா",
            "பாகுபலி",
            "கோபால்",
            "ஜடேஜா",
            "நாசர்",
            "லெனின்",
            "ஸ்டாலின்",
            "சிவகாமி",
            "இராமன்",
            "மனோகர்",
            "பானர்ஜி",
            "சாஸ்திரி",
            "சுஜாதா",
            "கண்ணன்",
            "குமார்",
            "அன்பழகன்",
            "நெடுஞ்செழியன்",
            "கரிகாலன்",
            "செங்குட்டுவன்",
            "வானதி",
            "குந்தவை",
            "பூங்குழலி",
            "கதிர்வேல்",
            "முத்துச்செல்வன்",
            "அருண்மொழி",
            "கன்னியாகுமரி",
            "திருநெல்வேலி",
            "கோயம்புத்தூர்",
            "தாமிரபரணி",
            "சடகோபன்",
            "அனுராதா",
            "ரமணன்",
            "அனுத்தமா",
            "நடேசன்",
            "சுசித்ரா",
            "சஞ்சய்",
            "ராகவ்",
            "சொல்லடா",
            "நில்லடா",
        ]
        for word in proper_nouns:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, "EXCLUDED_OTHER", f"Proper noun '{word}' was not excluded! Got {cat} ({tag})")

    def test_excluded_obliques_and_infinitives(self):
        """Test detection and exclusion of oblique pronouns, combining forms, and infinitives."""
        words = [
            "இவற்றுள்",
            "அவற்றுள்",
            "தன்னுடன்",
            "தன்னை",
            "என்னை",
            "உன்னை",
            "தனக்கு",
            "எனக்கு",
            "துணை",
            "மறு",
            "செய்ய",
            "செல்ல",
            "சொல்ல",
            "வாழ்க",
            "அணுக",
            "இயங்க",
            "சொடுக்குக",
            "பெய்ய",
            "உலக",
            "தமிழக",
            "தத்துவ",
            "என்ன",
            "அல்லது",
            "என்பது",
            "பற்றி",
            "கொண்டு",
            "அப்பாவா",
        ]
        for word in words:
            cat, tag = classify_tamil_word(word)
            self.assertIn(
                cat,
                ("EXCLUDED_PARTICIPLE", "EXCLUDED_CASE", "EXCLUDED_OTHER"),
                f"Word '{word}' should have been excluded! Got {cat} ({tag})"
            )

    def test_excluded_unsupported_keyboard_characters(self):
        """Test exclusion of words containing characters not present on the keyboard (Grantha: ஜ, ஷ, ஸ, ஹ, etc.)."""
        grantha_and_unsupported = [
            "சர்வீஸ்",
            "நிதிஷ்",
            "பிரான்சிஸ்",
            "ஜனவரி",
            "ஹோட்டல்",
            "கலெக்ஷன்",
            "விஷயம்",
            "ரோஜா",
            "ஷண்முகம்",
            "லக்ஷ்மி",
        ]
        for word in grantha_and_unsupported:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(
                cat,
                "EXCLUDED_OTHER",
                f"Word '{word}' containing non-keyboard characters was not excluded! Got {cat} ({tag})"
            )

    def test_numerals_and_adverbs_exclusion(self):
        """Test exclusion of numerals, ordinals, discourse adverbs, and particles."""
        test_cases = [
            ('முதல்', 'EXCLUDED_OTHER'),
            ('இரண்டு', 'EXCLUDED_OTHER'),
            ('நேற்று', 'EXCLUDED_OTHER'),
            ('பிறகு', 'EXCLUDED_OTHER'),
            ('அதிகம்', 'EXCLUDED_OTHER'),
            ('பின்னர்', 'EXCLUDED_OTHER'),
            ('என்பதை', 'EXCLUDED_OTHER'),
            ('நன்றி', 'EXCLUDED_OTHER'),
            ('உண்டு', 'EXCLUDED_OTHER'),
            ('லட்சம்', 'EXCLUDED_OTHER'),
            ('சுமார்', 'EXCLUDED_OTHER'),
            ('தவிர', 'EXCLUDED_OTHER'),
            ('அல்ல', 'EXCLUDED_OTHER'),
            ('நான்கு', 'EXCLUDED_OTHER'),
            ('கொஞ்சம்', 'EXCLUDED_OTHER'),
            ('நல்லது', 'EXCLUDED_OTHER'),
            ('சிறிது', 'EXCLUDED_OTHER'),
            ('ரொம்ப', 'EXCLUDED_OTHER'),
            ('நிறைய', 'EXCLUDED_OTHER'),
            ('போன்று', 'EXCLUDED_OTHER'),
            ('தவறு', 'EXCLUDED_OTHER'),
            ('மூன்றாம்', 'EXCLUDED_OTHER'),
            ('முதலாவது', 'EXCLUDED_OTHER'),
            ('ஒன்னு', 'EXCLUDED_OTHER'),
            ('ரெண்டு', 'EXCLUDED_OTHER'),
        ]
        for word, expected_cat in test_cases:
            cat, tag = classify_tamil_word(word)
            self.assertEqual(cat, expected_cat, f'Failed on {word}: got {cat} ({tag})')


if __name__ == "__main__":
    unittest.main()
