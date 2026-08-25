# AI Agent Instructions

> **This is the only file you need to read.**

For all project context, instructions, and guidance, read:

**`PROJECT_CONTEXT.md`**

---

## Why This File Exists

Different AI agents look for different instruction files:
- VS Code Copilot → `.github/copilot-instructions.md`
- Cursor → `.cursorrules`
- Claude Code → `CLAUDE.md`
- Others → `AGENT.md`, `INSTRUCTIONS.md`, etc.

**Solution:** This file ensures any agent finds its way to the comprehensive documentation, regardless of which file it discovers first.

---

## File Routing

- **`AGENT.md`** (this file) → Universal entry point
- **`.github/copilot-instructions.md`** → VS Code/GitHub Copilot router
- **`PROJECT_CONTEXT.md`** → **Single source of truth** (read this)

All other instruction files are routers that point to `PROJECT_CONTEXT.md`.

---

## Quick Context

- **Project:** Datumara - Open-source analytics LLM for SQL generation
- **Goal:** Turn business questions into schema-aware SQL
- **Current:** v0.1-alpha → v0.2-beta (target: 60-70% SQL validity by 2026-09-01)
- **Key Issue:** Training works (loss: 2.3→0.12), but data is noisy (<10% valid SQL)
- **Solution:** Execution-guided verification (Zhu et al. 2026)

**Start here:** `docs/plans/BACKLOG.md` for current priorities.

---

**Repository:** https://github.com/achagani/datumara  
**Full Documentation:** `PROJECT_CONTEXT.md`
