#!/bin/bash
# Monitor training progress and checkpoint creation

CHECKPOINT_DIR="models/local-tinyllama-checkpoint/checkpoints"
PROGRESS_FILE="models/local-tinyllama-checkpoint/training_progress.jsonl"

echo "🔍 Monitoring Datumara training..."
echo ""

while true; do
    if [[ -f "$PROGRESS_FILE" ]]; then
        LAST_LINE=$(tail -1 "$PROGRESS_FILE")
        STEP=$(echo "$LAST_LINE" | jq -r '.step // 0')
        LOSS=$(echo "$LAST_LINE" | jq -r '.loss // 0')
        ELAPSED=$(echo "$LAST_LINE" | jq -r '.elapsed_seconds // 0')
        
        echo "📊 Step: $STEP | Loss: $LOSS | Elapsed: ${ELAPSED}s"
        
        if [[ -d "$CHECKPOINT_DIR" ]]; then
            CHECKPOINTS=$(ls -1 "$CHECKPOINT_DIR" 2>/dev/null | wc -l)
            if [[ $CHECKPOINTS -gt 0 ]]; then
                echo "💾 Checkpoints saved: $CHECKPOINTS"
                ls -lh "$CHECKPOINT_DIR" | grep checkpoint_ | awk '{print "   " $9 " (" $5 ")"}'
            fi
        fi
        
        # Check if training completed
        if [[ $STEP -ge 2000 ]]; then
            echo ""
            echo "✅ Training completed!"
            break
        fi
    else
        echo "⏳ Waiting for training to start..."
    fi
    
    sleep 30
done
