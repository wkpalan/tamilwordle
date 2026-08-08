import csv
import json
import re

tamil_regex = re.compile(r"^[\u0b80-\u0bff]+$")
grapheme_regex = re.compile(r"[\u0b80-\u0bff][\u0bbe-\u0bcd\u0bd7]?", re.IGNORECASE)

def get_tamil_letters(word):
    if not isinstance(word, str):
        return []
    word = word.strip()
    if not tamil_regex.match(word):
        return []
    return grapheme_regex.findall(word)

word_freq = {}

csv_file = "/Users/kokulapalan/projects/tamilwordle/data/aviiciii-tamil-words-frequency.csv"
print(f"Reading {csv_file}...")

with open(csv_file, mode="r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader, None) # skip header
    for row in reader:
        if not row:
            continue
        word = row[0].strip()
        freq = int(row[1]) if len(row) > 1 and row[1].isdigit() else 0
        
        letters = get_tamil_letters(word)
        l = len(letters)
        if l in (3, 4, 5):
            if word not in word_freq or freq > word_freq[word]:
                word_freq[word] = freq

print(f"Total unique valid 3,4,5-letter words found: {len(word_freq)}")

# Sort words by frequency (highest first)
sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

entire_words = []
main_words = []

# Main target pool: top 25,000 words with frequency >= 5 (or top frequency)
for word, freq in sorted_words:
    letters = grapheme_regex.findall(word)
    entire_words.append(word)
    if freq >= 5 and len(main_words) < 30000:
        main_words.append(letters)

print(f"Main target pool count: {len(main_words)}")
print(f"Entire dictionary count: {len(entire_words)}")

# Write to top_words.json
json_file = "/Users/kokulapalan/projects/tamilwordle/frontend/public/top_words.json"
print(f"Writing to {json_file}...")
with open(json_file, "w", encoding="utf-8") as f:
    json.dump({
        "tamilMainWordList": main_words,
        "tamilEntireWordList": entire_words
    }, f, ensure_ascii=False, separators=(',', ':'))

# Write to top_10000.csv
csv_out = "/Users/kokulapalan/projects/tamilwordle/frontend/public/top_10000.csv"
print(f"Writing to {csv_out}...")
with open(csv_out, "w", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["word", "frequency", "length"])
    for word, freq in sorted_words:
        letters = grapheme_regex.findall(word)
        writer.writerow([word, freq, len(letters)])

print("Done processing word lists!")
