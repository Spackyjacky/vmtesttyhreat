#!/usr/bin/env bash
# Surfaces decisions flagged for review
# Usage: ./review.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$SCRIPT_DIR/.."
CSV="$BASE/data/decisions.csv"
FLAG="$BASE/data/review_due.txt"
TODAY=$(date +%Y-%m-%d)

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║        COMMAND CENTER — REVIEW DUE           ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

if [ ! -f "$CSV" ]; then
    echo "  No decisions.csv found."
    exit 0
fi

COUNT=0
while IFS=',' read -r date decision reasoning expected_outcome review_date status; do
    # Skip header
    [ "$date" = "date" ] && continue
    # Remove quotes if present
    review_date="${review_date//\"/}"
    status="${status//\"/}"
    decision="${decision//\"/}"
    if [ "$status" = "active" ] && [ "$review_date" \< "$TODAY" ] || [ "$review_date" = "$TODAY" ]; then
        echo "  ⚠  DATE: $date"
        echo "     DECISION: $decision"
        echo "     REVIEW DATE: $review_date"
        echo ""
        COUNT=$((COUNT+1))
    fi
done < "$CSV"

if [ "$COUNT" -eq 0 ]; then
    echo "  ✓  No decisions currently due for review."
else
    echo "  Total: $COUNT decision(s) due for review."
    echo ""
    echo "  Run the command center and go to Decisions to mark as reviewed."
fi
echo ""
