# Documentation Architecture

> **Single Source of Truth** + **Router Files** pattern

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SINGLE SOURCE OF TRUTH                   │
│                                                             │
│              PROJECT_CONTEXT.md (comprehensive)             │
│              - Complete project documentation               │
│              - Deep technical details                       │
│              - Research foundations                         │
│              - Full workflows                               │
└─────────────────────────────────────────────────────────────┘
                              ↑
                              |
        ┌─────────────────────┼─────────────────────┐
        |                     |                     |
┌───────┴────────┐   ┌────────┴────────┐   ┌───────┴────────┐
│   AGENT.md     │   │ .github/        │   │   CLAUDE.md    │
│   (universal)  │   │ copilot-        │   │   (Claude)     │
│                │   │ instructions.md │   │                │
│   Router for   │   │ (VS Code)       │   │   Router for   │
│   any agent    │   │                 │   │   Claude Code  │
│   that finds   │   │   Router for    │   │   that finds   │
│   it in root   │   │   VS Code       │   │   CLAUDE.md    │
└────────────────┘   └─────────────────┘   └────────────────┘
        ↑                     ↑                     ↑
        |                     |                     |
┌───────┴────────────────────────────────────────────────────┐
│                    .cursorrules                             │
│                    (Cursor IDE)                             │
│                    Router for Cursor                        │
└─────────────────────────────────────────────────────────────┘
```

---

## File Purposes

### **Single Source of Truth**

| File | Purpose | Lines | Audience |
|------|---------|-------|----------|
| `PROJECT_CONTEXT.md` | Complete documentation | ~430 | Humans + All agents |

### **Router Files**

| File | Purpose | Lines | Agent/IDE |
|------|---------|-------|-----------|
| `AGENT.md` | Universal entry point | ~30 | Any agent finding it in root |
| `.github/copilot-instructions.md` | VS Code router | ~20 | VS Code Copilot, GitHub Copilot |
| `CLAUDE.md` | Claude router | ~20 | Claude Code |
| `.cursorrules` | Cursor router | ~15 | Cursor IDE |

---

## How It Works

### Agent Discovery Paths

1. **VS Code Copilot:**
   - Auto-reads `.github/copilot-instructions.md`
   - → Directed to `AGENT.md`
   - → Directed to `PROJECT_CONTEXT.md` ✅

2. **Cursor:**
   - Reads `.cursorrules`
   - → Directed to `AGENT.md`
   - → Directed to `PROJECT_CONTEXT.md` ✅

3. **Claude Code:**
   - Reads `CLAUDE.md`
   - → Directed to `AGENT.md`
   - → Directed to `PROJECT_CONTEXT.md` ✅

4. **Any Other Agent:**
   - Finds `AGENT.md` in root
   - → Directed to `PROJECT_CONTEXT.md` ✅

---

## Benefits

### ✅ **No Duplication**
- All content lives in `PROJECT_CONTEXT.md`
- Router files are tiny (<30 lines each)
- Easy to maintain (update once, everywhere gets it)

### ✅ **Universal Compatibility**
- Works with any agent following any convention
- Future-proof (new agents will find something)
- Standard file names for each ecosystem

### ✅ **Clean Architecture**
- Single responsibility per file
- Clear separation: routers vs. content
- Easy to understand and extend

### ✅ **IDE/Agent Switching**
- Switch from VS Code to Cursor? Same content.
- Switch from Copilot to Claude? Same content.
- Add new agent? Just create a router.

---

## Router Pattern

All router files follow this pattern:

```markdown
# [Agent Name] Instructions

> **Router File:** This file directs [Agent] to the comprehensive documentation.

**Read this first:** `AGENT.md`

**Complete project context:** `PROJECT_CONTEXT.md`

---

## Why This File Exists

[Brief explanation of agent-specific convention]

**All instruction content is in:** `PROJECT_CONTEXT.md`

---

## Quick Context

- **Project:** [One-liner]
- **Current:** [Version]
- **Goal:** [Target]
- **Issue:** [Key problem]

**Check first:** `docs/plans/BACKLOG.md` for priorities

---

**Full instructions:** See `AGENT.md` in root directory.
```

---

## Adding New Agents

To support a new agent:

1. **Identify the file name** the agent looks for
2. **Create a router** following the pattern above
3. **Point to** `AGENT.md` → `PROJECT_CONTEXT.md`

Example: If an agent looks for `INSTRUCTIONS.md`:

```markdown
# Instructions

> **Router:** Read `AGENT.md` for complete context.

All project documentation is in `PROJECT_CONTEXT.md`.
```

---

## Content Strategy

### What Goes Where

**`PROJECT_CONTEXT.md` (Single Source):**
- Complete project structure
- All documentation references
- Data assets analysis
- Model architecture
- Workflows
- Key concepts
- Research foundations
- Agent guidelines
- Troubleshooting
- Quick reference

**Router Files:**
- "Why this file exists" explanation
- Pointer to `AGENT.md`
- Pointer to `PROJECT_CONTEXT.md`
- 5-bullet quick context
- One-line call-to-action

**Never:**
- Duplicate content in routers
- Agent-specific instructions in routers
- Technical details in routers

---

## Maintenance

### Updating Documentation

1. **Edit** `PROJECT_CONTEXT.md`
2. **Done.** All agents get the update.

### Adding New Sections

1. **Add to** `PROJECT_CONTEXT.md`
2. **Reference from** `AGENT.md` if needed
3. **No router changes** required

### Changing Project Info

1. **Update** `PROJECT_CONTEXT.md`
2. **Optional:** Update quick context in `AGENT.md`
3. **No router changes** required

---

## File Sizes

```
PROJECT_CONTEXT.md           430 lines (comprehensive)
AGENT.md                      30 lines (universal router)
.github/copilot-instructions.md  20 lines (VS Code router)
CLAUDE.md                     20 lines (Claude router)
.cursorrules                  15 lines (Cursor router)
-----------------------------------------------------------
Total content:               515 lines
Actual duplication:           ~100 lines (routers only)
Unique content:              ~430 lines (single source)
```

**Duplication ratio:** ~20% (routers) / ~80% (single source)

---

## Best Practices

### ✅ Do
- Keep routers minimal (<30 lines)
- Always point to `AGENT.md` first
- Use consistent language across routers
- Update only `PROJECT_CONTEXT.md` for content changes
- Test that all routers resolve correctly

### ❌ Don't
- Duplicate content in routers
- Add agent-specific instructions to routers
- Make routers longer than 1 page
- Forget to test router links
- Create router files without a purpose

---

## Migration Notes

If you have existing agent-specific documentation:

1. **Consolidate** all content into `PROJECT_CONTEXT.md`
2. **Create** router files for each agent
3. **Test** that each agent finds the right content
4. **Remove** old agent-specific files

---

## Future Considerations

### Potential Additions

- `.windsurfrules` for Windsurf IDE
- `CODEIUM.md` for Codeium
- `TABNINE.md` for Tabnine
- Any new agent convention

### Deprecation

If an agent adds native support for `AGENT.md`:
- Remove that agent's specific router
- Update this document

---

**Philosophy:** One source of truth, many paths to it.
