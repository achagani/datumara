#!/bin/bash
# Smart training monitor - only alerts on important events
# Runs in background and notifies when training completes or fails

PROGRESS_FILE="models/local-tinyllama-checkpoint/training_progress.jsonl"
CHECKPOINT_DIR="models/local-tinyllama-checkpoint/checkpoints"
NOTIFY_FILE="/tmp/training_notification.txt"

echo "🔍 Smart training monitor started"
echo "Will notify when:"
echo "  - Training completes (step 2000)"
echo "  - First checkpoint saved (step 100)"
echo "  - Training fails or stops"
echo ""

LAST_STEP=0
FIRST_CHECKPOINT_FOUND=false

while true; do
    if [[ -f "$PROGRESS_FILE" ]]; then
        # Get latest step
        CURRENT_STEP=$(tail -1 "$PROGRESS_FILE" 2>/dev/null | jq -r '.step // 0')
        
        # Check if training completed
        if [[ $CURRENT_STEP -ge 2000 ]] && [[ $LAST_STEP -lt 2000 ]]; then
            echo "" > "$NOTIFY_FILE"
            echo "✅ TRAINING COMPLETED!" >> "$NOTIFY_FILE"
            echo "Step: $CURRENT_STEP/2000" >> "$NOTIFY_FILE"
            echo "Time: $(date)" >> "$NOTIFY_FILE"
            echo "" >> "$NOTIFY_FILE"
            echo "Next: Export to Ollama format" >> "$NOTIFY_FILE"
            echo "  python training/export_huggingface.py --adapter models/local-tinyllama-checkpoint/best_checkpoint --base-model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --output-dir models/datumara-local-merged" >> "$NOTIFY_FILE"
            echo "  python training/export_to_ollama.py --model-dir models/datumara-local-merged --name datumara-local" >> "$NOTIFY_FILE"
            echo "Notification: Training completed" | tee /dev/stderr
            break
        fi
        
        # Check for first checkpoint
        if [[ "$FIRST_CHECKPOINT_FOUND" = false ]] && [[ -d "$CHECKPOINT_DIR" ]]; then
            CHECKPOINT_COUNT=$(ls -1 "$CHECKPOINT_DIR" 2>/dev/null | grep checkpoint_ | wc -l)
            if [[ $CHECKPOINT_COUNT -gt 0 ]]; then
                FIRST_CHECKPOINT_FOUND=true
                echo "" > "$NOTIFY_FILE"
                echo "💾 FIRST CHECKPOINT SAVED!" >> "$NOTIFY_FILE"
                echo "Step: $CURRENT_STEP" >> "$NOTIFY_FILE"
                echo "Checkpoints: $CHECKPOINT_COUNT" >> "$NOTIFY_FILE"
                echo "Time: $(date)" >> "$NOTIFY_FILE"
                ls -lh "$CHECKPOINT_DIR" >> "$NOTIFY_FILE"
                echo "Notification: First checkpoint saved" | tee /dev/stderr
            fi
        fi
        
        # Check if training stopped unexpectedly
        if [[ $CURRENT_STEP -eq $LAST_STEP ]] && [[ $CURRENT_STEP -gt 0 ]] && [[ $CURRENT_STEP -lt 2000 ]]; then
            # Wait 30 seconds and check again
            sleep 30
            NEW_STEP=$(tail -1 "$PROGRESS_FILE" 2>/dev/null | jq -r '.step // 0')
            if [[ $NEW_STEP -eq $LAST_STEP ]]; then
                echo "" > "$NOTIFY_FILE"
                echo "⚠️  TRAINING MAY HAVE STOPPED" >> "$NOTIFY_FILE"
                echo "Last step: $CURRENT_STEP" >> "$NOTIFY_FILE"
                echo "Time: $(date)" >> "$NOTIFY_FILE"
                echo "Check terminal for errors" >> "$NOTIFY_FILE"
                echo "Notification: Training may have stopped" | tee /dev/stderr
                break
            fi
        fi
        
        LAST_STEP=$CURRENT_STEP
    else
        echo "Waiting for training to start..."
    fi
    
    # Check every 2 minutes (efficient polling)
    sleep 120
done
