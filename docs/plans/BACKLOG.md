# Datumara Backlog

**Last Updated:** 2026-08-25  
**Current Status:** ✅ Training Complete | ✅ Data Acquired (14K examples) | ⚠️ Model Quality Needs Improvement

This is the working backlog for improving Datumara. Items are ordered by priority and should be checked off only after implementation and validation.

## P0: Make The Local Model Useful

- [x] **Add checkpoint saving and resume support so interrupted runs do not lose progress.** ← Critical after 1192-step interruption
  - Save adapter weights every N steps (e.g., every 100 steps)
  - Save `last_checkpoint.txt` with step number for resume
  - Add `--resume` flag to training script to continue from last checkpoint
  - Keep only last 3 checkpoints to save disk space
- [x] Add a held-out train/validation/test split with deterministic seed and complexity stratification.
- [ ] Mask prompt tokens from the loss so training scores the SQL completion rather than reproducing the prompt.
- [ ] Add validation loss during training and report train/validation curves.
- [ ] Add rolling loss averages and an ETA/steps-remaining display to live monitoring.
- [x] Save the best checkpoint by validation loss instead of using only the final checkpoint.
- [ ] Add SQL-generation evaluation: parse validity, exact match, normalized match, and schema consistency.
- [ ] Add a post-training inference smoke test with bounded tokens and assert non-empty output.
- [x] Fix the Ollama prompt template and stop tokens; verify output with a bounded automated inference test.
- [x] Run a meaningful local TinyLlama experiment and record quality metrics, not only training loss.
- [ ] Compare training loss against validation loss to detect memorization and overfitting.

## P0.5: v0.2-beta Development Plan (ACTIVE - Target: 2026-09-01)

**See:** [`PLAN_V0.2.md`](PLAN_V0.2.md) for detailed breakdown

### Stream 1: Data Cleaning (Days 1-3) - CRITICAL
- [ ] **Clean and normalize column names across all datasets** ← BLOCKING
  - Standardize: SQL/query/issue_sql → sql
  - Standardize: Question/Text → question  
  - Standardize: db_id/db/database → db_id
- [ ] **Run full cleaning pipeline** (acquire_and_clean.py)
  - Execution verification (sample databases created ✅)
  - Schema consistency checks
  - Question-SQL alignment scoring (LLM judge)
- [ ] **Create Datumara-Platinum v0.2 dataset** (~10K verified examples)
  - Filter by execution validity
  - Remove schema inconsistencies
  - Score alignment ≥4.0/5.0

### Stream 2: Training (Days 2-4) - HIGH
- [ ] **Mask prompt tokens from loss** ← NEW
  - Only train on SQL completion tokens
- [ ] **Add validation loss tracking**
  - Report train/validation curves
  - Detect overfitting
- [ ] **Retrain with cleaned data** (3000 steps)
  - Same config as v0.1 for fair comparison
  - Expected: 2-3x quality improvement

### Stream 3: Evaluation (Days 3-5) - HIGH
- [ ] **Add SQL-generation evaluation suite**
  - Parse validity
  - Execution validity
  - Exact/normalized match
  - Schema consistency
- [ ] **Add post-training inference smoke test**
  - Bounded tokens, assert non-empty
- [ ] **Compare v0.2 vs v0.1** (side-by-side report)

### Stream 4: Export (Days 5-6) - MEDIUM
- [ ] **Export as `datumara-local-v0.2`**
- [ ] **Create v0.2 Modelfile** (SQL-focused system prompt)
- [ ] **Validate with automated inference**

### Stream 5: Documentation (Days 6-7) - MEDIUM
- [ ] **Publish v0.2-beta release notes**
- [ ] **Update benchmarks & comparison charts**
- [ ] **Blog post: "The Power of Clean Data"**

### Deferred to v0.3-rc
- [ ] ⏸️ Increase LoRA rank from 8 to 16 or 32
- [ ] ⏸️ Extend training to 5000-10000 steps
- [ ] ⏸️ Add schema grounding (RAG)

## P1: Complete The Hosted Training Path

- [ ] Implement `training/train.py` using the shared model, LoRA, training, and hardware configuration.
- [ ] Add runtime hardware eligibility checks before model loading and fail with actionable guidance.
- [ ] Add 4-bit QLoRA dependency and verify it on the target hosted GPU.
- [ ] Support configurable sequence length, micro-batch size, gradient accumulation, precision, and checkpoint interval.
- [ ] Add automatic batch-size/context-length recommendations from detected free VRAM.
- [ ] Implement curriculum learning and complexity-weighted loss only after baseline training is measurable.
- [ ] Add experiment configuration snapshots, random seeds, git revision, and environment metadata to every run.
- [ ] Add graceful handling for OOM, interruptions, and insufficient disk space.

## P1: Data And Evaluation Quality

- [x] Validate every augmented example against its database schema and SQLite execution where possible. ← Scripts created, execution pending
- [x] Detect and remove duplicate or contradictory examples across splits.
- [ ] Preserve the SQL answer when tokenizing long schema prompts; measure truncation rates by complexity.
- [ ] Use native chat templates for chat-tuned bases and verify prompt/response token boundaries.
- [ ] Report how many examples are processed per run when a step cap stops before the full dataset.
- [ ] Add a fixed evaluation set that is never used for training decisions.
- [ ] Implement Qwen baseline benchmarking and side-by-side comparison reports.
- [ ] Add hard-example mining from failed validation and test predictions.

## P2: Distribution And Operations

- [ ] Add one-command export from adapter to merged Hugging Face format.
- [ ] Add optional authenticated Hugging Face upload with model card, license, dataset attribution, and training metadata.
- [ ] Keep Ollama export architecture-aware and validate the created model with automated inference.
- [ ] Add a Datumara Ollama Modelfile with SQL-focused system instructions and conservative generation settings.
- [ ] Add model versioning and a changelog for published checkpoints.
- [ ] Add CI checks for Python syntax, YAML validity, report generation, and export smoke tests.

## P3: Product Improvements

- [ ] Add database dialect profiles for SQLite, PostgreSQL, BigQuery, Snowflake, and DuckDB.
- [ ] Add schema-aware SQL repair and validation before returning a query.
- [ ] Add analytics tasks beyond SQL generation: metric definitions, statistical summaries, and anomaly detection.
- [ ] Add a routing task for selecting the correct database or dialect.
- [ ] Add a simple local API or CLI with structured JSON output.
- [ ] Publish benchmark results with clear hardware, dataset, and reproducibility details.

## Completed Foundations

- [x] Runtime hardware detection and model capability profiles.
- [x] Local TinyLlama LoRA training on the Quadro T2000.
- [x] Per-step progress JSONL and Markdown training report.
- [x] Merged Hugging Face export.
- [x] Ollama registration for the TinyLlama-based local artifact.
