# Datumara v0.2-beta: 3-Day Sprint to Confidence

**Goal:** Prove we can generate valid SQL with cleaned data  
**Timeline:** 3 days (2026-08-25 to 2026-08-28)  
**Theme:** "Fast Validation, Not Perfection"

---

## Day 1: Data Cleaning (BLOCKING)

### Morning (9 AM - 12 PM)
**Task:** Run data cleaning pipeline on priority datasets

**Priority Order:**
1. ✅ **bird23_filtered** (6.6K) - Already pre-cleaned, start here
2. ✅ **mini_dev** (1.5K) - High quality, needed for evaluation
3. ⚠️ **bird_critic** (500) - Unique asset (bug→fix)
4. ⚠️ **effi_sql** (5.6K) - Unique asset (base→optimized)

**Script:** `data/acquire_and_clean.py`

**What to Do:**
```bash
cd /home/achagani/llm-analytics
source .venv/bin/activate

# Run cleaning on bird23_filtered first (fastest path to validation)
python data/acquire_and_clean.py --dataset bird23_filtered --output data/platinum/datumara_v02_train.parquet

# Then mini_dev (for evaluation)
python data/acquire_and_clean.py --dataset mini_dev --output data/platinum/datumara_v02_dev.parquet
```

**Success Criteria:**
- [ ] 6.6K examples cleaned and normalized
- [ ] Execution verification complete
- [ ] Schema consistency checked
- [ ] Output: `data/platinum/datumara_v02_train.parquet`

### Afternoon (1 PM - 6 PM)
**Task:** Quality analysis of cleaned data

**What to Do:**
```python
# Quick quality check
import pandas as pd
df = pd.read_parquet('data/platinum/datumara_v02_train.parquet')

print(f"Total examples: {len(df):,}")
print(f"Columns: {list(df.columns)}")
print(f"SQL length: mean={df['sql'].str.len().mean():.0f}, median={df['sql'].str.len().median():.0f}")
print(f"Sample: {df['question'].iloc[0]}")
print(f"SQL: {df['sql'].iloc[0]}")
```

**Success Criteria:**
- [ ] Column names normalized (question, sql, db_id)
- [ ] No NULL values in critical columns
- [ ] SQL looks reasonable (not truncated)
- [ ] Question-SQL pairs make sense (spot check 10 examples)

### Evening (7 PM - 9 PM)
**Task:** Prepare training data format

**What to Do:**
- Convert to JSONL format (if needed by training script)
- Create train/dev split (80/20)
- Verify format matches training script expectations

**Deliverable:** Ready-to-train dataset

---

## Day 2: Training Launch (CRITICAL)

### Morning (9 AM - 12 PM)
**Task:** Update training script with improvements

**Improvements:**
1. ✅ **Mask prompt tokens** - Only train on SQL tokens
2. ✅ **Add validation loss** - Track train/val gap
3. ✅ **Save best checkpoint** - By validation loss

**Script:** `src/training/train_local_checkpoint.py`

**Changes Needed:**
```python
# Add validation tracking
val_loss = evaluate_on_validation_set(...)
print(f"Step {step}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

# Save best checkpoint
if val_loss < best_val_loss:
    best_val_loss = val_loss
    save_checkpoint('best_val_checkpoint')
```

### Afternoon (1 PM - 6 PM)
**Task:** Launch training

**Command:**
```bash
cd /home/achagani/llm-analytics
source .venv/bin/activate

# Train on cleaned data (3000 steps)
python src/training/train_local_checkpoint.py \
  --data_path data/platinum/datumara_v02_train.parquet \
  --eval_data_path data/platinum/datumara_v02_dev.parquet \
  --output_dir models/local-tinyllama-lora-v0.2 \
  --steps 3000 \
  --batch_size 4 \
  --lr 2e-4 \
  --save_every 100 \
  --eval_every 50
```

**Monitor:**
```bash
# Watch training progress
tail -f models/local-tinyllama-lora-v0.2/training_progress.jsonl

# Or use monitoring script
bash scripts/training/monitor_training.sh
```

**Success Criteria:**
- [ ] Training starts without errors
- [ ] Loss decreases in first 100 steps
- [ ] Validation loss tracked
- [ ] Checkpoints saved every 100 steps

### Evening (7 PM - 9 PM)
**Task:** Monitor initial training progress

**What to Look For:**
- Initial loss: Should start around 2.0-2.5
- After 100 steps: Should drop to ~1.5
- After 500 steps: Should drop to ~0.5
- Train-val gap: Should be <0.1 (if larger, overfitting)

**If Problems:**
- Loss not decreasing: Check learning rate, data format
- Loss NaN: Check for NULL values in data
- OOM error: Reduce batch size

---

## Day 3: Quick Evaluation (CONFIDENCE CHECK)

### Morning (9 AM - 12 PM)
**Task:** Create evaluation script

**Script:** `scripts/evaluation/quick_eval_v02.py`

**What to Test:**
```python
# Load v0.2 model
model_v02 = load_model('models/local-tinyllama-lora-v0.2')

# Test on 20 examples from Mini-Dev
test_questions = [...]  # From mini_dev dataset
expected_sql = [...]  # Ground truth

results = []
for question, expected in zip(test_questions, expected_sql):
    generated = model_v02.generate(question)
    results.append({
        'question': question,
        'expected': expected,
        'generated': generated,
        'exact_match': generated.strip() == expected.strip(),
        'valid_sql': is_valid_sql(generated),  # Try to parse
        'executes': executes_on_db(generated, db_id),  # Try to run
    })

# Calculate metrics
print(f"Exact Match: {sum(r['exact_match'] for r in results)/len(results)*100:.1f}%")
print(f"Valid SQL: {sum(r['valid_sql'] for r in results)/len(results)*100:.1f}%")
print(f"Executes: {sum(r['executes'] for r in results)/len(results)*100:.1f}%")
```

### Afternoon (1 PM - 4 PM)
**Task:** Run evaluation

**Success Criteria (v0.2-beta target):**
- ✅ **SQL Validity ≥60%** (up from <10% in v0.1)
- ✅ **Execution Accuracy ≥40%** (up from 0% in v0.1)
- ✅ **Exact Match ≥30%** (baseline)

**If We Hit These:** 🎉 CONFIDENT! Move to full evaluation
**If We Miss:** 🔍 Analyze failures, adjust approach

### Afternoon (4 PM - 6 PM)
**Task:** Compare v0.1 vs v0.2

**Side-by-Side Test:**
```python
# Same 20 questions, both models
results_v01 = evaluate(model_v01, test_questions)
results_v02 = evaluate(model_v02, test_questions)

print("v0.1 Valid SQL: {:.1f}%".format(results_v01['valid_sql']))
print("v0.2 Valid SQL: {:.1f}%".format(results_v02['valid_sql']))
print("Improvement: {:.1f}x".format(results_v02['valid_sql'] / results_v01['valid_sql']))
```

**Expected:** 3-6x improvement (from <10% to 50-60%)

### Evening (7 PM - 9 PM)
**Task:** Decision Point

**Questions to Answer:**
1. ✅ Did cleaned data improve SQL validity?
2. ✅ Is the model generating schema-grounded SQL?
3. ✅ Are we confident to proceed with full v0.2-beta plan?

**If YES:** Continue with full 7-day plan
**If NO:** Pivot (try larger model, add schema grounding, etc.)

---

## Risk Mitigation

### Risk 1: Data cleaning takes too long
**Fallback:** Use only bird23_filtered (6.6K) for initial validation
- Already pre-filtered
- Higher quality than full BIRD
- Faster to process

### Risk 2: Training doesn't converge
**Fallback:** 
- Use same config as v0.1 (proven to work)
- Reduce steps to 1000 (faster iteration)
- Check data format matches v0.1

### Risk 3: No improvement over v0.1
**Fallback:**
- Analyze failure modes (schema? complexity? domain?)
- Try curriculum learning (simple → complex)
- Consider larger model (7B instead of 1.1B)

---

## Definition of Done (Day 3)

**We have confidence when:**
- [ ] Model generates valid SQL on 60%+ of test queries
- [ ] SQL executes on target database (40%+ execution accuracy)
- [ ] Clear improvement over v0.1 (3x+ better)
- [ ] Training stable (loss decreases smoothly)
- [ ] No major failure modes identified

**If All Boxes Checked:** ✅ Proceed with full v0.2-beta plan (7 days total)
**If Some Boxes Missing:** 🔧 Adjust plan, extend timeline

---

## Daily Checkpoints

### End of Day 1:
- [ ] Cleaned dataset ready (6.6K+ examples)
- [ ] Quality verified (spot check 10 examples)
- [ ] Format ready for training

### End of Day 2:
- [ ] Training launched successfully
- [ ] Loss decreasing (check at step 100, 500)
- [ ] Checkpoints saving properly

### End of Day 3:
- [ ] Evaluation complete (20+ test queries)
- [ ] Metrics calculated (validity, execution, exact match)
- [ ] v0.1 vs v0.2 comparison
- [ ] GO/NO-GO decision for full plan

---

**Theme:** Fast validation, not perfection  
**Goal:** Confidence in 3 days  
**Success:** 60%+ SQL validity
