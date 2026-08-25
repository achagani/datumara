# Datumara Versioning Strategy

**Last Updated:** 2026-08-25  
**Current Version:** v0.1-alpha

---

## Version Numbering

Datumara follows **Semantic Versioning** (SemVer) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR** (1.x.x): Breaking changes or production-ready releases
- **MINOR** (0.x.x): New features, improvements, significant quality gains
- **PATCH** (0.0.x): Bug fixes, minor improvements

### Pre-release Labels

- **-alpha**: Early testing, proof of concept, not feature-complete
- **-beta**: Feature-complete, quality improvements in progress
- **-rc** (release candidate): Production-ready candidate, final testing
- **(no label)**: Production-ready, stable

---

## Version History

### v0.1-alpha (2026-08-25) - Current

**Status:** Proof of Concept ✅

**What Works:**
- ✅ Training pipeline with checkpointing
- ✅ LoRA fine-tuning on TinyLlama 1.1B
- ✅ Export to Ollama format
- ✅ Loss convergence (2.3 → 0.12)

**What Doesn't Work:**
- ❌ SQL generation quality (<10% validity)
- ❌ Tokenization artifacts
- ❌ No schema grounding
- ❌ No execution verification

**Training Data:** 7,000 examples (unverified quality)  
**Model Size:** 1.1B parameters  
**LoRA Rank:** 8

**Use Case:** Development and testing only. **Not for production.**

---

### v0.2-beta (Target: 2026-09-01)

**Status:** In Development

**Goals:**
- [ ] Clean and normalize 14K+ acquired datasets
- [ ] Execute verification pipeline (schema + execution)
- [ ] Create Datumara-Platinum dataset (~10K high-quality examples)
- [ ] Retrain with same config, better data

**Expected Improvements:**
- Training loss: <0.10
- SQL validity: 60-70%
- Execution accuracy: 40-50%
- Reduced tokenization artifacts

**Training Data:** 10,000+ examples (verified quality)  
**Model Size:** 1.1B parameters  
**LoRA Rank:** 8 (unchanged)

**Use Case:** Beta testing, internal evaluation. **Not for production.**

---

### v0.3-rc (Target: 2026-09-08)

**Status:** Planned

**Goals:**
- [ ] Increase LoRA rank (8 → 16 or 32)
- [ ] Extend training (5000+ steps)
- [ ] Add schema grounding (RAG with database metadata)
- [ ] Implement execution-guided decoding
- [ ] Comprehensive evaluation suite

**Expected Improvements:**
- Training loss: <0.05
- SQL validity: 75-80%
- Execution accuracy: 60-70%
- Valid SQL generation
- Schema-aware outputs

**Training Data:** 10K+ examples + schema metadata  
**Model Size:** 1.1B parameters  
**LoRA Rank:** 16-32

**Use Case:** Release candidate, external testing. **Close to production-ready.**

---

### v1.0-ga (Target: 2026-09-25)

**Status:** Planned

**Goals:**
- [ ] Scale to 7B+ parameter model (Llama-3-8B or Qwen2.5-7B)
- [ ] Implement RLVR (reinforcement learning with verification)
- [ ] Generate synthetic training data (GPT-4 augmentation)
- [ ] Acquire BIRD-Platinum via author collaboration
- [ ] Production deployment pipeline
- [ ] Comprehensive documentation and API

**Expected Improvements:**
- Training loss: <0.03
- SQL validity: 85-90%
- Execution accuracy: 75-85%
- Production-grade reliability
- Full evaluation suite

**Training Data:** 50K+ examples (mixed real + synthetic)  
**Model Size:** 7-8B parameters  
**LoRA Rank:** 32+

**Use Case:** **Production-ready**, general availability.

---

## Future Versions (Post-1.0)

### v1.1.x - Maintenance
- Bug fixes
- Performance optimizations
- Minor quality improvements

### v1.2.x - Features
- New database dialects
- Advanced RAG techniques
- Multi-turn SQL conversation

### v2.0.0 - Next Generation
- Larger models (70B+)
- Multi-modal SQL (text + schema + examples)
- Real-time learning from execution feedback

---

## Version Release Criteria

### Alpha (0.x-alpha)
- [ ] Training pipeline works
- [ ] Model can be exported
- [ ] Loss converges
- [ ] Basic functionality demonstrated

### Beta (0.x-beta)
- [ ] Feature-complete architecture
- [ ] Quality metrics tracked
- [ ] Known issues documented
- [ ] Internal testing possible

### Release Candidate (0.x-rc)
- [ ] All features implemented
- [ ] Quality metrics meet threshold (>75% validity)
- [ ] Evaluation suite complete
- [ ] External testing possible
- [ ] Documentation draft

### General Availability (x.0.0)
- [ ] Production quality (>85% validity)
- [ ] Comprehensive evaluation
- [ ] Full documentation
- [ ] Deployment pipeline automated
- [ ] Support infrastructure ready

---

## Quality Metrics by Version

| Version | Training Loss | SQL Validity | Execution Accuracy | Production Ready |
|---------|--------------|--------------|-------------------|------------------|
| **v0.1-alpha** | 0.12 | <10% | 0% | ❌ No |
| **v0.2-beta** | <0.10 | 60-70% | 40-50% | ❌ No |
| **v0.3-rc** | <0.05 | 75-80% | 60-70% | ⚠️ Maybe |
| **v1.0-ga** | <0.03 | 85-90% | 75-85% | ✅ Yes |
| **v2.0** | <0.01 | 90-95% | 85-90% | ✅ Yes |

---

## Branching Strategy

```
main          - Production-ready code (v1.0+)
develop       - Integration branch for features
feature/*     - Individual features
release/*     - Release preparation (e.g., release/v0.2-beta)
hotfix/*      - Critical fixes for production
```

### Tagging Convention

```bash
# Alpha releases
git tag -a v0.1-alpha -m "Proof of concept"

# Beta releases
git tag -a v0.2-beta -m "Clean data retraining"

# Release candidates
git tag -a v0.3-rc1 -m "First release candidate"
git tag -a v0.3-rc2 -m "Second release candidate"

# Production releases
git tag -a v1.0.0 -m "General availability"
git tag -a v1.0.1 -m "Bug fixes"
```

---

## Model Checkpointing

Each version corresponds to specific training checkpoints:

### v0.1-alpha
- Base: `models/local-tinyllama-checkpoint/checkpoint_final_2000`
- Exported: `datumara-local` (Ollama)
- Config: LoRA rank=8, 2000 steps, 7K examples

### v0.2-beta (planned)
- Base: `models/local-tinyllama-checkpoint-v0.2/checkpoint_best`
- Exported: `datumara-local-v0.2` (Ollama)
- Config: LoRA rank=8, 3000 steps, 10K+ verified examples

### v0.3-rc (planned)
- Base: `models/local-tinyllama-checkpoint-v0.3/checkpoint_best`
- Exported: `datumara-local-v0.3-rc` (Ollama)
- Config: LoRA rank=16-32, 5000+ steps, schema grounding

### v1.0-ga (planned)
- Base: `models/qwen2.5-7b-checkpoint-v1.0/checkpoint_best`
- Exported: `datumara` (Ollama) + HuggingFace upload
- Config: 7B model, RLVR, 10K+ steps, 50K+ examples

---

## Decision Log

### 2026-08-25: Version Numbering Decision

**Decision:** Start at v0.1-alpha instead of v1.0

**Rationale:**
- Current model quality is not production-ready
- Calling it v1.0 would set wrong expectations
- Incremental versioning allows for iterative improvement
- Follows industry best practices for ML models

**Alternatives Considered:**
- Start at v1.0: Rejected - implies production readiness
- Use date-based versioning: Rejected - less clear progression
- Use build numbers only: Rejected - lacks semantic meaning

**Stakeholders:**
- @achagani (decision maker)
- Based on user feedback: "i wouldn't call it 1.0 until we have achieved a good enough version"

---

## References

- [Semantic Versioning Specification](https://semver.org/)
- [ML Model Versioning Best Practices](https://mlflow.org/docs/latest/model.html)
- [HuggingFace Model Versioning](https://huggingface.co/docs/hub/models-versioning)

---

**Next Version:** v0.2-beta  
**Target Date:** 2026-09-01  
**Key Milestone:** Clean data retraining with execution verification
