# GitHub Copilot Instructions

> **Router File:** This file directs VS Code Copilot to the comprehensive documentation.

**Read this first:** `../AGENT.md`

**Complete project context:** `../PROJECT_CONTEXT.md`

---

## Why This File Exists

VS Code Copilot automatically reads `.github/copilot-instructions.md`. This file ensures Copilot finds the right documentation.

**All instruction content is in:** `PROJECT_CONTEXT.md`

---

## Quick Context for Copilot

- **Project:** Datumara - SQL generation LLM
- **Current:** v0.1-alpha → v0.2-beta (2026-09-01)
- **Goal:** 60-70% SQL validity via execution-guided verification
- **Data:** 14K examples (bird23, mini_dev, bird_critic, effi_sql)
- **Issue:** Noisy training data (<10% valid SQL despite loss: 2.3→0.12)

**Check first:** `docs/plans/BACKLOG.md` for priorities

---

**Full instructions:** See `AGENT.md` in root directory.
