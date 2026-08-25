#!/bin/bash
# Datumara Complete Evaluation Pipeline
# 
# This script:
# 1. Downloads BIRD databases (if not present)
# 2. Generates predictions from multiple models
# 3. Executes queries side-by-side
# 4. Generates comparison report
#
# Usage:
#   bash evaluate_all.sh
#   bash evaluate_all.sh --test-set mini_dev

set -e

# Configuration
TEST_SET=${1:-"mini_dev"}
OUTPUT_DIR="results/evaluation_$(date +%Y%m%d_%H%M%S)"
DB_PATH="data/databases"
PREDICTIONS_DIR="predictions"

echo "=============================================================================="
echo "Datumara Complete Evaluation Pipeline"
echo "=============================================================================="
echo "Test Set: $TEST_SET"
echo "Output Directory: $OUTPUT_DIR"
echo "Database Path: $DB_PATH"
echo "Predictions Directory: $PREDICTIONS_DIR"
echo ""

# Step 1: Download databases if not present
echo "=============================================================================="
echo "Step 1: Checking/Downloading BIRD Databases"
echo "=============================================================================="

if [ ! -d "$DB_PATH/train_databases" ] || [ ! -d "$DB_PATH/dev_databases" ]; then
    echo "Databases not found. Downloading..."
    python data/download_bird_databases.py --output-dir $DB_PATH
else
    echo "✓ Databases already downloaded"
    ls -lh $DB_PATH/
fi

# Step 2: Generate predictions from models
echo "=============================================================================="
echo "Step 2: Generating Model Predictions"
echo "=============================================================================="

mkdir -p $PREDICTIONS_DIR

# Generate predictions for v0.1-alpha
echo "Generating predictions for Datumara v0.1-alpha..."
mkdir -p $PREDICTIONS_DIR/datumara_v0.1_alpha
python generate_predictions.py \
    --model "datumara-local" \
    --test-set $TEST_SET \
    --output $PREDICTIONS_DIR/datumara_v0.1_alpha/predictions.json

# Generate predictions for v0.2-beta (if available)
if [ -f "models/datumara-v0.2-beta/model.safetensors" ]; then
    echo "Generating predictions for Datumara v0.2-beta..."
    mkdir -p $PREDICTIONS_DIR/datumara_v0.2_beta
    python generate_predictions.py \
        --model "datumara-local-v0.2" \
        --test-set $TEST_SET \
        --output $PREDICTIONS_DIR/datumara_v0.2_beta/predictions.json
else
    echo "⚠ v0.2-beta model not found, skipping..."
fi

# Generate predictions for baselines (optional)
echo "Generating baseline predictions (GPT-4, etc.)..."
# This would require API keys, so we'll skip for now
# mkdir -p $PREDICTIONS_DIR/gpt4_baseline
# python generate_predictions.py --model "gpt-4" --test-set $TEST_SET --output $PREDICTIONS_DIR/gpt4_baseline/predictions.json

# Step 3: Run evaluation
echo "=============================================================================="
echo "Step 3: Running Side-by-Side Evaluation"
echo "=============================================================================="

python evaluate_models.py \
    --test-set "data/bird_raw/${TEST_SET}.parquet" \
    --db-path $DB_PATH \
    --predictions-dir $PREDICTIONS_DIR \
    --output $OUTPUT_DIR/comparison.json

# Step 4: Generate visual report
echo "=============================================================================="
echo "Step 4: Generating Visual Report"
echo "=============================================================================="

python -c "
import pandas as pd
import json

# Load results
with open('$OUTPUT_DIR/comparison.json', 'r') as f:
    results = json.load(f)

# Create comparison table
print('\n' + '='*80)
print('EXECUTION ACCURACY COMPARISON')
print('='*80)
print(results['comparison_table'].to_string(index=False))

# Save as CSV
results['comparison_table'].to_csv('$OUTPUT_DIR/comparison.csv', index=False)
print(f'\n✓ CSV saved to $OUTPUT_DIR/comparison.csv')
"

# Step 5: Display summary
echo "=============================================================================="
echo "Evaluation Complete!"
echo "=============================================================================="
echo ""
echo "Results saved to:"
echo "  - JSON: $OUTPUT_DIR/comparison.json"
echo "  - CSV: $OUTPUT_DIR/comparison.csv"
echo "  - Markdown: $OUTPUT_DIR/comparison.md"
echo ""
echo "Next steps:"
echo "  1. Review $OUTPUT_DIR/comparison.md for detailed analysis"
echo "  2. Compare against BIRD leaderboard: https://bird-bench.github.io/"
echo "  3. Submit to leaderboard if results are competitive"
echo ""

# Optional: Submit to BIRD leaderboard
read -p "Submit results to BIRD leaderboard? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Preparing submission package..."
    python prepare_bird_submission.py --results $OUTPUT_DIR/comparison.json
fi
