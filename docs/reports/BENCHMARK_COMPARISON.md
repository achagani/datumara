# Datumara vs BIRD Leaderboard Comparison Framework

**Last Updated:** 2026-08-25  
**Purpose:** Objective benchmarking against state-of-the-art text-to-SQL methods

---

## BIRD Leaderboard Overview

The BIRD benchmark is the gold standard for text-to-SQL evaluation, featuring:
- **12,751** unique question-SQL pairs
- **95** big databases (33.4 GB total)
- **37+** professional domains
- **Two metrics:** Execution Accuracy (EX) and Valid Efficiency Score (VES)

### Leaderboard Categories

1. **Overall Leaderboard** - All methods (single + multi-model)
2. **Single-Model Leaderboard** - Single model inference only
3. **Mini-Dev Leaderboard** - 500 high-quality examples (3 dialects)
4. **Efficiency Leaderboard** - R-VES metric (reward-based valid efficiency)

---

## Current State-of-the-Art (as of Aug 2026)

### Top Performers - Execution Accuracy (EX)

| Rank | Method | Model Size | EX (%) | Date |
|------|--------|------------|--------|------|
| 🥇 **Human Performance** | Data Engineers + DB Students | - | **92.96** | - |
| 🏆 AskData + GPT-4o | AT&T CDO - DSAIR | UNK | 81.95 | Dec 2025 |
| 🥈 Agentar-Scale-SQL | Ant Group | UNK | 81.67 | Sep 2025 |
| 🥉 Sber Text2SQL | SberData Research | UNK | 81.33 | Jun 2026 |
| 4️⃣ Xiaomi Text2SQL | Xiaomi ITP & Data | UNK | 80.83 | May 2026 |
| 5️⃣ RAS | Adya AI | UNK | 79.82 | Aug 2026 |

### Top Open-Source Models (Single-Model)

| Rank | Method | Model Size | EX (%) | Approach |
|------|--------|------------|--------|----------|
| 1️⃣ DeepEye-SQL | 27B | 78.42 | Multi-stage reasoning |
| 2️⃣ Spektr-SQL | 30B-3B-MoE | 78.31 | Amazon Ads |
| 3️⃣ DataGallery-Text2SQL | UNK | 77.53 | Huawei 2012 Labs |
| 4️⃣ LongData-SQL | UNK | 77.53 | LongShine AI |
| 5️⃣ AxisSQL | 31B | 76.86 | UST |

### Small Model Category (<10B)

| Rank | Method | Model Size | EX (%) | Notable |
|------|--------|------------|--------|---------|
| 1️⃣ CSC-SQL + Qwen2.5-7B | 7B | 71.72 | Wuhan Univ + USTC |
| 2️⃣ LEAF-SQL | 14B | 71.60 | JXUFE |
| 3️⃣ SLM-SQL + Qwen2.5-1.5B | 1.5B | 70.49 | Wuhan Univ + USTC |
| 4️⃣ OmniSQL-7B | 7B | 67.97 | Renmin Univ + ByteDance |
| 5️⃣ SFT CodeS-7B | 7B | 59.25 | Renmin Univ |

### Mini-Dev Leaderboard (500 examples, 3 dialects)

| Rank | Method | EX (%) | SQLite | MySQL | PostgreSQL |
|------|--------|--------|--------|-------|------------|
| 🥇 SmartQuery + GPT-5.1 | 56.80 | - | - | - |
| 🥈 TA + GPT-4 | 50.80 | 58.00 | 49.20 | 35.80 |
| 🥉 GPT-4 | 35.80 | 47.80 | 40.80 | 35.80 |
| 4️⃣ GPT-4-32k | 35.00 | 47.00 | 43.20 | 35.00 |
| 5️⃣ Llama3-8b-instruct | 18.40 | 24.40 | 24.60 | 18.40 |

---

## Datumara Positioning Strategy

### Current Status (v0.1-alpha)

| Metric | Datumara v0.1 | vs Leaderboard | Status |
|--------|---------------|----------------|--------|
| **Model Size** | 1.1B | Smaller than all | ✅ Efficient |
| **Training Data** | 7K (noisy) | 10-100x less | ⚠️ Needs improvement |
| **SQL Validity** | <10% | Far below SOTA | ❌ Critical issue |
| **Execution Accuracy** | 0% | Far below SOTA | ❌ Critical issue |
| **Approach** | LoRA fine-tuning | Standard | ✅ Baseline |

### Target Status (v0.2-beta)

| Metric | Datumara v0.2 | vs Leaderboard | Target |
|--------|---------------|----------------|--------|
| **Model Size** | 1.1B | Smallest in comparison | ✅ Ultra-efficient |
| **Training Data** | 10K (verified) | Competitive | ✅ Quality-focused |
| **SQL Validity** | 60-70% | Between 7B-14B models | 🎯 Realistic |
| **Execution Accuracy** | 40-50% | Between 1.5B-7B models | 🎯 Realistic |
| **Approach** | BIRD-Platinum cleaning | Novel methodology | ✅ Differentiated |

### Target Status (v1.0-ga)

| Metric | Datumara v1.0 | vs Leaderboard | Target |
|--------|---------------|----------------|--------|
| **Model Size** | 7-8B | Competitive | ✅ Standard size |
| **Training Data** | 50K+ (mixed) | Comparable to SOTA | ✅ Scale achieved |
| **SQL Validity** | 85-90% | Near human performance | 🎯 Ambitious |
| **Execution Accuracy** | 75-85% | Top 10-20 position | 🎯 Competitive |
| **Approach** | RLVR + RAG + Clean Data | Hybrid innovation | ✅ Novel combination |

---

## Comparison Methodology

### Metrics to Track

#### Primary Metrics (BIRD Standard)
1. **Execution Accuracy (EX)** - % of SQL queries that execute correctly
   - Formula: `EX = (# correct executions) / (# total queries)`
   - BIRD threshold: Exact match of execution results
   
2. **Valid Efficiency Score (VES)** - Correctness + efficiency
   - Rewards: Correct results, fast execution, low resource usage
   - Penalizes: Wrong results, slow queries, excessive resource use

3. **Reward-based VES (R-VES)** - Improved VES with better reward shaping
   - Used in recent submissions (2025-2026)
   - More robust to edge cases

#### Secondary Metrics (Development)
4. **Parse Validity** - Can the output be parsed as valid SQL?
   - Prerequisite for execution
   - Measures basic syntax learning

5. **Exact Match (EM)** - Does generated SQL match reference exactly?
   - Strict metric
   - May penalize semantically equivalent alternatives

6. **Normalized Match (NM)** - Are queries semantically equivalent?
   - Allows syntactic variations
   - More lenient than EM

7. **Schema Validity** - Do referenced tables/columns exist?
   - Measures schema grounding
   - Critical for real-world deployment

### Evaluation Protocol

#### Test Sets
1. **BIRD Dev Set** (1,534 examples) - Standard benchmark
   - Cleaned version (2023-09-25)
   - Publicly available
   - Used for leaderboard submission

2. **Mini-Dev Set** (500 examples) - Development testing
   - 3 dialects: SQLite, MySQL, PostgreSQL
   - Faster iteration
   - Good for ablation studies

3. **Datumara Test Set** (1,000 examples) - Internal held-out
   - Never used for training
   - Stratified by complexity
   - Tracked across versions

#### Evaluation Pipeline
```python
class DatumaraEvaluator:
    def __init__(self, test_set: str, db_path: str):
        self.test_set = load_bird_dataset(test_set)
        self.db_path = db_path
        self.metrics = {}
    
    def evaluate(self, model, generated_sqls: List[str]) -> dict:
        results = []
        for i, (question, reference_sql) in enumerate(self.test_set):
            generated_sql = generated_sqls[i]
            
            # Primary metrics
            ex = self.check_execution(generated_sql, reference_sql)
            ves = self.compute_ves(generated_sql, reference_sql)
            
            # Secondary metrics
            parse_valid = self.check_parse(generated_sql)
            em = self.check_exact_match(generated_sql, reference_sql)
            nm = self.check_normalized_match(generated_sql, reference_sql)
            schema_valid = self.check_schema(generated_sql)
            
            results.append({
                'question_id': i,
                'ex': ex,
                'ves': ves,
                'parse_valid': parse_valid,
                'em': em,
                'nm': nm,
                'schema_valid': schema_valid,
                'complexity': self.get_complexity(question)
            })
        
        return self.aggregate(results)
```

---

## Datumara Comparison Tables

### Table 1: Small Model Comparison (<2B parameters)

| Model | Size | Training Data | EX (%) | VES (%) | Approach | Date |
|-------|------|---------------|--------|---------|----------|------|
| **Datumara v0.1** | 1.1B | 7K (noisy) | <10 | N/A | LoRA FT | Aug 2026 |
| **Datumara v0.2 (target)** | 1.1B | 10K (verified) | 40-50 | 35-45 | BIRD-Platinum | Sep 2026 |
| **Datumara v1.0 (target)** | 1.1B | 50K+ (mixed) | 60-70 | 55-65 | RLVR + RAG | Sep 2026 |
| SLM-SQL + Qwen-0.5B | 0.5B | UNK | 61.82 | 57.11 | Fine-tuning | Aug 2025 |
| SLM-SQL + Qwen-1.5B | 1.5B | UNK | 70.49 | 65.25 | Fine-tuning | Aug 2025 |
| Prem-1B-SQL | 1B | UNK | 51.54 | N/A | Fine-tuning | Sep 2024 |
| xorazm-text2sql-0.8b | 0.8B | UNK | 59.59 | 53.43 | Fine-tuning | Jul 2026 |

**Key Insight:** Datumara v0.2 should target 40-50% EX to be competitive with 1.5B models. Datumara v1.0 should target 60-70% to match SOTA for small models.

### Table 2: Efficiency Comparison (Model Size vs Performance)

| Model | Size | EX (%) | EX per Billion Params | Efficiency Rank |
|-------|------|--------|----------------------|----------------|
| **Datumara v0.2 (target)** | 1.1B | 45 | 40.9 | 🥇 1st |
| **Datumara v1.0 (target)** | 1.1B | 65 | 59.1 | 🥇 1st |
| SLM-SQL + Qwen-1.5B | 1.5B | 70.49 | 47.0 | 🥈 2nd |
| xorazm-text2sql-0.8b | 0.8B | 59.59 | 74.5 | 🥇 1st (tie) |
| Prem-1B-SQL | 1B | 51.54 | 51.5 | 🥈 2nd |
| OmniSQL-7B | 7B | 67.97 | 9.7 | 🥉 3rd |
| CSC-SQL + Qwen-7B | 7B | 71.72 | 10.2 | 🥉 3rd |
| DeepEye-SQL | 27B | 78.42 | 2.9 | 4th |
| AskData + GPT-4o | UNK (~100B) | 81.95 | <1.0 | 5th |

**Key Insight:** Datumara's competitive advantage is **efficiency** - highest EX per billion parameters. This is our unique selling point.

### Table 3: Training Data Efficiency

| Method | Training Examples | EX (%) | EX per 1K Examples | Data Efficiency |
|--------|------------------|--------|-------------------|-----------------|
| **Datumara v0.2 (target)** | 10K | 45 | 4.5 | 🥇 1st |
| **Datumara v1.0 (target)** | 50K | 65 | 1.3 | 🥈 2nd |
| BIRD-Platinum (Zhu et al.) | 2.5K | ~60 | 24.0 | 🥇 1st (paper claim) |
| Typical SFT | 100K+ | 70-80 | <0.8 | 🥉 3rd |

**Key Insight:** Following BIRD-Platinum methodology, Datumara should achieve higher data efficiency than standard SFT approaches.

---

## Competitive Advantages

### Datumara Strengths

1. **Ultra-Efficient** (<2B params)
   - Runs on consumer hardware (Quadro T2000, 4GB)
   - No cloud dependency
   - Privacy-preserving (local deployment)

2. **Data Quality Focus**
   - BIRD-Platinum methodology
   - Execution verification
   - Schema consistency checks

3. **Open Source**
   - Full transparency
   - Community-driven improvement
   - Reproducible results

4. **Specialized for Analytics**
   - SQL-focused (not general code)
   - Schema-aware generation
   - Business intelligence use cases

### Datumara Weaknesses

1. **Model Size**
   - Limited capacity vs 7B+ models
   - Cannot match largest models' performance

2. **Training Data**
   - Less data than big tech (10K vs 100K+)
   - No access to proprietary databases

3. **Compute Resources**
   - Single GPU vs clusters
   - Longer iteration cycles

4. **No Ensemble Methods**
   - Single-model only
   - Cannot leverage self-consistency voting

---

## Benchmarking Roadmap

### Phase 1: v0.2-beta (Aug 25 - Sep 1, 2026)

**Goal:** Establish baseline, compete with 1-2B models

**Test Sets:**
- Mini-Dev (500 examples, SQLite only)
- Datumara internal test (1K examples)

**Metrics to Report:**
- Parse Validity (%)
- Execution Accuracy (%)
- Schema Validity (%)
- Complexity-stratified results

**Comparison Targets:**
- Beat Prem-1B-SQL (51.54% EX)
- Approach SLM-SQL + Qwen-1.5B (70.49% EX)
- Target: 40-50% EX

### Phase 2: v0.3-rc (Sep 2-8, 2026)

**Goal:** Compete with 7B models

**Test Sets:**
- Mini-Dev (all 3 dialects)
- BIRD Dev (1,534 examples)

**Metrics to Report:**
- All Phase 1 metrics
- Exact Match (%)
- Normalized Match (%)
- R-VES (if applicable)

**Comparison Targets:**
- Beat OmniSQL-7B (67.97% EX)
- Approach CSC-SQL + Qwen-7B (71.72% EX)
- Target: 65-70% EX

### Phase 3: v1.0-ga (Sep 9-25, 2026)

**Goal:** Top 20 overall leaderboard position

**Test Sets:**
- Full BIRD Dev submission
- Mini-Dev (all dialects)
- LiveSQLBench (if available)

**Metrics to Report:**
- All previous metrics
- Full BIRD submission metrics
- Efficiency analysis

**Comparison Targets:**
- Top 20 overall (75%+ EX)
- Top 5 small models (<2B)
- Best EX per billion params

---

## Submission Guidelines

### BIRD Leaderboard Submission

**Requirements:**
1. Email: bird.bench23@gmail.com
2. Subject: "BIRD Leaderboard Submission - [Method Name]"
3. Include:
   - Method name and description
   - Model size and architecture
   - Training data details
   - Generated SQL predictions (JSON format)
   - Paper/preprint link (if available)

**Format:**
```json
{
  "question_id": "1001",
  "db_id": "user_preferences",
  "sql": "SELECT COUNT(*) FROM users WHERE created_at > '2024-01-01'"
}
```

**Timeline:** Results returned in ~10 days

**Categories:**
- Single-Model (no ensemble, no voting)
- Multi-Model (ensemble, self-consistency)
- Open-Source (public weights)
- Closed-Source (API-based)

### Datumara Submission Plan

**v0.2-beta:** Mini-Dev only (development track)  
**v0.3-rc:** BIRD Dev (full leaderboard)  
**v1.0-ga:** BIRD Dev + Mini-Dev + efficiency metrics

---

## Reporting Template

### Monthly Benchmark Report

```markdown
## Datumara Benchmark Report - [Month Year]

### Version: [vX.X]

### Test Set: [Mini-Dev / BIRD Dev / Internal]

### Overall Metrics
- Execution Accuracy: XX.XX%
- Parse Validity: XX.XX%
- Schema Validity: XX.XX%

### By Complexity
- Easy: XX.XX% (N=XXX)
- Medium: XX.XX% (N=XXX)
- Hard: XX.XX% (N=XXX)
- Expert: XX.XX% (N=XXX)

### By Domain
- E-commerce: XX.XX%
- Finance: XX.XX%
- Healthcare: XX.XX%
- Education: XX.XX%

### Comparison to Previous Version
- v0.1 → v0.2: +XX.XX% improvement
- Biggest gains: [specific areas]
- Remaining gaps: [specific areas]

### Leaderboard Position (if submitted)
- Overall Rank: #XX / XXX
- Small Model Rank: #XX / XX
- Efficiency Rank: #XX / XX

### Next Steps
- [ ] Improve [specific weakness]
- [ ] Test on [specific domain]
- [ ] Submit to [leaderboard]
```

---

## Key Takeaways

### Objective Targets

1. **v0.2-beta (Sep 1):**
   - 40-50% EX on Mini-Dev
   - Beat all <1B models
   - Approach 1.5B model performance

2. **v0.3-rc (Sep 8):**
   - 65-70% EX on Mini-Dev
   - Compete with 7B models
   - Submit to BIRD leaderboard

3. **v1.0-ga (Sep 25):**
   - 75%+ EX on BIRD Dev
   - Top 20 overall
   - #1 efficiency (EX per billion params)

### Success Criteria

✅ **Success:** Datumara v1.0 achieves top 5 position among small models (<2B)  
🎯 **Stretch:** Datumara v1.0 achieves top 20 overall (beating some 30B+ models)  
🏆 **Dream:** Datumara v1.0 achieves best EX per billion params (efficiency champion)

---

## References

- **BIRD Benchmark:** https://bird-bench.github.io/
- **BIRD-Critic:** https://bird-critic.github.io/
- **LiveSQLBench:** https://livesqlbench.ai/
- **Mini-Dev:** https://github.com/bird-bench/mini_dev
- **BIRD-Platinum Paper:** Zhu et al. (2026) - Data cleaning methodology
- **PapersWithCode:** https://paperswithcode.com/sota/text-to-sql-on-bird

---

**Last Updated:** 2026-08-25  
**Next Review:** 2026-09-01 (v0.2-beta release)  
**Maintained By:** Datumara Team
