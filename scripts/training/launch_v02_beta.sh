#!/bin/bash
# Launch v0.2-beta training with prompt masking and validation tracking

set -e

echo "======================================================================"
echo "Datumara v0.2-beta Training Launch"
echo "======================================================================"
echo ""
echo "Configuration:"
echo "  - Training data: 12,688 cleaned examples"
echo "  - Validation data: 1,500 examples (mini_dev)"
echo "  - Prompt masking: ENABLED (train only on SQL tokens)"
echo "  - Validation tracking: Every 200 steps"
echo "  - Checkpointing: Every 100 steps"
echo "  - Max steps: 3,000"
echo "  - LoRA: r=8, alpha=32"
echo "  - Learning rate: 2e-4"
echo ""
echo "Starting training..."
echo ""

cd /home/achagani/llm-analytics
source .venv/bin/activate

python src/training/train_v02_beta.py \
    --max-steps 3000 \
    --max-length 512 \
    --checkpoint-every 100 \
    --val-every 200 \
    --keep-checkpoints 5

echo ""
echo "Training complete! Check models/datumara-v02-beta/ for outputs"
