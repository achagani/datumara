#!/bin/bash
# Quick test export of current checkpoint to Ollama

set -e

echo "🧪 Datumara Checkpoint Test Export"
echo "=================================="
echo ""

# Find the latest checkpoint
CHECKPOINT_DIR=$(ls -td models/local-tinyllama-checkpoint/checkpoints/checkpoint_* | head -1)
CHECKPOINT_NAME=$(basename "$CHECKPOINT_DIR")

if [[ -z "$CHECKPOINT_DIR" ]]; then
    echo "❌ No checkpoints found!"
    exit 1
fi

echo "Latest checkpoint: $CHECKPOINT_NAME"
echo ""

# Create temporary export directory
TEST_EXPORT_DIR="models/test-checkpoint-export"
rm -rf "$TEST_EXPORT_DIR"
mkdir -p "$TEST_EXPORT_DIR"

# Get base model name
BASE_MODEL="TinyLlama/TinyLlama-1.1B-Chat-v1.0"

echo "Step 1: Merging checkpoint with base model..."
# Use Python to merge LoRA weights
source .venv/bin/activate
python3 << PYTHON_EOF
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

checkpoint_dir = "$CHECKPOINT_DIR"
base_model = "$BASE_MODEL"
output_dir = "$TEST_EXPORT_DIR"

print(f"Loading base model: {base_model}")
model = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.float16,
    device_map="cpu",
    trust_remote_code=True
)

print(f"Loading LoRA checkpoint: {checkpoint_dir}")
model = PeftModel.from_pretrained(model, checkpoint_dir)

print("Merging weights...")
model = model.merge_and_unload()

print(f"Saving merged model to: {output_dir}")
model.save_pretrained(output_dir)

# Also save tokenizer
tokenizer = AutoTokenizer.from_pretrained(base_model)
tokenizer.save_pretrained(output_dir)

print("✅ Model merged and saved!")
PYTHON_EOF

echo ""
echo "Step 2: Creating Ollama Modelfile..."
cat > "$TEST_EXPORT_DIR/Modelfile" << 'EOF'
FROM .
PARAMETER temperature 0.1
PARAMETER top_p 0.9
SYSTEM """You are Datumara, an analytics AI assistant. Generate SQL queries from natural language questions. 
- Return ONLY the SQL query, no explanations
- Use proper SQL syntax (SELECT, FROM, WHERE, GROUP BY, ORDER BY, etc.)
- Assume SQLite dialect
- Keep queries concise and efficient
- Use appropriate JOINs when multiple tables are involved
- Include WHERE clauses for date filters when relevant
"""
EOF
echo "✅ Modelfile created"
echo ""

# Create Ollama model
MODEL_NAME="datumara-test"
echo "Step 3: Creating Ollama model '$MODEL_NAME'..."
cd "$TEST_EXPORT_DIR"
ollama create "$MODEL_NAME" -f Modelfile
cd - > /dev/null
echo "✅ Model created successfully"
echo ""

# Test the model
echo "Step 4: Testing model with sample queries..."
echo ""

TEST_QUERIES=(
  "Return only SQL: show all users"
  "Return only SQL: count orders by region"
  "Return only SQL: top 5 customers by revenue"
)

for QUERY in "${TEST_QUERIES[@]}"; do
  echo "Query: $QUERY"
  echo "----------------------------------------"
  RESULT=$(timeout 30 ollama run "$MODEL_NAME" "$QUERY" 2>&1)
  if [[ $? -eq 0 ]]; then
    echo "$RESULT"
    echo ""
  else
    echo "⚠️  Timeout or error (this is expected for test models)"
    echo ""
  fi
done

echo "=================================="
echo "✅ Test export complete!"
echo ""
echo "Model name: $MODEL_NAME"
echo "Location: $TEST_EXPORT_DIR"
echo ""
echo "To test manually:"
echo "  ollama run $MODEL_NAME \"Return only SQL: your question\""
echo ""
echo "To delete after testing:"
echo "  ollama rm $MODEL_NAME"
echo "  rm -rf $TEST_EXPORT_DIR"
