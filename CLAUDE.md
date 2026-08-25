# Claude Code Instructions

> **Router File:** This file directs Claude Code to the comprehensive documentation.

**Read this first:** `AGENT.md`

**Complete project context:** `PROJECT_CONTEXT.md`

---

## Why This File Exists

Claude Code looks for `CLAUDE.md` by convention. This file ensures Claude finds the right documentation.

**All instruction content is in:** `PROJECT_CONTEXT.md`

---

## Quick Context

- **Project:** Datumara - SQL generation LLM
- **Current:** v0.1-alpha → v0.2-beta (2026-09-01)
- **Goal:** 60-70% SQL validity via execution-guided verification
- **Data:** 14K examples with unique BUG→FIX and BASE→OPTIMIZED pairs
- **Issue:** Noisy training data (<10% valid SQL despite loss: 2.3→0.12)

**Check first:** `docs/plans/BACKLOG.md` for priorities

---

**Full instructions:** See `AGENT.md` in root directory.
