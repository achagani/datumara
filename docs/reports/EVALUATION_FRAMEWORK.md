# Datumara Evaluation Framework

Complete system for evaluating and comparing SQL generation models side-by-side.

## Overview

This framework provides:
- **Execution-based evaluation** (not just string matching)
- **Multi-model comparison** (Datumara vs competitors)
- **Comprehensive metrics** (EX, VES, parse validity, schema validity)
- **Complexity-stratified analysis** (easy/medium/hard/expert)
- **BIRD leaderboard compatibility** (submit-ready format)

## Quick Start

### 1. Download Databases

```bash
# Download all BIRD databases (train, dev, mini-dev)
python data/download_bird_databases.py --output-dir data/databases

# Or run the full pipeline (auto-downloads if missing)
bash evaluate_all.sh
```

### 2. Generate Predictions

```bash
# Generate predictions from v0.1-alpha model
python generate_predictions.py \
    --model datumara-local \
    --test-set mini_dev \
    --output predictions/datumara_v0.1/predictions.json
```

### 3. Run Evaluation

```bash
# Evaluate all models in predictions/ directory
python evaluate_models.py \
    --test-set data/bird_raw/mini_dev.parquet \
    --db-path data/databases \
    --predictions-dir predictions \
    --output results/comparison.json
```

### 4. View Results

```bash
# Open markdown report
open results/comparison.md

# Or view CSV
cat results/comparison.csv
```

---

## Directory Structure

```
llm-analytics/
├── data/
│   ├── databases/              # BIRD databases (downloaded)
│   │   ├── train_databases/    # 95 databases, 33.4 GB
│   │   ├── dev_databases/      # Development set databases
│   │   └── mini_dev/           # Mini-Dev (3 dialects)
│   ├── bird_raw/               # Raw datasets (parquet)
│   └── download_bird_databases.py
├── predictions/
│   ├── datumara_v0.1_alpha/    # v0.1 predictions
│   │   └── predictions.json
│   ├── datumara_v0.2_beta/     # v0.2 predictions
│   └── competitor_1/           # Baseline predictions
├── results/
│   ├── comparison.json         # Full results
│   ├── comparison.csv          # Summary table
│   └── comparison.md           # Human-readable report
├── evaluate_models.py          # Main evaluation script
├── generate_predictions.py     # Prediction generator
├── evaluate_all.sh             # Complete pipeline
└── BENCHMARK_COMPARISON.md     # Leaderboard comparison
```

---

## Metrics

### Primary Metrics (BIRD Standard)

#### 1. Execution Accuracy (EX)
**Definition:** Percentage of queries that execute correctly and produce the same result as the reference SQL.

```python
EX = (# correct executions) / (# total queries)
```

**Why it matters:** Measures actual correctness, not just syntax.

#### 2. Valid Efficiency Score (VES)
**Definition:** Combines correctness with execution efficiency.

```python
VES = max(0, 1.0 - 0.1 * (execution_time / baseline_time))
```

**Why it matters:** Rewards efficient queries, penalizes slow ones.

#### 3. Reward-based VES (R-VES)
**Definition:** Improved VES with better reward shaping (used in 2025-2026 submissions).

### Secondary Metrics (Development)

#### 4. Parse Validity
**Definition:** Can the output be parsed as valid SQL?

```python
Parse Validity = (# parseable SQL) / (# total queries)
```

**Why it matters:** Prerequisite for execution. Measures basic syntax learning.

#### 5. Schema Validity
**Definition:** Do all referenced tables/columns exist in the database?

```python
Schema Validity = (# schema-valid SQL) / (# total queries)
```

**Why it matters:** Measures schema grounding. Critical for real-world use.

#### 6. Exact Match (EM)
**Definition:** Does generated SQL match reference exactly?

```python
EM = (# exact matches) / (# total queries)
```

**Why it matters:** Strict metric. Penalizes semantically equivalent alternatives.

#### 7. Normalized Match (NM)
**Definition:** Are queries semantically equivalent after normalization?

```python
NM = (# normalized matches) / (# total queries)
```

**Why it matters:** More lenient than EM. Allows syntactic variations.

---

## Test Sets

### 1. Mini-Dev (500 examples)
- **Purpose:** Fast development testing
- **Dialects:** SQLite, MySQL, PostgreSQL
- **Domains:** 10+ professional domains
- **Complexity:** Stratified (easy/medium/hard/expert)

**When to use:** Daily development, ablation studies, hyperparameter tuning.

### 2. BIRD Dev (1,534 examples)
- **Purpose:** Official benchmark for leaderboard submission
- **Dialect:** SQLite (primary)
- **Domains:** 37+ professional domains
- **Complexity:** Full distribution

**When to use:** Final evaluation before submission, comparison with SOTA.

### 3. BIRD Train (9,428 examples)
- **Purpose:** Training (not evaluation)
- **Note:** Contains annotation errors (61% error rate)
- **Recommendation:** Use cleaned version (BIRD-Platinum)

**When to use:** Training only, never for evaluation.

### 4. Datumara Internal Test (1,000 examples)
- **Purpose:** Held-out test set
- **Source:** Stratified sample from train + external
- **Usage:** Never used for training

**When to use:** Version comparison, tracking progress over time.

---

## Usage Examples

### Example 1: Evaluate Single Model

```bash
# Generate predictions
python generate_predictions.py \
    --model datumara-local \
    --test-set mini_dev \
    --output predictions/my_model/predictions.json

# Evaluate
python evaluate_models.py \
    --test-set data/bird_raw/mini_dev.parquet \
    --db-path data/databases/mini_dev/sqlite \
    --predictions-dir predictions \
    --output results/my_model_results.json
```

### Example 2: Compare Multiple Models

```bash
# Generate predictions for all models
for model in datumara-v0.1 datumara-v0.2 competitor-1; do
    python generate_predictions.py \
        --model $model \
        --test-set mini_dev \
        --output predictions/$model/predictions.json
done

# Compare
python evaluate_models.py \
    --test-set data/bird_raw/mini_dev.parquet \
    --db-path data/databases/mini_dev/sqlite \
    --predictions-dir predictions \
    --output results/model_comparison.json
```

### Example 3: Full Pipeline

```bash
# Run everything (download, generate, evaluate, report)
bash evaluate_all.sh mini_dev
```

---

## Output Format

### JSON Results

```json
{
  "timestamp": "2026-08-25 14:30:00",
  "test_set": "mini_dev",
  "db_path": "data/databases/mini_dev/sqlite",
  "models": {
    "datumara_v0.1_alpha": {
      "total": 500,
      "parse_valid": 450,
      "schema_valid": 400,
      "exact_match": 180,
      "normalized_match": 220,
      "execution_correct": 200,
      "ves_sum": 175.5,
      "metrics": {
        "parse_validity": 0.90,
        "schema_validity": 0.80,
        "exact_match": 0.36,
        "normalized_match": 0.44,
        "execution_accuracy": 0.40,
        "avg_ves": 0.8775,
        "by_complexity": {
          "easy": 0.65,
          "medium": 0.45,
          "hard": 0.25,
          "expert": 0.10
        }
      }
    }
  },
  "comparison_table": {
    "Model": ["datumara_v0.1_alpha"],
    "Parse Validity": ["90.0%"],
    "Execution Accuracy": ["40.0%"],
    ...
  }
}
```

### Markdown Report

```markdown
# Datumara Model Comparison Report

**Generated:** 2026-08-25 14:30:00  
**Test Set:** mini_dev  
**Database:** data/databases/mini_dev/sqlite

---

## Executive Summary

| Model | Execution Accuracy | Parse Validity | Avg VES |
|-------|-------------------|----------------|---------|
| **datumara_v0.2_beta** | 65.0% | 95.0% | 0.92 |
| **datumara_v0.1_alpha** | 40.0% | 90.0% | 0.88 |

---

## Detailed Results

### datumara_v0.2_beta

- **Parse Validity:** 95.0%
- **Schema Validity:** 92.0%
- **Exact Match:** 58.0%
- **Normalized Match:** 62.0%
- **Execution Accuracy:** 65.0%
- **Avg VES:** 0.92

**By Complexity:**
- Easy: 85.0%
- Medium: 70.0%
- Hard: 50.0%
- Expert: 35.0%
```

---

## BIRD Leaderboard Submission

### Submission Process

1. **Prepare predictions** in required format:
```bash
python prepare_bird_submission.py \
    --results results/comparison.json \
    --output submission_package.zip
```

2. **Email to BIRD team:**
- **Email:** bird.bench23@gmail.com
- **Subject:** BIRD Leaderboard Submission - Datumara v0.2
- **Include:**
  - Method name and description
  - Model size and architecture
  - Training data details
  - Generated predictions (JSON)
  - Paper/preprint link (if available)

3. **Wait for evaluation** (~10 days)

4. **Results published** on https://bird-bench.github.io/

### Submission Categories

- **Single-Model:** No ensemble, no voting (Datumara default)
- **Multi-Model:** Ensemble methods, self-consistency voting
- **Open-Source:** Public weights (Datumara qualifies)
- **Closed-Source:** API-based models (GPT-4, Claude)

---

## Troubleshooting

### Issue: Database not found

```bash
# Download databases
python data/download_bird_databases.py --output-dir data/databases
```

### Issue: Predictions not generating

```bash
# Check if Ollama model is running
ollama list

# If not running, pull model
ollama pull datumara-local

# Test model manually
ollama run datumara-local "SELECT 1"
```

### Issue: Low execution accuracy

**Possible causes:**
1. **Parse errors:** Model not generating valid SQL
   - Solution: Train longer, use syntax constraints
   
2. **Schema errors:** Model referencing non-existent tables/columns
   - Solution: Improve schema grounding, add schema linking
   
3. **Semantic errors:** SQL executes but wrong results
   - Solution: More training data, execution feedback

### Issue: Evaluation too slow

```bash
# Reduce test set size
python evaluate_models.py \
    --test-set data/bird_raw/mini_dev.parquet \
    --subset-size 100  # Only evaluate first 100 examples
```

---

## Performance Benchmarks

### Expected Metrics by Model Size

| Model Size | Parse Validity | Execution Accuracy | Avg VES |
|------------|---------------|-------------------|---------|
| <1B | 70-80% | 30-40% | 0.75-0.85 |
| 1-2B | 80-90% | 40-50% | 0.85-0.90 |
| 7-8B | 90-95% | 60-70% | 0.90-0.95 |
| 30B+ | 95-98% | 75-85% | 0.95-0.98 |

### Datumara Targets

| Version | Model Size | Parse Validity | Execution Accuracy | Target Date |
|---------|------------|---------------|-------------------|-------------|
| v0.1-alpha | 1.1B | 85% | <10% | ✅ Aug 25, 2026 |
| v0.2-beta | 1.1B | 90% | 40-50% | 🎯 Sep 1, 2026 |
| v0.3-rc | 1.1B | 92% | 60-70% | 📅 Sep 8, 2026 |
| v1.0-ga | 7-8B | 95% | 75-85% | 📅 Sep 25, 2026 |

---

## Advanced Usage

### Custom Metrics

```python
# Add custom metric to evaluator
class CustomEvaluator(DatumaraEvaluator):
    def compute_custom_metric(self, sql1, sql2):
        # Your custom comparison logic
        return score
    
    def evaluate_model(self, model_name, predictions):
        results = super().evaluate_model(model_name, predictions)
        
        # Add custom metric
        results['metrics']['custom'] = self.compute_custom_metric(...)
        
        return results
```

### Parallel Evaluation

```python
# Evaluate models in parallel
from multiprocessing import Pool

with Pool(4) as p:
    results = p.map(evaluator.evaluate_model, model_predictions.items())
```

### Database Connection Pooling

```python
# For large-scale evaluation
from sqlalchemy import create_engine

engine = create_engine('sqlite:///database.db', pool_size=10, max_overflow=20)
```

---

## References

- **BIRD Benchmark:** https://bird-bench.github.io/
- **BIRD Paper:** Li et al. (2023) - "Can LLM Already Serve as a Database Interface?"
- **BIRD-Platinum:** Zhu et al. (2026) - "Human-Level Text-to-SQL via RLVR"
- **Mini-Dev:** https://github.com/bird-bench/mini_dev
- **Evaluation Code:** https://github.com/bird-bench/BIRD-CRITIC-1

---

## Contributing

To add new metrics or test sets:

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit PR

---

## License

MIT License - See LICENSE file for details

---

**Last Updated:** 2026-08-25  
**Maintained By:** Datumara Team  
**Questions?** Open an issue on GitHub
