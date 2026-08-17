#!/usr/bin/env python3
"""
Tamil Wordle - Automated ML-Assisted Proper Noun & POS Audit Framework
======================================================================
This tool utilizes Stanford Stanza (Universal Dependencies Neural Model for Tamil)
and Transformer NER to automatically audit Wordle word lists, flag proper nouns
(PROPN / Person / Location / Deity names), and generate audit reports.

Usage:
  python data/audit_proper_nouns_ml.py
  python data/audit_proper_nouns_ml.py --input data/top_1500_filtered_words.csv --output-report data/ml_audit_report.md
  python data/audit_proper_nouns_ml.py --auto-append
"""

import os
import sys
import csv
import time
import argparse
from typing import List, Dict, Tuple

try:
    from filter_words_pipeline import KNOWN_BASE_NOUNS, CORE_TAMIL_BASE_NOUNS
except ImportError:
    KNOWN_BASE_NOUNS = set()
    CORE_TAMIL_BASE_NOUNS = set()

try:
    import stanza
except ImportError:
    print("Error: Stanza is not installed. Run: micromamba install stanza")
    sys.exit(1)


def load_input_words(input_path: str) -> List[Tuple[str, int, int]]:
    """Loads words, frequencies, and lengths from CSV or TXT."""
    words = []
    if input_path.endswith(".csv"):
        with open(input_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                w = row.get("word", "").strip()
                if not w:
                    continue
                freq = int(row.get("freq", row.get("frequency", 0)))
                length = int(row.get("length", 0))
                words.append((w, freq, length))
    else:
        with open(input_path, mode="r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w and not w.startswith("#"):
                    words.append((w, 0, 0))
    return words


def run_ml_audit(
    words: List[Tuple[str, int, int]],
    batch_size: int = 100,
    carrier_template: str = "{word} நேற்று வந்தார்."
) -> Dict[str, any]:
    """Runs neural POS tagging on words embedded in carrier sentence contexts."""
    print("Initializing Stanford Stanza Tamil Neural Model...")
    nlp = stanza.Pipeline(
        lang="ta",
        processors="tokenize,pos",
        verbose=False,
        use_gpu=True
    )

    total_words = len(words)
    print(f"Auditing {total_words:,} words with Neural NLP Model...")

    flagged_proper_nouns = []
    common_nouns = []
    verbs = []
    other_pos = []

    start_time = time.time()

    # Process in batches for speed
    for i in range(0, total_words, batch_size):
        batch = words[i:i + batch_size]
        # Construct carrier sentences
        sentences = [carrier_template.format(word=w[0]) for w in batch]
        text_blob = "\n".join(sentences)

        doc = nlp(text_blob)

        for (word, freq, length), sent in zip(batch, doc.sentences):
            target_token = None
            for token in sent.words:
                if token.text == word:
                    target_token = token
                    break

            if target_token is None and len(sent.words) > 0:
                target_token = sent.words[0]

            upos = target_token.upos if target_token else "UNKNOWN"
            xpos = target_token.xpos if target_token else "UNKNOWN"

            record = {
                "word": word,
                "freq": freq,
                "length": length,
                "upos": upos,
                "xpos": xpos,
            }

            # Flag proper nouns (PROPN), adjectives (ADJ / JJ), oblique noun stems (NO), and non-noun POS
            is_excluded_pos = (
                upos in ("PROPN", "ADJ", "ADV", "PRON", "ADP", "SCONJ", "CCONJ", "PART", "NUM", "DET", "INTJ")
                or (xpos and xpos.startswith("NO"))
                or (xpos and xpos.startswith("JJ"))
            )

            if is_excluded_pos and word not in SAFE_COMMON_NOUNS:
                flagged_proper_nouns.append(record)
            elif upos == "NOUN":
                common_nouns.append(record)
            elif upos == "VERB":
                verbs.append(record)
            else:
                other_pos.append(record)

        processed = min(i + batch_size, total_words)
        pct = (processed / total_words) * 100
        print(f"  Progress: {processed:,} / {total_words:,} ({pct:.1f}%) | Flagged Proper Nouns: {len(flagged_proper_nouns)}", end="\r")

    elapsed = time.time() - start_time
    print(f"\nAudit completed in {elapsed:.2f}s!")

    return {
        "total": total_words,
        "elapsed_sec": elapsed,
        "proper_nouns": flagged_proper_nouns,
        "common_nouns": common_nouns,
        "verbs": verbs,
        "other_pos": other_pos,
    }


def generate_markdown_report(results: Dict[str, any], output_path: str, input_path: str):
    """Generates a detailed Markdown audit report."""
    proper_nouns = results["proper_nouns"]
    total = results["total"]
    elapsed = results["elapsed_sec"]

    lines = [
        "# Tamil Wordle - Machine Learning Proper Noun Audit Report",
        "",
        f"- **Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Input Dataset**: `{input_path}`",
        f"- **Engine**: Stanford Stanza Universal Dependencies (Tamil Neural Pipeline)",
        f"- **Total Words Audited**: {total:,}",
        f"- **Flagged Proper Nouns (`PROPN`)**: **{len(proper_nouns)}** ({len(proper_nouns)/total*100:.2f}%)",
        f"- **Common Nouns (`NOUN`)**: {len(results['common_nouns']):,}",
        f"- **Verbs (`VERB`)**: {len(results['verbs']):,}",
        f"- **Other POS**: {len(results['other_pos']):,}",
        f"- **Processing Time**: {elapsed:.2f} seconds",
        "",
        "---",
        "",
        "## Flagged Proper Nouns & Personal Names",
        "",
        "| # | Word | Frequency | Length | UPOS | XPOS Tag | Classification |",
        "|---|------|-----------|--------|------|----------|----------------|",
    ]

    for idx, item in enumerate(proper_nouns, 1):
        lines.append(
            f"| {idx} | **{item['word']}** | {item['freq']:,} | {item['length']} | `{item['upos']}` | `{item['xpos']}` | Proper Noun / Named Entity |"
        )

    lines.append("")
    lines.append("---")
    lines.append("*Generated by `data/audit_proper_nouns_ml.py`*")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✓ Markdown report written to: {output_path}")


# Whitelist of legitimate common nouns / verbal nouns
SAFE_COMMON_NOUNS = {
    'தமிழ்', 'அப்பா', 'அம்மா', 'மனிதன்', 'வாசல்', 'விளையாட்டு', 'முத்து', 'பட்டம்', 'களம்', 'ஆளுமை',
    'அன்பு', 'மருந்து', 'முதலீடு', 'உண்மை', 'பாடல்', 'செயல்', 'பதவி', 'உரிமை', 'கூடுதல்', 'உறுதி',
    'தொடர்', 'அவசியம்', 'மாற்றம்', 'கடல்', 'சதவீதம்', 'ஆதரவு', 'பிரிவு', 'அதிபர்', 'நிச்சயம்', 'நடிகை',
    'தமிழர்', 'உயிரியல்', 'உரையாடல்', 'சமயம்', 'நிர்வாகம்', 'நெருப்பு', 'வருடம்', 'திறன்', 'தெற்கு',
    'நினைவு', 'வீரர்', 'தகுதி', 'சூழல்', 'ஆணையம்', 'வானியல்', 'மகளிர்', 'பயணிகள்', 'எண்ணெய்', 'பேச்சு',
    'நிகழ்ச்சி', 'வீரர்கள்', 'வேண்டுகோள்', 'சொற்கள்', 'ஏற்பாடு', 'எண்கள்', 'படங்கள்', 'குழுக்கள்', 'சுற்றி',
    'முன்னர்', 'இவ்வளவு', 'சாப்பாடு', 'அரசு', 'மக்கள்', 'காதல்', 'ஆண்டு', 'அறிவியல்', 'மூலம்', 'சிறப்பு',
    'கடிதம்', 'அரசியல்', 'குடும்பம்', 'இயற்கை', 'சமூகம்', 'பண்பாடு', 'வரலாறு', 'புத்தகம்', 'தலைவர்',
    'தோற்றம்', 'வளர்ச்சி', 'எழுத்து', 'பயன்பாடு', 'உணர்வு', 'நம்பிக்கை', 'காரணம்', 'நோக்கம்', 'கருத்து',
    'அறிவு', 'பார்வை', 'முடிவு', 'நிலைமை', 'வாழ்க்கை', 'உலகம்', 'உயிரினம்', 'விலங்கு', 'பறவை', 'மரம்',
    'செடி', 'மலர்', 'காடு', 'மலை', 'ஆறு', 'குளம்', 'வானம்', 'காற்று', 'நீர்', 'நிலம்', 'நெருப்பு',
    'காலம்', 'பருவம்', 'பகல்', 'இரவு', 'காலை', 'மாலை', 'உணவு', 'நீர்', 'வீடு', 'ஊர்', 'நகரம்',
    'நாடு', 'மொழி', 'இனம்', 'மதம்', 'கலை', 'இசை', 'நாட்டியம்', 'கூத்து', 'ஓவியம்', 'சிற்பம்',
    'தொழில்', 'வணிகம்', 'வேளாண்மை', 'கல்வி', 'பள்ளி', 'கல்லூரி', 'நூல்', 'ஏடு', 'கவிதை', 'கட்டுரை',
    'செந்தமிழ்', 'தமிழன்', 'தமிழகம்', 'குடும்ப', 'மனித'
}


SAFE_COMMON_NOUNS.update(KNOWN_BASE_NOUNS)
SAFE_COMMON_NOUNS.update(CORE_TAMIL_BASE_NOUNS)

def export_ml_excluded_gazetteer(proper_nouns: List[Dict], output_path: str):
    """Exports clean, non-whitelisted proper names/entities to a gazetteer file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    names = sorted({r["word"] for r in proper_nouns if r["word"] not in SAFE_COMMON_NOUNS})
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Tamil Wordle - ML Neural Model Flagged Proper Names & Entities\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for name in names:
            f.write(f"{name}\n")
    print(f"✓ ML Proper Nouns Gazetteer ({len(names)} entities) written to: {output_path}")


def export_flagged_csv(proper_nouns: List[Dict], output_path: str):
    """Exports flagged proper nouns to a CSV file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["word", "freq", "length", "upos", "xpos"])
        writer.writeheader()
        for r in proper_nouns:
            writer.writerow(r)
    print(f"✓ Flagged CSV written to: {output_path}")


def auto_append_to_gazetteer(proper_nouns: List[Dict], gazetteer_path: str):
    """Appends flagged names to the gazetteer file."""
    existing = set()
    if os.path.exists(gazetteer_path):
        with open(gazetteer_path, "r", encoding="utf-8") as f:
            existing = {line.strip() for line in f if line.strip() and not line.startswith("#")}

    new_names = [r["word"] for r in proper_nouns if r["word"] not in existing and r["word"] not in SAFE_COMMON_NOUNS]
    if not new_names:
        print("No new names to append to gazetteer.")
        return 0

    with open(gazetteer_path, "a", encoding="utf-8") as f:
        f.write(f"\n# --- ML Neural Model Flagged Names ({time.strftime('%Y-%m-%d')}) ---\n")
        for name in sorted(new_names):
            f.write(f"{name}\n")

    print(f"✓ Appended {len(new_names)} new proper names to {gazetteer_path}")
    return len(new_names)


def main():
    parser = argparse.ArgumentParser(description="Tamil Wordle ML-Assisted Proper Noun Audit")
    parser.add_argument(
        "--input", "-i",
        default="/Users/kokulapalan/projects/tamilwordle/data/top_1500_filtered_words.csv",
        help="Input CSV or TXT file with words to audit"
    )
    parser.add_argument(
        "--output-report", "-r",
        default="/Users/kokulapalan/projects/tamilwordle/data/ml_audit_report.md",
        help="Path to output Markdown audit report"
    )
    parser.add_argument(
        "--output-csv", "-c",
        default="/Users/kokulapalan/projects/tamilwordle/data/ml_flagged_proper_nouns.csv",
        help="Path to output flagged CSV"
    )
    parser.add_argument(
        "--output-gazetteer",
        default="/Users/kokulapalan/projects/tamilwordle/data/ml_excluded_proper_nouns.txt",
        help="Path to output ML-generated exclusion gazetteer file"
    )
    parser.add_argument(
        "--gazetteer", "-g",
        default="/Users/kokulapalan/projects/tamilwordle/data/tamil_proper_names_gazetteer.txt",
        help="Path to Tamil proper names gazetteer"
    )
    parser.add_argument(
        "--auto-append",
        action="store_true",
        help="Automatically append flagged proper names to gazetteer and rebuild dictionary"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=0,
        help="Limit number of words to audit (0 for all)"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=50,
        help="Batch size for neural evaluation"
    )

    args = parser.parse_args()

    words = load_input_words(args.input)
    if args.limit and args.limit > 0:
        words = words[:args.limit]
    if not words:
        print(f"Error: No words found in {args.input}")
        sys.exit(1)

    results = run_ml_audit(words, batch_size=args.batch_size)

    generate_markdown_report(results, args.output_report, args.input)
    export_flagged_csv(results["proper_nouns"], args.output_csv)
    export_ml_excluded_gazetteer(results["proper_nouns"], args.output_gazetteer)

    if args.auto_append:
        added_count = auto_append_to_gazetteer(results["proper_nouns"], args.gazetteer)
        if added_count > 0:
            pipeline_script = os.path.join(os.path.dirname(args.gazetteer), "run_pipeline.sh")
            if os.path.exists(pipeline_script):
                print("Re-running filtering pipeline with updated gazetteer...")
                os.system(f"bash {pipeline_script}")


if __name__ == "__main__":
    main()
