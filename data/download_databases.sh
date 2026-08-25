#!/bin/bash
# Download BIRD databases for execution verification
# Based on: https://bird-bench.github.io/

set -e

echo "=========================================="
echo "Downloading BIRD Databases"
echo "=========================================="

# Create data directory
mkdir -p data/databases

cd data/databases

# Download BIRD databases (SQLite format)
# Note: These are the official BIRD benchmark databases

echo ""
echo "Downloading BIRD Train databases..."
if [ ! -f "bird_train_databases.zip" ]; then
    # Using the official HuggingFace URL
    wget -q --show-progress "https://huggingface.co/datasets/birdsql/bird_sql_train/resolve/main/bird_train_databases.zip" -O bird_train_databases.zip
    echo "✓ Downloaded train databases"
else
    echo "✓ Train databases already downloaded"
fi

echo ""
echo "Downloading BIRD Dev databases..."
if [ ! -f "bird_dev_databases.zip" ]; then
    wget -q --show-progress "https://huggingface.co/datasets/birdsql/bird_sql_dev/resolve/main/bird_dev_databases.zip" -O bird_dev_databases.zip
    echo "✓ Downloaded dev databases"
else
    echo "✓ Dev databases already downloaded"
fi

# Extract databases
echo ""
echo "Extracting databases..."

if [ -f "bird_train_databases.zip" ]; then
    unzip -q -o bird_train_databases.zip -d train_databases
    echo "✓ Extracted train databases"
fi

if [ -f "bird_dev_databases.zip" ]; then
    unzip -q -o bird_dev_databases.zip -d dev_databases
    echo "✓ Extracted dev databases"
fi

# Count databases
train_count=$(find train_databases -name "*.sqlite" | wc -l)
dev_count=$(find dev_databases -name "*.sqlite" | wc -l)

echo ""
echo "=========================================="
echo "Download Complete!"
echo "=========================================="
echo "Train databases: $train_count"
echo "Dev databases:   $dev_count"
echo "Location:        data/databases/"
echo ""

# Move to standard location
if [ -d "train_databases" ]; then
    mv train_databases/* . 2>/dev/null || true
    rm -rf train_databases
fi

if [ -d "dev_databases" ]; then
    mv dev_databases/* . 2>/dev/null || true
    rm -rf dev_databases
fi

echo "Databases organized in: data/databases/"
echo ""
echo "Next step: Run data/acquire_and_clean.py"
