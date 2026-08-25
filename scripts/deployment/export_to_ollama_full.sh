#!/bin/bash
# Export trained checkpoint to Ollama format and test it

set -e

echo "🚀 Datumara Export Pipeline"
echo "=========================="
echo ""

# Configuration
CHECKPOINT_DIR="models/local-tinyllama-checkpoint/best_checkpoint"
MERGED_DIR="models/datumara-local-merged"
OLLAMA_NAME="datumara-local"

# Step 1: Check if best checkpoint exists
echo "Step 1: Checking for best checkpoint..."
if [[ ! -d "$CHECKPOINT_DIR" ]]; then
    echo "❌ Best checkpoint not found at $CHECKPOINT_DIR"
    echo ""
    echo "Looking for available checkpoints:"
    ls -lh models/local-tinyllama-checkpoint/checkpoints/ 2>/dev/null || echo "No checkpoints found"
    exit 1
fi
echo "✅ Best checkpoint found"
echo ""

# Step 2: Merge with base model
echo "Step 2: Merging best checkpoint with TinyLlama base model..."
echo "  This will download TinyLlama if not cached (~2.2GB)"
source venv/bin/activate
python training/export_huggingface.py \
  --adapter "$CHECKPOINT_DIR" \
  --base-model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --output-dir "$MERGED_DIR"
echo "✅ Merged model saved to $MERGED_DIR"
echo ""

# Step 3: Create Ollama model
echo "Step 3: Creating Ollama model..."
python training/export_to_ollama.py \
  --model-dir "$MERGED_DIR" \
  --name "$OLLAMA_NAME"
echo "✅ Ollama model created: $OLLAMA_NAME"
echo ""

# Step 4: Test the model
echo "Step 4: Testing the model with SQL queries..."
echo ""

echo "Test 1: Simple SELECT"
echo "-------------------"
ollama run "$OLLAMA_NAME" "Return only SQL: show all users"
echo ""

echo "Test 2: Aggregation query"
echo "-------------------------"
ollama run "$OLLAMA_NAME" "Return only SQL: count orders by region"
echo ""

echo "Test 3: JOIN query"
echo "------------------"
ollama run "$OLLAMA_NAME" "Return only SQL: find top 10 customers by revenue"
echo ""

# Step 5: Summary
echo "=========================="
echo "✅ Export complete!"
echo ""
echo "Model details:"
echo "  Name: $OLLAMA_NAME"
echo "  Base: TinyLlama 1.1B Chat"
echo "  Training: 2000 steps with checkpointing"
echo ""
echo "Usage:"
echo "  ollama run $OLLAMA_NAME"
echo ""
echo "To publish to Ollama library:"
echo "  ollama push $OLLAMA_NAME"
echo ""
