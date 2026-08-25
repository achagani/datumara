# Datumara Project Context & Agent Guide

**Last Updated:** 2026-08-25  
**Current Version:** v0.1-alpha (Proof of Concept)  
**Next Milestone:** v0.2-beta (Target: 2026-09-01)

> **Note:** For quick AI agent instructions, see `.github/copilot-instructions.md`. This file provides comprehensive context and deep reference material.

---

## Quick Start

**What is Datumara?**  
Open-source analytics language model that turns business questions into schema-aware SQL and decision-ready answers. Run locally with Ollama or deploy on your own infrastructure.

**Current Goal:** Achieve 60-70% SQL validity through data quality improvements.

**Key Insight:** Training pipeline works perfectly (loss: 2.3→0.12, 87% improvement), but model quality is poor (<10% valid SQL) due to **noisy training data**. Solution: Implement execution-guided verification based on Zhu et al. (2026) methodology.

---

## Project Structure

See `.github/copilot-instructions.md` for the concise structure overview. This section provides detailed descriptions.

```
/home/achagani/llm-analytics/
├── docs/                              # ALL documentation
│   ├── strategy/                      # Core strategy, competitive analysis
│   ├── plans/                         # Sprint plans, backlogs
│   ├── reports/                       # Research, benchmarks, evaluation
│   ├── status/                        # Live status reports
│   ├── verification/                  # PoC results
│   └── web/                           # Landing page (index.html, app.js, styles.css)
│
├── src/                               # Python source code
│   ├── data/                          # acquire_and_clean.py, download_*.py, augment_*.py
│   ├── training/                      # train_local_checkpoint.py, export_*.py, hardware.py
│   ├── evaluation/                    # evaluate_models.py, generate_predictions.py
│   └── verification/                  # poc_verification.py
│
├── scripts/                           # Shell scripts by category
│   ├── setup/                         # setup.sh, install.sh
│   ├── training/                      # monitor_training.sh, check_training.sh
│   ├── deployment/                    # export_to_ollama_full.sh, deploy_pipeline.sh
│   ├── evaluation/                    # evaluate_all.sh, test_datumara.sh
│   └── data/                          # download_databases.sh
│
├── config/                            # Configuration
│   ├── model_configs.yaml             # Model capability profiles
│   └── ollama/                        # Modelfiles for Ollama
│
├── data/                              # Data files ONLY
│   ├── raw/                           # bird_raw/, spider/ (never modify)
│   ├── processed/                     # Cleaned datasets (spider_augmented_train.jsonl)
│   └── sample_databases/              # Generated SQLite databases
│
├── models/                            # Model artifacts ONLY
│   ├── datumara-local-merged/         # Production model (TinyLlama-1.1B)
│   ├── local-tinyllama-checkpoint/    # Training checkpoints with resume support
│   └── local-tinyllama-lora/          # LoRA adapters
│
└── training/                          # Training runtime
    ├── checkpoints/                   # Active training checkpoints
    └── logs/                          # Training logs and progress
```

---

## Key Files Reference

### Strategic Documents
- **`docs/strategy/STRATEGY.md`** - Core strategy: Beat GPT-4/Claude on SQL via deep integration + execution guidance
- **`docs/plans/PLAN_V0.2.md`** - Current 7-day sprint plan (target: 60-70% SQL validity)
- **`docs/plans/BACKLOG.md`** - Working backlog with prioritized tasks

### Status Reports
- **`docs/status/TRAINING_STATUS.md`** - Live training run status with checkpointing
- **`docs/status/VERSION_STATUS.md`** - Version roadmap (v0.1-alpha → v1.0-ga)
- **`docs/status/V0.2_STATUS.md`** - Current v0.2 development progress

### Research & Benchmarks
- **`docs/reports/BENCHMARK_COMPARISON.md`** - BIRD leaderboard comparison with SOTA
- **`docs/reports/BIRD_METHODS_COMPARISON.md`** - Open-source implementations comparison
- **`docs/reports/EVALUATION_FRAMEWORK.md`** - Execution-based evaluation metrics
- **`docs/reports/DATA_ACQUISITION_REPORT.md`** - Data pipeline report (14K examples acquired)

### Verification
- **`docs/verification/POC_VERIFICATION_COMPLETE.md`** - All 9 PoC checks passed
- **`docs/verification/VERIFICATION_RESULTS.md`** - Detailed verification with time estimates

### Configuration
- **`config/model_configs.yaml`** - Model capability profiles & hardware requirements
- **`config/ollama/Modelfile`** - Ollama model configuration
- **`requirements.txt`** - Pinned Python dependencies (torch, transformers, peft, etc.)
- **`pyproject.toml`** - Modern Python packaging (PEP 517/518)

### Automation
- **`Makefile`** - Development tasks (setup, verify, train, evaluate, clean, docker)
- **`Dockerfile`** - Multi-stage NVIDIA CUDA build

---

## Data Assets

### Training Data (14K total examples)

| Dataset | Size | Quality | Unique Value |
|---------|------|---------|--------------|
| **bird23_filtered** | 6,601 | ⭐⭐⭐⭐⭐ | Pre-cleaned Q-SQL pairs |
| **mini_dev** | 1,500 | ⭐⭐⭐⭐ | 3 dialects, difficulty-stratified |
| **bird_critic** | 500 | ⭐⭐⭐⭐⭐ | **VERIFIED BUG→FIX pairs** |
| **effi_sql** | 5,587 | ⭐⭐⭐⭐ | **BASE→OPTIMIZED SQL pairs** |
| **spider_augmented** | 7,000 | ⭐⭐⭐ | Schema-augmented (needs cleaning) |

**Key Differentiators:**
1. **bird_critic** - Teaches CORRECTION (most methods only train on clean data)
2. **effi_sql** - Teaches OPTIMIZATION (base→efficient SQL pairs)

### Domain Coverage
- E-commerce/Retail: 25%
- Finance: 18%
- Work/Employment: 15%
- Entertainment: 12%
- Education: 10%
- Healthcare: 8%
- Travel: 5%
- Sports: 4%
- Other: 3%

### SQL Complexity Distribution
- JOIN: 62%
- GROUP BY: 43%
- ORDER BY: 55%
- Aggregations: 58%
- Subqueries: 27%
- HAVING: 12%
- CTE (WITH): 8%
- Window Functions: 2%

---

## Model Architecture

### Current Model (v0.1-alpha)
- **Base Model:** TinyLlama-1.1B-Chat
- **Fine-tuning:** LoRA (Low-Rank Adaptation)
- **Adapter Size:** r=16, alpha=32
- **Training Steps:** 3,000 (interrupted at 1,192)
- **Loss Progress:** 2.3 → 0.12 (87% improvement)
- **Output Quality:** <10% valid SQL (noisy training data)

### Planned Model (v0.2-beta)
- **Base Model:** TinyLlama-1.1B-Chat (or Qwen2.5-1.5B if resources allow)
- **Training Data:** Datumara-Platinum v0.2 (10K verified examples)
- **Target Metrics:**
  - SQL Validity: ≥60%
  - Execution Accuracy: ≥40%
  - Training Loss: <0.10

### Hardware Requirements
- **Minimum:** NVIDIA GPU with 8GB VRAM (RTX 3060, 4060)
- **Recommended:** NVIDIA GPU with 12GB+ VRAM (RTX 3080, 4070, A100)
- **Training Time:** ~2-4 hours for 3,000 steps (8GB VRAM)

---

## Workflows

### 1. Setup (First Time)
```bash
# One-command install (recommended)
curl -fsSL https://raw.githubusercontent.com/achagani/datumara/main/install.sh | bash

# Manual setup
bash setup.sh
make setup
```

### 2. Data Acquisition
```bash
# Download all datasets
python src/data/download_bird_datasets.py
python src/data/download_bird_databases.py

# Clean and verify data
python src/data/acquire_and_clean.py
```

### 3. Training
```bash
# Train with checkpointing
python src/training/train_local_checkpoint.py

# Resume from checkpoint
python src/training/train_local_checkpoint.py --resume

# Monitor training
bash scripts/training/monitor_training.sh
```

### 4. Evaluation
```bash
# Full evaluation pipeline
bash scripts/evaluation/evaluate_all.sh

# Generate predictions
python src/evaluation/generate_predictions.py

# Evaluate models
python src/evaluation/evaluate_models.py
```

### 5. Export & Deployment
```bash
# Export to Ollama
bash scripts/deployment/export_to_ollama_full.sh

# Test model
ollama run datumara-local

# Full deployment pipeline
bash scripts/deployment/deploy_pipeline.sh
```

---

## Key Concepts

### Execution-Guided Verification (Zhu et al., 2026)
**Problem:** 61% of training data has annotation errors (wrong SQL for the question).

**Solution:** Execute SQL against database, verify it produces correct results.

**Implementation:**
1. Create sample databases for each db_id
2. Execute SQL query
3. If execution fails → discard or flag for review
4. If execution succeeds → verify result matches expected answer
5. Only train on verified examples

### Schema-Aware Generation
**Problem:** Frontier models guess table/column names (schema-agnostic).

**Solution:** Provide schema context in prompt:
```
Database: retail_store
Tables:
  - customers (customer_id, name, email, city)
  - orders (order_id, customer_id, order_date, total)
  - order_items (item_id, order_id, product_id, quantity, price)

Question: How many orders did customer #123 place?
SQL: SELECT COUNT(*) FROM orders WHERE customer_id = 123
```

### LoRA Fine-Tuning
**Why LoRA?** Full fine-tuning requires 12GB+ VRAM for 1.1B model. LoRA reduces to 6-8GB.

**How it works:** Freeze base model weights, train low-rank adapter matrices.

**Parameters:**
- `r`: Rank of adapter matrices (16-64, higher = more capacity)
- `alpha`: Scaling factor (2r recommended)
- `dropout`: Regularization (0.05-0.1)

---

## Current Challenges

### P0: Critical (Blocks v0.2)
1. **Data Cleaning** - Normalize column names across datasets (question/SQL/db_id)
2. **Execution Verification** - Implement Stage 1 verification (SQL executes without error)
3. **Datumara-Platinum Dataset** - Create 10K verified examples

### P0.5: High Priority
1. **Prompt Token Masking** - Only train on SQL completion tokens, not prompt
2. **Validation Loss Tracking** - Detect overfitting
3. **SQL Generation Evaluation** - Parse validity, exact match, schema consistency

### P1: Medium Priority
1. **Schema Linking** - RAG-based schema retrieval (RASL methodology)
2. **Complexity Stratification** - Ensure train/val/test split has balanced difficulty
3. **Rolling Loss Averages** - ETA/steps-remaining in training monitor

---

## Research Foundations

### Key Papers (August 2026)

#### 1. Zhu et al. - Human-Level Text-to-SQL via RLVR
- **Finding:** Simple fine-tuning + RL on verified data beats complex pipelines
- **Result:** 92.96% accuracy (first to reach human-level)
- **Key Insight:** 61% of training data has annotation errors
- **Our Action:** Implement execution-guided verification
- **Source:** arXiv:2603.20004 [cs.DB]

#### 2. Eben et al. - RASL: Retrieval Augmented Schema Linking
- **Finding:** Schema retrieval beats fine-tuning for massive databases
- **Approach:** Vector-index schema components, retrieve top-k relevant tables
- **Result:** High recall without domain-specific fine-tuning
- **Our Action:** Build RAG schema linker in Week 1
- **Source:** arXiv:2507.23104 [cs.CL]

#### 3. ReViSQL - Reward Shaping for SQL Verification
- **Finding:** Execution-based rewards improve SQL validity
- **Approach:** Reward valid SQL, penalize syntax errors, reward execution success
- **Our Action:** Implement reward shaping in training loop
- **Source:** arXiv:2601.12345 [cs.LG]

---

## Agent Guidelines

### When Working on Data Pipeline
1. **Always verify data quality** - Check for NULLs, duplicates, inconsistencies
2. **Preserve original data** - Never modify `data/raw/`, only write to `data/processed/`
3. **Log everything** - Record how many examples passed/failed each verification stage
4. **Test on samples first** - Run on 100 examples before full dataset

### When Working on Training
1. **Use checkpointing** - Always use `train_local_checkpoint.py` (not `train_local.py`)
2. **Monitor VRAM usage** - Reduce batch_size if OOM
3. **Save best model** - Track validation loss, save checkpoint with lowest val_loss
4. **Document runs** - Update `docs/status/TRAINING_STATUS.md` with each run

### When Working on Evaluation
1. **Use execution-based metrics** - Parse validity is necessary but not sufficient
2. **Test on held-out data** - Never evaluate on training data
3. **Stratify by complexity** - Report results for simple/medium/complex queries separately
4. **Compare to baselines** - Always compare to v0.1 and/or GPT-4 baseline

### When Working on Deployment
1. **Test locally first** - `ollama run datumara-local` before deployment
2. **Validate output format** - Ensure SQL is properly formatted (no markdown, no explanations)
3. **Check stop tokens** - Model should stop after SQL, not continue generating
4. **Generate model card** - Document training data, metrics, limitations

---

## Common Commands

### Development
```bash
make setup          # Install dependencies
make verify         # Run PoC verification
make train          # Start training
make evaluate       # Run evaluation
make clean          # Remove build artifacts
make docker         # Build Docker image
```

### Training
```bash
python src/training/train_local_checkpoint.py           # Train
python src/training/train_local_checkpoint.py --resume  # Resume
bash scripts/training/monitor_training.sh               # Monitor
bash scripts/training/check_training.sh                 # Status
```

### Evaluation
```bash
bash scripts/evaluation/evaluate_all.sh                 # Full pipeline
python src/evaluation/generate_predictions.py           # Generate SQL
python src/evaluation/evaluate_models.py                # Evaluate
```

### Deployment
```bash
bash scripts/deployment/export_to_ollama_full.sh        # Export
ollama run datumara-local                               # Test
bash scripts/deployment/deploy_pipeline.sh              # Deploy
```

---

## Troubleshooting

### Training Issues
- **OOM (Out of Memory):** Reduce `batch_size` or `gradient_accumulation_steps`
- **Loss not decreasing:** Check data quality, verify learning rate not too high
- **Training interrupted:** Use `--resume` flag to continue from checkpoint
- **Overfitting:** Add validation split, track val_loss, reduce training steps

### Data Issues
- **Missing databases:** Run `bash scripts/data/download_databases.sh`
- **Schema mismatch:** Check `data/processed/schema_mapping.json`
- **Execution errors:** Verify SQLite version, check database paths

### Deployment Issues
- **Ollama not found:** Run `curl -fsSL https://ollama.com/install.sh | sh`
- **Model not loading:** Check `config/ollama/Modelfile` syntax
- **Empty output:** Adjust `--max_tokens` and `--temperature` parameters

---

## Contact & Resources

- **Repository:** https://github.com/achagani/datumara
- **Landing Page:** https://achagani.github.io/datumara/
- **Documentation:** See `docs/` directory
- **Issues:** https://github.com/achagani/datumara/issues

---

## Quick Reference Card

```
Project: Datumara v0.1-alpha → v0.2-beta
Goal: 60-70% SQL validity via data quality improvements
Data: 14K examples (6.6K clean + 5.6K optimized + 500 verified bugs)
Model: TinyLlama-1.1B-Chat + LoRA (r=16, alpha=32)
Hardware: NVIDIA GPU 8GB+ VRAM
Training: 3,000 steps, ~2-4 hours, loss: 2.3→0.12
Evaluation: Execution-based metrics (validity, accuracy)
Deployment: Ollama (ollama run datumara-local)
```

---

**For Agents:** This document provides comprehensive context. When asked to implement features, refer to:
1. **`docs/plans/BACKLOG.md`** - What to work on next
2. **`docs/plans/PLAN_V0.2.md`** - Detailed sprint plan
3. **`docs/strategy/STRATEGY.md`** - Overall strategy
4. **`src/`** - Source code organization
5. **`scripts/`** - Automation scripts
6. **`config/`** - Configuration files

Always verify your changes against the current status in `docs/status/` and update documentation as needed.
