#!/bin/bash
# Quick check of training status

NOTIFY_FILE="/tmp/training_notification.txt"
PROGRESS_FILE="models/local-tinyllama-checkpoint/training_progress.jsonl"

echo "📊 Datumara Training Status"
echo "=========================="
echo ""

# Check for notifications
if [[ -f "$NOTIFY_FILE" ]] && [[ -s "$NOTIFY_FILE" ]]; then
    echo "🔔 NOTIFICATION:"
    cat "$NOTIFY_FILE"
    echo ""
    echo "=========================="
    echo ""
fi

# Current progress
if [[ -f "$PROGRESS_FILE" ]]; then
    LAST_LINE=$(tail -1 "$PROGRESS_FILE")
    STEP=$(echo "$LAST_LINE" | jq -r '.step // 0')
    LOSS=$(echo "$LAST_LINE" | jq -r '.loss // 0')
    ELAPSED=$(echo "$LAST_LINE" | jq -r '.elapsed_seconds // 0')
    
    echo "Current Progress:"
    echo "  Step: $STEP/2000"
    echo "  Loss: $LOSS"
    echo "  Elapsed: $(printf '%dm %ds' $((${ELAPSED%.*}/60)) $((${ELAPSED%.*}%60)))"
    
    # Check checkpoints
    CHECKPOINT_DIR="models/local-tinyllama-checkpoint/checkpoints"
    if [[ -d "$CHECKPOINT_DIR" ]]; then
        CHECKPOINTS=$(ls -1 "$CHECKPOINT_DIR" 2>/dev/null | grep checkpoint_ | wc -l)
        echo "  Checkpoints saved: $CHECKPOINTS"
    fi
else
    echo "Training not started or progress file not found"
fi

echo ""
echo "Monitor log: /tmp/training_monitor.log"
echo "Notification file: $NOTIFY_FILE"
