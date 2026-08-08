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

words_by_len = {3: {}, 4: {}, 5: {}}

csv_file = "/Users/kokulapalan/projects/tamilwordle/data/aviiciii-tamil-words-frequency.csv"
print(f"Reading {csv_file}...")

with open(csv_file, mode="r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader, None)
    for row in reader:
        if not row:
            continue
        word = row[0].strip()
        freq = int(row[1]) if len(row) > 1 and row[1].isdigit() else 0
        
        letters = get_tamil_letters(word)
        l = len(letters)
        if l in words_by_len:
            if word not in words_by_len[l] or freq > words_by_len[l][word]:
                words_by_len[l][word] = freq

sorted_by_len = {}
for l in [3, 4, 5]:
    sorted_by_len[l] = sorted(words_by_len[l].items(), key=lambda x: x[1], reverse=True)
    print(f"Length {l} count: {len(sorted_by_len[l])}")

main_words = []
top_entire = []

for l in [3, 4, 5]:
    for word, freq in sorted_by_len[l][:5000]:
        letters = grapheme_regex.findall(word)
        main_words.append(letters)
    for word, freq in sorted_by_len[l][:10000]:
        top_entire.append(word)

# Write fast initial top_words.json
json_file = "/Users/kokulapalan/projects/tamilwordle/frontend/public/top_words.json"
print(f"Writing to {json_file}...")
with open(json_file, "w", encoding="utf-8") as f:
    json.dump({
        "tamilMainWordList": main_words,
        "tamilEntireWordList": top_entire
    }, f, ensure_ascii=False, separators=(',', ':'))

# Write full per-length dictionaries
for l in [3, 4, 5]:
    out_path = f"/Users/kokulapalan/projects/tamilwordle/frontend/public/words_{l}.json"
    print(f"Writing to {out_path}...")
    words_list = [w for w, f in sorted_by_len[l]]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(words_list, f, ensure_ascii=False, separators=(',', ':'))

# Write full top_10000.csv
csv_out = "/Users/kokulapalan/projects/tamilwordle/frontend/public/top_10000.csv"
print(f"Writing to {csv_out}...")
with open(csv_out, "w", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["word", "frequency", "length"])
    for l in [3, 4, 5]:
        for word, freq in sorted_by_len[l]:
            writer.writerow([word, freq, l])

print("Optimization complete!")
