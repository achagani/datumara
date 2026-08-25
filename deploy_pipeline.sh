#!/bin/bash
# Complete deployment pipeline: export, test, and prepare for distribution

set -e

echo "🚀 Datumara Full Deployment Pipeline"
echo "===================================="
echo ""

# Step 1: Export to Ollama
echo "Step 1: Exporting to Ollama format..."
./export_to_ollama_full.sh
echo ""

# Step 2: Run comprehensive tests
echo "Step 2: Running comprehensive SQL tests..."
./test_datumara.sh datumara-local
echo ""

# Step 3: Generate model card
echo "Step 3: Generating model card..."
cat > models/MODEL_CARD.md << 'EOF'
# Datumara Local

## Model Details

- **Base Model**: TinyLlama 1.1B Chat
- **Training**: LoRA fine-tuning with checkpointing
- **Architecture**: Decoder-only transformer
- **Parameters**: 1.1B (2.25M trainable with LoRA)
- **License**: MIT

## Training Data

- **Dataset**: Spider augmented (SQL + natural language questions)
- **Examples**: 7,000 training examples
- **Steps**: 2,000 training steps
- **Sequence Length**: 256 tokens
- **Checkpointing**: Every 100 steps with best model selection

## Capabilities

Datumara Local is designed for:
- Generating SQL queries from natural language questions
- Schema-aware query generation
- Supporting analytical queries (aggregations, JOINs, filters)

## Usage

### With Ollama
```bash
ollama run datumara-local "Return only SQL: show all users"
```

### Example Queries
```bash
# Simple SELECT
ollama run datumara-local "Return only SQL: count orders by region"

# JOIN queries
ollama run datumara-local "Return only SQL: find top 10 customers by revenue"

# Aggregations
ollama run datumara-local "Return only SQL: calculate monthly revenue"
```

## Limitations

- Trained on SQLite syntax; may need adjustments for other databases
- Best for analytical queries; not optimized for transactional SQL
- 1.1B parameter size limits complex reasoning capabilities

## Hardware Requirements

- **Inference**: 4GB+ GPU or CPU with 8GB+ RAM
- **Training**: 4GB+ GPU with CUDA support

## Version History

### v0.1.0 (Initial Release)
- First checkpointed training run
- 2000 steps on TinyLlama 1.1B base
- LoRA fine-tuning with r=8, alpha=16

## Citation

```
@software{datumara2026,
  title = {Datumara: Open Analytics Intelligence},
  author = {Datumara Team},
  year = {2026},
  url = {https://github.com/achagani/datumara}
}
```

## Contact

- GitHub: https://github.com/achagani/datumara
- Website: https://achagani.github.io/datumara
EOF

echo "✅ Model card created: models/MODEL_CARD.md"
echo ""

# Step 4: Create deployment summary
echo "Step 4: Creating deployment summary..."
cat > models/DEPLOYMENT_SUMMARY.txt << EOF
Datumara Deployment Summary
===========================
Date: $(date)
Model: $OLLAMA_NAME

Files Created:
- models/datumara-local-merged/ (merged Hugging Face model)
- models/MODEL_CARD.md (model documentation)
- models/DEPLOYMENT_SUMMARY.txt (this file)

Ollama Model:
- Name: datumara-local
- Status: Ready for use
- Test Results: See test output above

Next Steps:
1. ✅ Model exported to Ollama
2. ✅ Tests completed
3. [ ] Optional: Publish to Ollama library (ollama push datumara-local)
4. [ ] Optional: Upload to Hugging Face Hub
5. [ ] Update install.sh if model name changed

Usage:
  ollama run datumara-local "Return only SQL: <your question>"

Installation for End Users:
  curl -fsSL https://raw.githubusercontent.com/achagani/datumara/main/install.sh | bash
EOF

echo "✅ Deployment summary created: models/DEPLOYMENT_SUMMARY.txt"
echo ""

echo "===================================="
echo "✅ Deployment Pipeline Complete!"
echo ""
echo "Your Datumara model is ready to use:"
echo "  ollama run datumara-local"
echo ""
echo "Documentation:"
echo "  models/MODEL_CARD.md"
echo "  models/DEPLOYMENT_SUMMARY.txt"
echo ""
