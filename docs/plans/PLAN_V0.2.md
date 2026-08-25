# Datumara v0.2-beta Development Plan

**Version:** v0.2-beta  
**Target Date:** 2026-09-01 (7 days from now)  
**Goal:** Achieve 60-70% SQL validity through data quality improvements  
**Theme:** "Clean Data, Better Results"

---

## Executive Summary

v0.2-beta focuses on **data quality over quantity**. Following Zhu et al. (2026) BIRD-Platinum methodology, we'll clean, verify, and filter our 14K acquired examples to create a high-quality training dataset. The hypothesis: **10K verified examples will outperform 100K noisy examples**.

**Key Insight from v0.1:** Training pipeline works perfectly (loss: 2.3→0.12), but model quality is poor (<10% valid SQL) due to noisy training data.

---

## Success Criteria

### Must Have (v0.2-beta definition)
- [ ] **SQL Validity ≥60%** (up from <10% in v0.1)
- [ ] **Execution Accuracy ≥40%** (up from 0% in v0.1)
- [ ] **Training Loss <0.10** (down from 0.12 in v0.1)
- [ ] **Datumara-Platinum Dataset** (10K verified examples)
- [ ] **Automated Evaluation Suite** (execution-based metrics)

### Nice to Have
- [ ] Validation loss tracking
- [ ] Complexity-stratified results
- [ ] Schema grounding prototype
- [ ] Comparison with v0.1 (side-by-side)

---

## Workstreams

### Stream 1: Data Cleaning & Verification (Days 1-3)

**Owner:** Data Pipeline  
**Priority:** CRITICAL (blocks everything else)

#### Tasks from Backlog
- [x] ✅ Detect and remove duplicate or contradictory examples across splits
- [ ] 🔲 **Clean and normalize column names across all datasets**
  - Standardize: `SQL/query/issue_sql` → `sql`
  - Standardize: `Question/Text` → `question`
  - Standardize: `db_id/db/database` → `db_id`
  - Standardize: `evidence/context/schema_info` → `evidence`
- [ ] 🔲 **Run full cleaning pipeline** (`acquire_and_clean.py`)
  - Execution verification (Stage 1)
  - Schema consistency checks (Stage 2)
  - Question-SQL alignment scoring (Stage 3)
- [ ] 🔲 **Create Datumara-Platinum dataset** (~10K high-quality examples)
  - Filter by execution validity
  - Remove schema inconsistencies
  - Score alignment with LLM judge (threshold ≥4.0/5.0)
- [ ] 🔲 **Validate every example against database schema**
  - Cross-reference table/column names
  - Verify foreign key relationships
  - Check data type compatibility

#### BIRD-Platinum Methodology Implementation

**Stage 1: Execution Validity**
```python
def verify_execution(sql: str, db_path: str) -> bool:
    """SQL must execute without errors"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(sql)
        cursor.fetchall()  # Ensure it returns results
        return True
    except Exception:
        return False
```

**Stage 2: Schema Consistency**
```python
def verify_schema(sql: str, schema: dict) -> bool:
    """All referenced tables/columns must exist"""
    # Parse SQL, extract table/column references
    # Cross-reference with actual schema
    # Return True if all objects exist
```

**Stage 3: Question-SQL Alignment**
```python
def verify_alignment(question: str, sql: str) -> float:
    """LLM judge scores semantic match 0-5"""
    # Use GPT-4 API or local LLM
    # Score: Does SQL answer the question?
    # Keep examples with score >= 4.0
```

#### Deliverables
1. `data/platinum/datumara_v0.2_train.parquet` (8-9K examples)
2. `data/platinum/datumara_v0.2_dev.parquet` (1K examples)
3. `data/platinum/datumara_v0.2_test.parquet` (1K examples)
4. `data/reports/cleaning_report.md` (quality metrics, rejection reasons)

---

### Stream 2: Training Improvements (Days 2-4)

**Owner:** Training Pipeline  
**Priority:** HIGH

#### Tasks from Backlog
- [ ] 🔲 **Mask prompt tokens from the loss**
  - Only train on SQL completion tokens
  - Don't waste capacity reproducing prompts
  - Implement via `labels` masking in `train_local_checkpoint.py`
- [ ] 🔲 **Add validation loss during training**
  - Track both training and validation loss
  - Report train/validation curves
  - Detect overfitting early
- [ ] 🔲 **Save best checkpoint by validation loss**
  - Already implemented in v0.1 ✅
  - Ensure it's using validation loss, not training loss
- [ ] 🔲 **Retrain with cleaned data** (same config as v0.1)
  - Base: TinyLlama-1.1B-Chat-v1.0
  - LoRA: rank=8, alpha=32 (unchanged for fair comparison)
  - Steps: 3000 (up from 2000, proportional to data increase)
  - Batch size: 1 (same as v0.1)

#### Training Configuration

```python
# v0.2-beta training config
TRAINING_CONFIG = {
    "model": "TinyLlama-1.1B-Chat-v1.0",
    "lora_rank": 8,  # Same as v0.1 for fair comparison
    "lora_alpha": 32,
    "train_steps": 3000,  # Up from 2000
    "batch_size": 1,
    "learning_rate": 2e-4,
    "warmup_ratio": 0.1,
    "checkpoint_every": 100,
    "eval_every": 100,
    "mask_prompt_tokens": True,  # NEW
    "track_validation": True,  # NEW
}
```

#### Deliverables
1. Updated `training/train_local_checkpoint.py` with prompt masking
2. `models/local-tinyllama-v0.2/` (checkpoint directory)
3. `training/reports/v0.2_training_report.md`
4. Training validation curves (PNG)

---

### Stream 3: Evaluation & Metrics (Days 3-5)

**Owner:** Quality Assurance  
**Priority:** HIGH (defines "success")

#### Tasks from Backlog
- [ ] 🔲 **Add SQL-generation evaluation**
  - Parse validity (can it be parsed as SQL?)
  - Exact match (matches reference SQL?)
  - Normalized match (semantically equivalent?)
  - Schema consistency (references valid objects?)
- [ ] 🔲 **Add post-training inference smoke test**
  - Bounded tokens (max 512)
  - Assert non-empty output
  - Assert SQL keywords present (SELECT, FROM, etc.)
- [ ] 🔲 **Compare training loss against validation loss**
  - Detect memorization vs. generalization
  - Report train/val gap
- [ ] 🔲 **Execute generated SQL against test databases**
  - Measure execution success rate
  - Compare results with expected output
  - Track error types (syntax, schema, logic)

#### Evaluation Metrics

```python
class SQLEvaluator:
    def __init__(self, test_db_path: str):
        self.db_path = test_db_path
    
    def evaluate(self, generated_sql: str, reference_sql: str) -> dict:
        return {
            "parse_valid": self.check_parse(generated_sql),
            "execution_valid": self.check_execution(generated_sql),
            "exact_match": self.check_exact_match(generated_sql, reference_sql),
            "normalized_match": self.check_normalized_match(generated_sql, reference_sql),
            "schema_valid": self.check_schema(generated_sql),
        }
```

#### Metrics Dashboard

| Metric | v0.1 | v0.2 Target | Measurement |
|--------|------|-------------|-------------|
| **Parse Validity** | ~30% | ≥70% | Can parse as SQL? |
| **Execution Validity** | 0% | ≥60% | Runs without error? |
| **Exact Match** | 0% | ≥40% | Matches reference exactly? |
| **Normalized Match** | 0% | ≥50% | Semantically equivalent? |
| **Schema Validity** | 0% | ≥65% | References valid objects? |
| **Train-Val Gap** | Unknown | <0.02 | Overfitting indicator |

#### Deliverables
1. `evaluation/sql_evaluator.py` (comprehensive evaluation)
2. `evaluation/reports/v0.2_metrics.json` (detailed results)
3. `evaluation/reports/v0.2_comparison.md` (v0.1 vs v0.2)
4. Automated smoke test script

---

### Stream 4: Export & Deployment (Days 5-6)

**Owner:** DevOps  
**Priority:** MEDIUM

#### Tasks from Backlog
- [ ] 🔲 **Keep Ollama export architecture-aware**
  - Validate created model with automated inference
  - Test with bounded generation
  - Verify stop tokens work correctly
- [ ] 🔲 **Add a Datumara Ollama Modelfile**
  - SQL-focused system instructions
  - Conservative generation settings
  - Version metadata (v0.2-beta)
- [ ] 🔲 **Add model versioning and changelog**
  - Tag exported model as `datumara-local-v0.2`
  - Document changes from v0.1
  - Track quality improvements

#### Modelfile Template

```dockerfile
FROM datumara-base:v0.2

# SQL-focused system prompt
SYSTEM """
You are Datumara v0.2-beta, an AI assistant specialized in SQL generation.
Given a natural language question, generate ONLY valid SQL.
Do not explain, do not provide context, just return SQL.
If you cannot generate SQL, return: "SQL_GENERATION_FAILED"
"""

# Conservative generation settings
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER max_tokens 512
PARAMETER stop ["<|endoftext|>", "Question:", "\n\n"]

# Version metadata
LABEL version "0.2-beta"
LABEL trained_on "Datumara-Platinum v0.2 (10K verified examples)"
LABEL base_model "TinyLlama-1.1B-Chat-v1.0"
LABEL training_date "2026-09-01"
LABEL quality_metrics "parse_validity=0.70, execution_validity=0.60"
```

#### Deliverables
1. `export/Modelfile.v0.2` (versioned Modelfile)
2. `datumara-local-v0.2` (Ollama model)
3. `export/reports/v0.2_export_validation.md`
4. Updated `install.sh` with version detection

---

### Stream 5: Documentation & Communication (Days 6-7)

**Owner:** Technical Writing  
**Priority:** MEDIUM

#### Tasks from Backlog
- [ ] 🔲 **Publish benchmark results**
  - Clear hardware specs
  - Dataset details (size, source, cleaning methodology)
  - Reproducibility instructions
- [ ] 🔲 **Update VERSIONING.md**
  - Document v0.2-beta release
  - Update roadmap to v0.3-rc
  - Track progress to v1.0-ga
- [ ] 🔲 **Create v0.2 release notes**
  - What improved (metrics)
  - What changed (training data, config)
  - Known issues
  - Migration guide from v0.1

#### Deliverables
1. `RELEASES/v0.2-beta.md` (release notes)
2. Updated `README.md` with v0.2 badges
3. Blog post: "Datumara v0.2: The Power of Clean Data"
4. Comparison charts (v0.1 vs v0.2)

---

## Detailed Timeline

### Day 1 (2026-08-25): Data Pipeline Setup
- [ ] Normalize column names in all datasets
- [ ] Set up sample databases for testing
- [ ] Test execution verification on mini_dev dataset
- [ ] Document cleaning methodology

### Day 2 (2026-08-26): Full Cleaning Pipeline
- [ ] Run execution verification on all 14K examples
- [ ] Run schema consistency checks
- [ ] Implement LLM judge for alignment scoring
- [ ] Filter and create Datumara-Platinum v0.2

### Day 3 (2026-08-27): Training Setup
- [ ] Implement prompt token masking
- [ ] Add validation loss tracking
- [ ] Prepare train/dev/test splits
- [ ] Launch training (3000 steps, ~3 hours)

### Day 4 (2026-08-28): Training Complete
- [ ] Monitor training, collect checkpoints
- [ ] Export best checkpoint
- [ ] Run initial evaluation
- [ ] Compare with v0.1 baseline

### Day 5 (2026-08-29): Comprehensive Evaluation
- [ ] Run full evaluation suite
- [ ] Execute generated SQL on test databases
- [ ] Calculate all metrics (parse, execution, match)
- [ ] Generate comparison report

### Day 6 (2026-08-30): Export & Validation
- [ ] Export to Ollama format
- [ ] Create Modelfile with v0.2 specs
- [ ] Run smoke tests
- [ ] Validate with automated inference

### Day 7 (2026-08-31): Documentation & Release
- [ ] Write release notes
- [ ] Update documentation
- [ ] Create comparison charts
- [ ] **RELEASE v0.2-beta** 🎉

---

## Resource Requirements

### Compute
- **GPU:** Quadro T2000 (4GB) - same as v0.1
- **Training Time:** ~3 hours (3000 steps)
- **Evaluation Time:** ~1 hour (full suite)
- **Total GPU Hours:** ~4 hours

### Storage
- **Cleaned Datasets:** ~2GB
- **Model Checkpoints:** ~2GB per checkpoint
- **Evaluation Results:** ~100MB
- **Total:** ~5GB

### External Services
- **LLM Judge API:** GPT-4 or Claude (~$10-20 for 10K examples)
- **Alternative:** Use local LLM (free, slower)

---

## Risk Management

### Risk 1: Execution Verification Fails
**Probability:** Medium  
**Impact:** High  
**Mitigation:** Use sample databases for development, acquire BIRD databases via author collaboration

### Risk 2: Quality Doesn't Improve
**Probability:** Low (based on Zhu et al. results)  
**Impact:** Critical  
**Mitigation:** Have fallback plan to increase LoRA rank or training steps

### Risk 3: Training Takes Too Long
**Probability:** Low  
**Impact:** Medium  
**Mitigation:** Can reduce steps to 2500 if needed, or use gradient accumulation

### Risk 4: Overfitting on Small Dataset
**Probability:** Medium  
**Impact:** Medium  
**Mitigation:** Track validation loss, implement early stopping

---

## Definition of Done

v0.2-beta is **DONE** when:

1. ✅ Datumara-Platinum v0.2 dataset created (10K verified examples)
2. ✅ Training complete with validation loss tracking
3. ✅ SQL validity ≥60% on test set
4. ✅ Execution accuracy ≥40% on test set
5. ✅ Model exported to Ollama as `datumara-local-v0.2`
6. ✅ Automated evaluation suite passes
7. ✅ Release notes published
8. ✅ Comparison with v0.1 documented

---

## Next Steps (Post-v0.2)

### v0.3-rc (Week 2: 2026-09-08)
- Increase LoRA rank (8 → 16 or 32)
- Add schema grounding (RAG)
- Extend training (5000+ steps)
- Target: 75-80% SQL validity

### v1.0-ga (Week 3-4: 2026-09-25)
- Scale to 7B+ parameter model
- Implement RLVR training
- Generate synthetic data
- Target: 85-90% SQL validity, production-ready

---

## Appendix: Backlog Mapping

### P0 Items Included in v0.2
- [x] ✅ Checkpoint saving (done in v0.1)
- [x] ✅ Train/dev/test split (done in v0.1)
- [ ] 🔲 Mask prompt tokens from loss
- [ ] 🔲 Add validation loss tracking
- [x] ✅ Save best checkpoint (done in v0.1)
- [ ] 🔲 Add SQL-generation evaluation
- [ ] 🔲 Add post-training inference smoke test
- [x] ✅ Fix Ollama prompt template (done in v0.1)
- [x] ✅ Run local TinyLlama experiment (done in v0.1)
- [ ] 🔲 Compare train vs validation loss

### P0.5 Items (All in v0.2)
- [ ] 🔲 Clean and normalize column names
- [ ] 🔲 Download/verify databases
- [ ] 🔲 Run full cleaning pipeline
- [ ] 🔲 Create Datumara-Platinum dataset
- [ ] 🔲 Retrain with cleaned data
- [ ] ⏸️ Increase LoRA rank (deferred to v0.3)
- [ ] ⏸️ Extend training to 5000+ steps (deferred to v0.3)
- [ ] ⏸️ Add schema grounding (deferred to v0.3)

### P1 Items Deferred to v0.3+
- [ ] ⏸️ Implement curriculum learning
- [ ] ⏸️ Add experiment configuration snapshots
- [ ] ⏸️ Preserve SQL answer during tokenization
- [ ] ⏸️ Use native chat templates
- [ ] ⏸️ Implement Qwen baseline benchmarking

---

**Status:** Ready to Execute  
**Next Action:** Start Day 1 tasks (data cleaning pipeline)  
**Questions?** Check [BACKLOG.md](BACKLOG.md) or [VERSIONING.md](VERSIONING.md)
