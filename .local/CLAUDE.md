# Coding Contract

Ship correct, minimal changes with high confidence.
Michelin-star standard: not "does it work?" but "is it the best version of itself?"

---

## Session Start

Read in order:
1. `~/Dropbox/.nimbus-shared/docs/DESIGN_PRINCIPLES.md` — 20 principles (mandatory, every session)
2. `~/code/tools/nimbus/.local/BRANCHING.md` — machine roles: iMac=dev, MBP=test (mandatory)
3. `~/Dropbox/.nimbus-shared/prompts/code-review-systematic.md` — 8 quality dimensions (mandatory before any code)
4. `.local/claude/state/current-state.md` — where we are
5. `.local/claude/knowledge-base/lessons-learned.md` — mistakes to avoid
6. `PROJECT.md` — project context (if exists)

**Steps 1–3 are non-negotiable.** They govern every decision. No coding session starts without them.

---

## The Loop

Every task follows this pattern:

```
UNDERSTAND → PLAN → IMPLEMENT → VERIFY → REPORT
```

### 1. Understand
- Read relevant files before touching them
- If requirements are unclear: ask 2-3 targeted questions, then propose
- Never assume — state assumptions explicitly

### 2. Plan
- Break into smallest possible steps
- Identify risks before writing code
- For complex decisions, use structured reasoning:
  ```
  Options: A, B, C
  Tradeoffs: [brief for each]
  Recommendation: X because Y
  ```

### 3. Implement
- One step at a time
- Smallest viable diff — no drive-by refactors
- Run tests between steps
- If something breaks, stop and assess

### 4. Verify
- Run the actual tests (not "tests would pass")
- Show the output
- Verification is part of the task, not optional

### 5. Report
Every response ends with:
```
## Summary
- [what was done]

## Files Changed
- `path/file` — why

## Quality Check (8 Dimensions)
1. Code Quality    — [verdict]
2. Performance     — [verdict]
3. Security        — [verdict]
4. Test Coverage   — [verdict]
5. Documentation   — [verdict]
6. Architecture    — [verdict]
7. Maintainability — [verdict]
8. Scope/Footprint — ✅ Minimal | ⚠️ Justify | 🔴 Revert

## Audit Gates
$ audit-gates-check.sh → N/N passing

## Verified
$ [command run]
[output]

## Next
- [if more steps needed]
```

---

## Rules

**Code quality**
- Prefer explicit over clever
- Prefer composition over inheritance
- Prefer pure functions where practical
- No dead code, no commented-out code
- Tests when behavior changes

**Git**
- Atomic commits with descriptive messages
- Never commit secrets (use `.env.example`)
- Don't rewrite shared history

**Machine Role (BRANCHING.md)**
- iMac = Developer: write code, commit to `dev` or `feature/*` only
- MBP = Tester: validate and merge to `main` only — never the code author
- iMac must NEVER merge dev→main — that is MBP's job, always
- All changes flow: `feature/*` → `dev` (iMac) → MBP validates → PR → `main`

**Audit Gates (mandatory)**
- Every major design decision, architectural constraint, or "this must never happen" rule → add a gate to `.local/AUDIT-GATES.md` **in the same commit**
- Gate format: bash command that produces output only when the invariant is VIOLATED (zero output = pass)
- Use prefix `U-NNN` (e.g. U-011, U-012) — increment from highest existing gate
- Run gates before marking any task done: `bash ~/Dropbox/.nimbus-shared/scripts/audit-gates-check.sh ~/Code/tools/bash/BASH/upkeep`
- "This must always be true" in a doc = a gate. If you can't write a gate for it, the constraint will break silently.

**Safety**
- Ask before destructive operations (`rm`, migrations, mass changes)
- Prefer `trash` over `rm`
- Create safety snapshot before large refactors:
  ```bash
  git stash push -m "safety: before [operation]"
  ```

**Scope**
- Stay in lane — change only what's requested
- If you spot unrelated issues, note them for later
- If tempted to "clean up" nearby code, don't

---

## Self-Review Checklist

Before presenting code, verify:
- [ ] Solves the actual problem (not an adjacent one)
- [ ] No syntax errors
- [ ] No obvious logic errors
- [ ] No hardcoded values that should be config
- [ ] No secrets or sensitive data
- [ ] Imports are used
- [ ] Functions are called
- [ ] Error cases handled
- [ ] Tests pass
- [ ] Design decision committed? → Gate added to `.local/AUDIT-GATES.md` in this same commit
- [ ] All gates passing: `bash ~/Dropbox/.nimbus-shared/scripts/audit-gates-check.sh ~/Code/tools/bash/BASH/upkeep`

---

## Common Failure Modes (Guard Against)

| Failure | Prevention |
|---------|------------|
| Over-engineering | Ask: "Is this the simplest solution?" |
| Helpful rewrites | Touch only what's needed |
| Assuming it works | Run the tests, show output |
| Hallucinating APIs | Verify with docs or quick test |
| Scope creep | Finish current task first |
| Lost context | Re-read state file if uncertain |
| Forgetting to update state | Do it at session end, always |

---

## When Stuck

1. **State the problem clearly** — often this reveals the solution
2. **Check what was already tried** — `.local/claude/state/current-state.md`
3. **Reduce scope** — solve a smaller version first
4. **Ask** — a focused question beats thrashing

---

## Session End

Before stopping:
1. Update `.local/claude/state/current-state.md`:
   - What was completed
   - What's next
   - Any blockers or open questions
2. Commit if there's meaningful progress
3. Note any learnings for `.local/claude/knowledge-base/lessons-learned.md`

---

## Deep Dives

| Topic | File |
|-------|------|
| Detailed workflows | `.local/claude/workflows/` |
| Coding rules | `.local/claude/rules/` |
| Past learnings | `.local/claude/knowledge-base/` |
| Checklists | `.local/claude/templates/` |
| Best practices 2026 | `.local/claude/BEST_PRACTICES_2026.md` |
