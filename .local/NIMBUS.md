# Upkeep — Project Guidance for Nimbus

Actions over advice. Read files, make minimal diffs, verify, report.

---

## Session Start (mandatory, in order)

```
1. Read ~/Dropbox/.nimbus-shared/docs/DESIGN_PRINCIPLES.md    ← 20 principles, always
2. Read ~/code/tools/nimbus/.local/BRANCHING.md               ← machine roles, always
3. Read ~/Dropbox/.nimbus-shared/prompts/code-review-systematic.md  ← 8 quality dimensions
4. Read .local/CLAUDE.md                                       ← Upkeep coding contract
5. Read .local/claude/state/current-state.md                  ← current focus
6. Read .local/claude/knowledge-base/lessons-learned.md       ← avoid repeating mistakes
```

Do not start work until steps 1–3 are loaded. They govern every decision made below.

---

## Machine Roles — Non-Negotiable

| Machine | Role | What it does |
|---------|------|-------------|
| **iMac** | 🔨 Developer | Writes all code. Commits to `dev` or `feature/*` only. |
| **MBP** | 🧪 Tester | Validates before merge to `main`. Never the code author. |
| **`main`** | 🏭 Stable | Always deployable. Merge only after MBP confirms. |

**iMac must not merge dev→main.** That is MBP's role, always.

---

## Quality Standard

Every Upkeep change is evaluated on 8 dimensions (from `code-review-systematic.md`):

1. **Code Quality & Best Practices** — naming, readability, DRY, language idioms
2. **Performance** — complexity, resource usage, optimization opportunities
3. **Security** — input validation, path traversal, injection risks, log privacy
4. **Test Coverage** — what exists vs. what's needed, edge cases, testability
5. **Documentation** — inline comments, README currency, operation guidance
6. **Architecture** — separation of concerns, coupling, DESIGN_PRINCIPLES alignment
7. **Maintainability** — complexity, future modification cost, technical debt
8. **Scope & Footprint (P20)** — changed only what this task required; unrelated issues filed as tasks

Michelin-star standard: not "does it work?" but "is it the best version of itself?"

---

## Audit Gates

**Location:** `.local/AUDIT-GATES.md`
**Runner:** `bash ~/Dropbox/.nimbus-shared/scripts/audit-gates-check.sh ~/Code/tools/bash/BASH/upkeep`

Rule: add a gate in the **same commit** as any design decision or architectural constraint.
Gate prefix: `U-NNN` (increment from highest existing gate).
All gates must pass before marking any task done.

---

## The Loop

```
LOAD CONTEXT → UNDERSTAND → PLAN → IMPLEMENT → VERIFY → REPORT
```

### Load Context
- Steps 1–6 above, every session, no exceptions

### Understand
- Read before changing
- If unclear, ask targeted questions
- State assumptions explicitly

### Plan
- Break into small steps
- One task at a time
- Identify risks upfront
- For non-trivial decisions: document Options → Tradeoffs → Recommendation

### Implement
- Smallest viable diff — no drive-by refactors
- Run tests between steps
- Stop if something breaks

### Verify
- Run actual commands, show actual output
- Never say "this should work"
- Run audit gates: `audit-gates-check.sh`

### Report
```
## Summary
- [what was done]

## Files Changed
- `path/file` — why

## Quality Check (8 dimensions)
- [brief verdict on each]

## Gates
$ audit-gates-check.sh output

## Verified
$ command
output
```

---

## Rules

**Ask first:**
- `rm` anything (use `trash`)
- Anything irreversible or large-scope

**Stay in scope (P20):**
- Change only what the task requires
- No drive-by refactors
- Unrelated issues → note them in a task, don't fix inline

**Verify everything:**
- Run the test, show the output
- Check error cases

**Design decisions:**
- Add U-NNN gate to `.local/AUDIT-GATES.md` in the same commit
- Document WHY in the commit message, not just WHAT

---

## When Stuck

1. State the problem clearly
2. Check what was tried: `.local/claude/state/current-state.md`
3. Reduce scope — solve a smaller version first
4. Ask a focused question

---

## Session End

1. Update `.local/claude/state/current-state.md` (completed / next / blockers)
2. Run audit gates — confirm all pass
3. Commit meaningful progress with semantic message
4. Add learnings to `.local/claude/knowledge-base/lessons-learned.md` if applicable

---

## Reference

| Need | Location |
|------|----------|
| 20 design principles | `~/Dropbox/.nimbus-shared/docs/DESIGN_PRINCIPLES.md` |
| Machine roles & branching | `~/code/tools/nimbus/.local/BRANCHING.md` |
| 8-dimension code review | `~/Dropbox/.nimbus-shared/prompts/code-review-systematic.md` |
| Upkeep coding contract | `.local/CLAUDE.md` |
| Audit gates | `.local/AUDIT-GATES.md` |
| Workflows | `.local/claude/workflows/` |
| Past learnings | `.local/claude/knowledge-base/` |
| Current state | `.local/claude/state/current-state.md` |
