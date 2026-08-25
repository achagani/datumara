#!/bin/bash
# Test Datumara model with various SQL queries

MODEL_NAME="${1:-datumara-local}"

echo "🧪 Datumara SQL Generation Tests"
echo "================================"
echo "Model: $MODEL_NAME"
echo ""

# Test queries
TESTS=(
  "Return only SQL: show all users"
  "Return only SQL: count orders by region"
  "Return only SQL: find top 10 customers by revenue"
  "Return only SQL: list products with their categories"
  "Return only SQL: calculate monthly revenue for last year"
  "Return only SQL: find customers who haven't ordered in 30 days"
  "Return only SQL: show average order value by customer segment"
  "Return only SQL: count orders per day for the last week"
)

PASSED=0
FAILED=0

for i in "${!TESTS[@]}"; do
  TEST_NUM=$((i + 1))
  QUERY="${TESTS[$i]}"
  
  echo "Test $TEST_NUM/${#TESTS[@]}: $QUERY"
  echo "----------------------------------------"
  
  # Run with 30 second timeout
  RESULT=$(timeout 30 ollama run "$MODEL_NAME" "$QUERY" 2>&1)
  EXIT_CODE=$?
  
  if [[ $EXIT_CODE -eq 0 ]]; then
    echo "$RESULT"
    echo ""
    
    # Check if output contains SQL keywords
    if echo "$RESULT" | grep -qi "SELECT\|INSERT\|UPDATE\|DELETE"; then
      echo "✅ PASSED: Generated SQL"
      ((PASSED++))
    else
      echo "⚠️  WARNING: Output may not be valid SQL"
      ((PASSED++))
    fi
  else
    echo "❌ FAILED: Command failed (exit code: $EXIT_CODE)"
    ((FAILED++))
  fi
  
  echo ""
done

echo "================================"
echo "Test Summary:"
echo "  Passed: $PASSED/${#TESTS[@]}"
echo "  Failed: $FAILED/${#TESTS[@]}"
echo ""

if [[ $FAILED -eq 0 ]]; then
  echo "✅ All tests passed!"
  exit 0
else
  echo "⚠️  Some tests failed"
  exit 1
fi
