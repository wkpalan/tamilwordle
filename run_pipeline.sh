#!/usr/bin/env bash
# ==============================================================================
# Tamil Wordle - Complete Word Filtering & JSON Asset Generation Pipeline
# ==============================================================================
# This script executes the entire data filtering workflow:
#  1. Compiles the Tamil proper names & entities gazetteer.
#  2. Runs 14 linguistic morphology unit test suites to ensure 0 regressions.
#  3. Streams and filters the 4.59M frequency dataset into target base nouns & verbs.
#  4. Runs ML Neural Audit (Stanford Stanza) to identify proper names & entities.
#  5. Generates pristine Wordle game JSON assets:
#     - frontend/public/top_words.json
#     - frontend/public/words.json
#     - frontend/public/words_3.json
#     - frontend/public/words_4.json
#     - frontend/public/words_5.json
#  6. Validates the frontend build with Vite.
# ==============================================================================

set -e

# ANSI Color Codes
GREEN="\033[1;32m"
BLUE="\033[1;34m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RED="\033[1;31m"
RESET="\033[0m"

START_TIME=$(date +%s)

# Directory Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
if [[ "$(basename "$SCRIPT_DIR")" == "data" ]]; then
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
fi

DATA_DIR="$PROJECT_ROOT/data"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
PUBLIC_DIR="$FRONTEND_DIR/public"

# Python Environment
PYTHON_BIN="/Users/kokulapalan/mamba/envs/tamilwordle/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

echo -e "${CYAN}======================================================${RESET}"
echo -e "${CYAN}   Tamil Wordle - Two-Pass ML Hybrid Pipeline        ${RESET}"
echo -e "${CYAN}======================================================${RESET}"
echo -e "${BLUE}Project Root:${RESET} $PROJECT_ROOT"
echo -e "${BLUE}Python Env:${RESET}   $PYTHON_BIN"
echo -e "${BLUE}Data Dir:${RESET}     $DATA_DIR"
echo -e "${BLUE}Public Dir:${RESET}   $PUBLIC_DIR"
echo ""

# ------------------------------------------------------------------------------
# Step 1: Compile Tamil Proper Names Gazetteer
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[1/6] Compiling Tamil Proper Names & Entities Gazetteer...${RESET}"
"$PYTHON_BIN" "$DATA_DIR/build_tamil_gazetteer.py"
echo -e "${GREEN}✓ Gazetteer successfully compiled: data/tamil_proper_names_gazetteer.txt${RESET}"
echo ""

# ------------------------------------------------------------------------------
# Step 2: Run Linguistic Morphology Unit Tests
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[2/6] Running Linguistic Morphology Unit Tests (14 suites)...${RESET}"
"$PYTHON_BIN" "$DATA_DIR/test_tamil_morphology.py"
echo -e "${GREEN}✓ All 14 unit test suites passed with 0 failures!${RESET}"
echo ""

# ------------------------------------------------------------------------------
# Step 3: Execute Pass 1 Word Filtering Pipeline
# ------------------------------------------------------------------------------
INPUT_CSV="$DATA_DIR/aviiciii-tamil-words-frequency.csv"
OUTPUT_CSV="$DATA_DIR/filtered_tamil_words.csv"
TOP_1500_CSV="$DATA_DIR/top_1500_filtered_words.csv"
TOP_WORDS_JSON="$PUBLIC_DIR/top_words.json"

if [ ! -f "$INPUT_CSV" ]; then
    echo -e "${RED}Error: Master dataset not found at $INPUT_CSV${RESET}"
    exit 1
fi

echo -e "${YELLOW}[3/6] Pass 1: Streaming & Filtering 4.59M Frequency Dataset...${RESET}"
"$PYTHON_BIN" "$DATA_DIR/filter_words_pipeline.py" \
    --input "$INPUT_CSV" \
    --output "$OUTPUT_CSV" \
    --top-n 3500 \
    --top-n-output "$TOP_1500_CSV" \
    --lengths 3,4,5 \
    --min-freq 2 \
    --mode keep \
    --export-game-json "$TOP_WORDS_JSON"

echo -e "${GREEN}✓ Pass 1 complete: Initial candidate pool generated.${RESET}"
echo ""

# ------------------------------------------------------------------------------
# Step 4: ML Neural Audit & Proper Nouns Exclusion (Stanford Stanza)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[4/6] Pass 2: Running ML Neural Named Entity & POS Audit...${RESET}"
"$PYTHON_BIN" "$DATA_DIR/audit_proper_nouns_ml.py" \
    --input "$TOP_1500_CSV" \
    --output-report "$DATA_DIR/ml_audit_report.md" \
    --output-csv "$DATA_DIR/ml_flagged_proper_nouns.csv" \
    --output-gazetteer "$DATA_DIR/ml_excluded_proper_nouns.txt"

echo -e "${GREEN}✓ ML Named Entity Audit complete: ml_excluded_proper_nouns.txt updated.${RESET}"
echo ""

# ------------------------------------------------------------------------------
# Step 5: Final Clean Asset Generation
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[5/6] Final Pass: Applying ML Gazetteer & Regenerating Clean Assets...${RESET}"
"$PYTHON_BIN" "$DATA_DIR/filter_words_pipeline.py" \
    --input "$INPUT_CSV" \
    --output "$OUTPUT_CSV" \
    --top-n 1500 \
    --top-n-output "$TOP_1500_CSV" \
    --lengths 3,4,5 \
    --min-freq 2 \
    --mode keep \
    --export-game-json "$TOP_WORDS_JSON"

echo -e "${GREEN}✓ Pristine filtered dictionary & Top 1,500 CSV generated!${RESET}"
echo ""

# ------------------------------------------------------------------------------
# Step 6: Verify Generated Game JSON Assets & Build Frontend
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[6/6] Verifying Generated Game JSON Assets & Building Frontend...${RESET}"

for f in "top_words.json" "words.json" "words_3.json" "words_4.json" "words_5.json"; do
    FILEPATH="$PUBLIC_DIR/$f"
    if [ -f "$FILEPATH" ]; then
        SIZE=$(du -h "$FILEPATH" | cut -f1)
        echo -e "  ${GREEN}✓${RESET} $f (${SIZE})"
    else
        echo -e "  ${RED}✗ Missing: $f${RESET}"
        exit 1
    fi
done

cd "$FRONTEND_DIR"
npm run build
cd "$PROJECT_ROOT"
echo -e "${GREEN}✓ Frontend production bundle compiled cleanly!${RESET}"
echo ""

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo -e "${CYAN}======================================================${RESET}"
echo -e "${GREEN} Hybrid Pipeline Completed Successfully in ${ELAPSED}s!${RESET}"
echo -e "${CYAN}======================================================${RESET}"
echo -e "Artifacts generated:"
echo -e "  1. Filtered Dictionary:  data/filtered_tamil_words.csv"
echo -e "  2. Top 1,500 Target:     data/top_1500_filtered_words.csv"
echo -e "  3. ML Audit Report:      data/ml_audit_report.md"
echo -e "  4. ML Excluded Names:    data/ml_excluded_proper_nouns.txt"
echo -e "  5. Master Game JSON:     frontend/public/top_words.json"
echo -e "  6. Fallback Game JSON:   frontend/public/words.json"
echo -e "  7. 3-Letter Words:       frontend/public/words_3.json"
echo -e "  8. 4-Letter Words:       frontend/public/words_4.json"
echo -e "  9. 5-Letter Words:       frontend/public/words_5.json"
echo ""
