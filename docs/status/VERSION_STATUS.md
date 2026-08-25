# Datumara Version Status

**Current Version:** v0.1-alpha  
**Last Updated:** 2026-08-25

---

## Quick Reference

| Version | Status | Quality | Use Case |
|---------|--------|---------|----------|
| **v0.1-alpha** | ✅ Complete | <10% valid SQL | Development/testing |
| **v0.2-beta** | 🔄 In Progress | 60-70% valid SQL | Internal evaluation |
| **v0.3-rc** | 📅 Planned | 75-80% valid SQL | External testing |
| **v1.0-ga** | 📅 Planned | 85-90% valid SQL | **Production** |

---

## Why v0.1 and Not v1.0?

**Simple answer:** The model isn't good enough yet.

**Detailed answer:**
- ✅ Training pipeline works perfectly
- ✅ Export to Ollama works
- ✅ Loss converges beautifully (2.3 → 0.12)
- ❌ **But:** SQL generation quality is <10% valid
- ❌ **But:** No evaluation metrics in place
- ❌ **But:** No schema grounding
- ❌ **But:** Production deployment would fail

**Lesson learned:** Don't call something v1.0 until it's actually ready for production.

---

## What Works in v0.1

```bash
✅ Training with checkpointing
✅ LoRA fine-tuning (2.25M params)
✅ Export to Ollama format
✅ Loss convergence (87% improvement)
✅ Resume from interruption
✅ Model serves in Ollama
```

## What Doesn't Work

```bash
❌ SQL generation quality (<10% valid)
❌ Tokenization artifacts in output
❌ Schema awareness
❌ Execution verification
❌ Production readiness
```

---

## Path to v1.0

### This Week → v0.2-beta
- Clean 14K+ acquired datasets
- Run execution verification
- Retrain with verified data
- **Target:** 60-70% SQL validity

### Next Week → v0.3-rc
- Increase LoRA rank (8 → 16-32)
- Add schema grounding (RAG)
- Extend training (5000+ steps)
- **Target:** 75-80% SQL validity

### Week 3-4 → v1.0-ga
- Scale to 7B+ parameter model
- Implement RLVR training
- Add synthetic data
- **Target:** 85-90% SQL validity, **production-ready**

---

## Download & Test v0.1

```bash
# Install
ollama pull datumara-local

# Test
ollama run datumara-local "Generate SQL to find total revenue"

# Expected output (v0.1-alpha):
# Garbled text, schema leakage, invalid SQL
# This is NORMAL for alpha version
```

---

## Versioning Philosophy

> "Release early, release often, but **don't lie about version numbers**."

- **v0.x.x** = "We're still figuring this out"
- **v1.0.0** = "You can trust this in production"
- **v2.0.0** = "We've learned a lot and made breaking changes"

**Current mindset:** We're in v0.x territory. Lots to learn, lots to improve.

---

## Key Documents

- [`VERSIONING.md`](VERSIONING.md) - Full versioning strategy and roadmap
- [`TRAINING_SUMMARY.md`](TRAINING_SUMMARY.md) - v0.1 training results
- [`DATA_ACQUISITION_REPORT.md`](DATA_ACQUISITION_REPORT.md) - Data pipeline status
- [`STRATEGY.md`](STRATEGY.md) - 4-week improvement plan
- [`BACKLOG.md`](BACKLOG.md) - Priority tasks

---

## Questions?

**Q: Can I use v0.1 in production?**  
**A:** Absolutely not. It will generate invalid SQL and break your workflows.

**Q: When is v1.0 coming?**  
**A:** Target: 2026-09-25 (4 weeks from now)

**Q: Should I wait for v1.0?**  
**A:** If you need production reliability, yes. If you want to experiment/contribute, start now!

**Q: How can I help?**  
**A:** Check the [backlog](BACKLOG.md), pick a task, and submit a PR!

---

**Bottom line:** v0.1 is a proof of concept. The foundation is solid, but the house isn't livable yet. Join us on the journey to v1.0! 🚀
