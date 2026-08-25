# Datumara Strategy: Outperforming Frontier Models on SQL

**Version:** 1.0  
**Date:** August 25, 2026  
**Goal:** Beat GPT-4/Claude on real-world SQL generation within 2-4 weeks

---

## Executive Summary

Frontier models (GPT-4, Claude 3.5) achieve ~85-90% accuracy on SQL benchmarks but have **critical weaknesses**:
1. ❌ Schema-agnostic (guess at table/column names)
2. ❌ Static knowledge (can't learn from corrections)
3. ❌ No execution feedback (optimize for text, not correctness)
4. ❌ Generalist (not SQL-specialized)

**Our asymmetric advantage:** Deep integration + execution guidance + continuous learning

**Target:** 90-95% execution accuracy on business SQL queries (vs. 80-85% for GPT-4 on same domain)

---

## Research Findings: State of the Art (August 2026)

### Key Papers & Learnings:

#### 1. **Human-Level Text-to-SQL via RLVR** (Zhu et al., Aug 2026)
- **Finding:** Simple fine-tuning + RL on **verified data** beats complex pipelines
- **Result:** 92.96% accuracy (first to reach human-level)
- **Key Insight:** 61% of training data has annotation errors - **data quality > model size**
- **Our Action:** Implement execution-guided verification immediately

#### 2. **RASL: Retrieval Augmented Schema Linking** (Eben et al., Jul 2025)
- **Finding:** Schema retrieval beats fine-tuning for massive databases
- **Approach:** Vector-index schema components, retrieve top-k relevant tables
- **Result:** High recall without domain-specific fine-tuning
- **Our Action:** Build RAG schema linker in Week 1

#### 3. **LitE-SQL: Execution-Guided Self-Correction** (Piao et al., Jan 2026)
- **Finding:** Test-time execution + self-correction improves accuracy 15-20%
- **Method:** Generate → Execute → Detect error → Revise
- **Our Action:** Add execution validator to inference pipeline

#### 4. **Think2SQL: Reinforcement Learning for Reasoning** (Papicchio et al., Apr 2026)
- **Finding:** Reward shaping for reasoning steps > result-only rewards
- **Technique:** Process rewards for schema linking, JOIN detection, aggregation
- **Our Action:** Implement multi-component reward function

#### 5. **SQuaD-SQL: Knowledge Distillation** (Wu et al., Jul 2026)
- **Finding:** Small models (1-3B) can match large models with proper distillation
- **Method:** LLM teacher → Small student + execution feedback
- **Our Action:** Use GPT-4 to generate training data, distill into Datumara

---

## Winning Strategy: 4-Week Sprint

### Week 1: Schema-Aware Foundation ✅
**Goal:** Never hallucinate table/column names

#### 1.1 Schema Grounding Layer
```python
class SchemaGroundedGenerator:
    def __init__(self, model, schema_index):
        self.model = model
        self.schema_index = schema_index  # Vector DB
    
    def generate(self, question, database_schema):
        # Retrieve relevant tables
        relevant_tables = self.schema_index.search(question, top_k=5)
        
        # Build schema context
        context = f"""
        Database Schema:
        {database_schema}
        
        Relevant Tables: {relevant_tables}
        
        Question: {question}
        SQL:"""
        
        return self.model.generate(context)
```

**Implementation:**
- Use ChromaDB or FAISS for schema indexing
- Embed table names, column names, descriptions
- Retrieve top-5 most relevant tables per query

**Expected Impact:** +15-20% accuracy (eliminates hallucination errors)

---

### Week 2: Execution-Guided Training 🎯
**Goal:** Optimize for execution success, not text similarity

#### 2.1 Execution-Guided Loss Function
```python
def execution_guided_loss(model, batch, test_database):
    questions = batch["question"]
    reference_sql = batch["sql"]
    expected_results = execute_on_db(reference_sql, test_database)
    
    # Generate SQL
    generated_sql = model.generate(questions)
    
    # Execute and compare results
    losses = []
    for gen_sql, expected in zip(generated_sql, expected_results):
        try:
            actual = execute_on_db(gen_sql, test_database)
            # Result-based loss (not text-based!)
            loss = 1 - result_similarity(actual, expected)
        except Exception as e:
            loss = 1.0  # Invalid SQL = maximum loss
        
        losses.append(loss)
    
    return mean(losses)
```

#### 2.2 Self-Correction Loop
```python
def generate_with_correction(model, question, schema, max_attempts=3):
    for attempt in range(max_attempts):
        sql = model.generate(question, schema)
        
        # Validate
        is_valid, error = validate_sql(sql, schema)
        if is_valid:
            return sql
        
        # Learn from error
        correction_prompt = f"""
        Generated SQL: {sql}
        Error: {error}
        
        Fix the SQL:"""
        
        sql = model.generate(correction_prompt)
    
    return sql  # Return best effort
```

**Expected Impact:** +10-15% accuracy (optimizes for what matters)

---

### Week 3: Data Amplification 📊
**Goal:** 10x training data with synthetic generation

#### 3.1 Synthetic Data Pipeline
```python
def generate_synthetic_data(schema, seed_questions, llm_teacher):
    synthetic_data = []
    
    for seed_q in seed_questions:
        # Generate variations
        variations = llm_teacher.generate(f"""
        Original question: {seed_q}
        Generate 10 semantically similar questions:
        """)
        
        for variation in variations:
            # Generate SQL with GPT-4
            sql = llm_teacher.generate(f"""
            Schema: {schema}
            Question: {variation}
            SQL:""")
            
            # Verify execution
            if execute_and_verify(sql):
                synthetic_data.append({
                    "question": variation,
                    "sql": sql,
                    "schema": schema
                })
    
    return synthetic_data
```

#### 3.2 Data Sources to Mine:
1. ✅ Spider dataset (10K examples)
2. ✅ BIRD dataset (12K examples)
3. ✅ WikiSQL (80K examples, simpler)
4. 🎯 StackOverflow SQL questions (scrape)
5. 🎯 GitHub SQL queries (BigQuery public datasets)
6. 🎯 dbt package examples (analytics engineering)
7. 🎯 Mode Analytics public queries
8. 🎯 Kaggle SQL notebooks

**Target:** 100K+ high-quality examples (vs. 7K currently)

**Expected Impact:** +10-15% accuracy (more diverse training)

---

### Week 4: Test-Time Compute & Ensemble 🚀
**Goal:** Beat GPT-4 on hard queries with smart inference

#### 4.1 Multi-Candidate Generation
```python
def generate_with_verification(model, question, schema, n_candidates=5):
    candidates = []
    
    # Generate multiple candidates (temperature sampling)
    for _ in range(n_candidates):
        sql = model.generate(question, schema, temperature=0.7)
        candidates.append(sql)
    
    # Execute all candidates
    scored = []
    for sql in candidates:
        try:
            result = execute_on_db(sql)
            score = evaluate_result_quality(result)
            scored.append((sql, score))
        except:
            scored.append((sql, -1))  # Invalid
    
    # Return best valid SQL
    best = max(scored, key=lambda x: x[1])
    return best[0]
```

#### 4.2 Confidence Estimation
```python
def predict_correctness(model, question, sql):
    # Features that predict correctness:
    features = {
        "syntax_valid": check_syntax(sql),
        "tables_exist": verify_tables(sql, schema),
        "columns_exist": verify_columns(sql, schema),
        "execution_time": measure_execution_time(sql),
        "result_size": count_result_rows(sql),
        "similarity_to_training": semantic_similarity(sql, training_sqls)
    }
    
    # Trained classifier predicts correctness
    confidence = correctness_classifier.predict(features)
    return confidence
```

**Strategy:**
- If confidence > 0.9: Return immediately
- If confidence 0.6-0.9: Generate 5 candidates, pick best
- If confidence < 0.6: Ask for clarification or escalate

**Expected Impact:** +5-10% accuracy on hard queries

---

## Architecture: Datumara v2.0

```
┌─────────────────────────────────────────────────┐
│              User Query                          │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│         Intent Classifier                        │
│  (SQL | Stats | Analysis | Insights)            │
└──────────┬──────────────────────────────────────┘
           ↓
    ┌──────┴──────┐
    │ SQL Query   │
    └──────┬──────┘
           ↓
┌─────────────────────────────────────────────────┐
│      Schema Retriever (RAG)                      │
│  - Vector search tables/columns                 │
│  - Return top-5 relevant schema                 │
└──────────┬──────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│     Datumara Model (LoRA Fine-tuned)            │
│  - Base: TinyLlama 1.1B                         │
│  - LoRA: SQL specialist                         │
│  - Context: Retrieved schema                    │
└──────────┬──────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│      Execution Validator                        │
│  - Run SQL on test DB                           │
│  - Check for errors                             │
│  - Verify result makes sense                    │
└──────────┬──────────────────────────────────────┘
           ↓
    ┌──────┴──────┐
    │   Valid?    │
    └──┬─────┬────┘
       │     │
    Yes│     │No
       │     └──────────────────────────┐
       ↓                                ↓
┌──────────────┐            ┌──────────────────────┐
│ Return SQL   │            │ Self-Correction Loop │
│ to User      │            │ (max 3 attempts)     │
└──────────────┘            └──────────┬───────────┘
                                       ↓
                              ┌────────────────────┐
                              │ Still Fails?       │
                              │ Return Error +     │
                              │ Suggestion         │
                              └────────────────────┘
```

---

## Metrics & Benchmarks

### Target Metrics (4 Weeks):

| Metric | Current | Week 4 Target | GPT-4 Baseline |
|--------|---------|---------------|----------------|
| **Simple SELECT** | - | 95% | 95-98% |
| **Basic JOINs (2-3 tables)** | - | 90% | 90-95% |
| **Aggregations + GROUP BY** | - | 88% | 90-95% |
| **Complex JOINs (5+ tables)** | - | 80% | 85-90% |
| **Subqueries / CTEs** | - | 75% | 85-90% |
| **Execution Accuracy (Overall)** | - | **88-92%** | 85-90% |
| **Inference Latency** | - | <100ms | 500-2000ms |
| **Hallucination Rate** | - | <2% | 10-15% |

### Benchmark Datasets:

1. **Spider** (academic, complex queries)
   - Target: 85%+ execution accuracy
   - Current SOTA: ~88%

2. **BIRD** (business scenarios, large DBs)
   - Target: 80%+ execution accuracy
   - Current SOTA: ~82%

3. **Real User Queries** (most important!)
   - Collect from early users
   - Target: 90%+ satisfaction

---

## Implementation Checklist

### Week 1: Schema-Aware Foundation
- [ ] Set up ChromaDB/FAISS for schema indexing
- [ ] Implement schema retrieval function
- [ ] Modify training data to include schema context
- [ ] Test on 100 queries (measure hallucination rate)

### Week 2: Execution-Guided Training
- [ ] Set up test database (SQLite for speed)
- [ ] Implement execution-guided loss function
- [ ] Add self-correction loop to inference
- [ ] Retrain model with new loss (2-4 hours)

### Week 3: Data Amplification
- [ ] Scrape StackOverflow SQL questions
- [ ] Extract GitHub SQL queries
- [ ] Generate synthetic variations with GPT-4
- [ ] Filter for quality (execute & verify)
- [ ] Retrain on 100K examples (6-8 hours)

### Week 4: Test-Time Compute
- [ ] Implement multi-candidate generation
- [ ] Build correctness classifier
- [ ] Add confidence-based routing
- [ ] Benchmark vs. GPT-4 on 500 queries

---

## Resource Requirements

### Compute:
- **Training:** 4GB GPU (your Quadro T2000) ✅
- **Inference:** CPU or any GPU ✅
- **Schema Index:** Minimal (runs locally) ✅

### Data:
- **Current:** 7K examples ✅
- **Target:** 100K examples (synthetic + scraped)
- **Cost:** ~$50-100 for GPT-4 API (data generation)

### Time:
- **Development:** 2-3 weeks
- **Training:** 2-4 hours per iteration
- **Total:** ~4 weeks to production-ready

---

## Risk Mitigation

### Risk 1: Data Quality Issues
**Mitigation:** Execute every generated SQL, discard invalid ones

### Risk 2: Overfitting to Training Data
**Mitigation:** Keep 20% as validation, monitor gap

### Risk 3: Slow Inference
**Mitigation:** Multi-candidate only for low-confidence queries

### Risk 4: Schema Changes
**Mitigation:** RAG approach - just re-index, no retraining

---

## Success Criteria

**After 4 weeks, we win if:**

1. ✅ **Execution accuracy >90%** on common business queries
2. ✅ **Hallucination rate <2%** (schema-grounded)
3. ✅ **Inference <100ms** (local, fast)
4. ✅ **Zero hallucinated tables/columns** (RAG prevents this)
5. ✅ **Better than GPT-4** on YOUR database (schema advantage)

**We lose if:**
- ❌ Still generating invalid SQL >10% of time
- ❌ Hallucinating table names
- ❌ Slower than GPT-4 API
- ❌ Can't handle 3+ table JOINs

---

## Next Actions (Start Today)

1. **Install ChromaDB:** `pip install chromadb`
2. **Index your schema:** Create vector embeddings of table/column names
3. **Modify training script:** Add schema context to prompts
4. **Set up test DB:** Create SQLite DB with sample data
5. **Implement execution validator:** Run generated SQL, check for errors

---

## Conclusion

**We CAN beat frontier models, but NOT by being a smaller version of them.**

**Win by:**
1. ✅ Schema awareness (they can't do this)
2. ✅ Execution optimization (they don't verify)
3. ✅ Continuous learning (they're static)
4. ✅ Local + fast (they're cloud-based)
5. ✅ Private (they send data to OpenAI)

**Timeline:** 4 weeks to production-ready, SQL-specialized model that outperforms GPT-4 on real business queries.

**Let's build!** 🚀
