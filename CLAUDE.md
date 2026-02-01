# Project Development Framework

## Project Initialization Protocol (ALWAYS START HERE)

When beginning ANY new project, execute these steps in order:

### 1. Repository Setup (First Action)
```bash
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2. Create Core .gitignore (Before Any Code)
Research and create comprehensive .gitignore for the project's tech stack:
- Language-specific patterns (Python: __pycache__, .venv, .pyc; Node: node_modules, etc.)
- IDE files (.vscode/*, .idea/*, etc.)
- OS files (.DS_Store, Thumbs.db)
- Environment files (.env, .env.local, secrets.*)
- Build artifacts (dist/, build/, *.egg-info/)
- Claude CLI files (.claude/settings.local.json, CLAUDE.local.md)

### 3. Tech Stack Research (Before Architecture)
**CRITICAL**: Research current best practices for 2026 (update year as time progresses):
- Web search for "best [framework/language] 2026" and "[project type] tech stack 2026"
- Prioritize: performance, security, developer experience, community support
- Document findings in `.claude/knowledge-base/tech-stack-decisions.md`
- Check Stack Overflow, GitHub trends, and official documentation
- Select "best of breed" tools - avoid deprecated or unmaintained libraries

### 4. Read This Project's Context
**ALWAYS read these files before any work**:
- `.claude/knowledge-base/lessons-learned.md` - mistakes we've already fixed
- `.claude/state/current-state.md` - where we are now
- `.claude/knowledge-base/tech-stack-decisions.md` - technology choices and rationale

---

## Core Architecture: API-First Development

**MANDATORY PATTERN**: All functionality must be accessible via internal API before building UI.

### Why API-First?
- Tested at Netflix with proven success
- UI becomes thin client calling API endpoints
- Easier testing (test API independently)
- Future flexibility (swap UI frameworks, add mobile, etc.)
- Clear separation of concerns

### Implementation Structure
```
project/
├── core/           # Business logic (pure functions, no I/O)
├── api/            # API layer (exposes core logic)
├── cli/            # CLI interface (calls API)
├── ui/             # GUI interface (calls API)
└── tests/          # Comprehensive test suite
```

### Development Sequence
1. Design API contract first (OpenAPI/Swagger spec)
2. Implement core business logic in `core/`
3. Build API layer in `api/` wrapping core
4. Write comprehensive API tests
5. Build UI/CLI that consumes API
6. Never put business logic in UI/CLI layers

---

## Test-Driven Development (TDD) - NON-NEGOTIABLE

**RED RULE**: No implementation code until a failing test exists.

### TDD Workflow
1. Write test that describes desired behavior (it will fail - RED)
2. Write minimum code to make test pass (GREEN)
3. Refactor while keeping tests green (REFACTOR)
4. Commit only when all tests pass

### Test Coverage Requirements
- Unit tests: All core business logic functions
- Integration tests: All API endpoints
- Edge cases: Error handling, boundary conditions, race conditions
- Regression tests: For every bug fix

---

## Two-Phase Development Workflow

### Phase 1: Prompt Improvement (Planning)
Before implementing ANY feature:
1. Clarify objective, scope, constraints, acceptance criteria
2. Identify all affected code paths and files
3. Check for edge cases, race conditions, timing issues
4. Propose safest implementation approach
5. Get explicit approval before coding

### Phase 2: Implementation
1. **BEFORE coding**:
   - Read all affected files
   - Review business logic for edge cases
   - Check for breaking changes to existing features
   - Add feature flag for easy disable if needed

2. **DURING coding**:
   - Write test first (TDD)
   - Add defensive error handling
   - Add debug logging (removable via flag)
   - Keep changes minimal and localized
   - No unrelated refactoring or formatting

3. **AFTER coding**:
   - Run all tests (unit, integration, e2e)
   - Review for logic errors
   - Check affected user flows
   - Verify no regressions
   - Document known limitations

4. **DEPLOYMENT readiness**:
   - Implement graceful degradation
   - Add rollback plan
   - Update documentation

---

## Quality Gates (Must Pass Before Commit)

### Security Review (Stop-Ship Authority)
- No secrets in code (API keys, passwords, tokens)
- OWASP Top 10 vulnerabilities checked
- Dependency vulnerabilities scanned
- Input validation at all boundaries
- SQL injection, XSS, CSRF protections verified

### Code Quality
- All tests passing (unit + integration)
- No regressions in existing features
- Code comments/docstrings for complex logic
- No AI attribution in comments
- PEP-8 (Python) or language-specific style guide
- No unused functions or dead code

### Documentation
- README.md updated if user-facing changes
- API documentation updated (if API changed)
- Inline comments for non-obvious logic
- Lessons learned captured in `.claude/knowledge-base/`

---

## Persistent State Management

**CRITICAL**: This project uses `.claude/` directory for persistent memory across sessions.

### Auto-Loaded Files
Claude automatically reads on startup:
- This `CLAUDE.md` file
- All files in `.claude/rules/`
- All files in `.claude/knowledge-base/`
- `.claude/state/current-state.md`

### You MUST Update After Every Significant Change
- `.claude/state/current-state.md` - current sprint, blockers, next steps
- `.claude/knowledge-base/lessons-learned.md` - mistakes, solutions, patterns
- `.claude/knowledge-base/tech-stack-decisions.md` - technology choices

### Why This Matters
When conversations compress or you restart Claude, these files are our memory. Without updates, context is lost and we repeat mistakes.

---

## Context Window Management (2026 Best Practices)

### Monitor Context Usage
- Watch the token percentage in Claude Code's status bar
- **Exit at 75-80% utilization**, not 90-95%
- Quality degrades near limits: more bugs, inconsistent decisions, forgotten patterns
- Better: multiple fresh sessions than one exhausted session

### Use /clear Between Unrelated Tasks
**Problem**: "Kitchen sink sessions" fill context with irrelevant information
**Solution**: Run `/clear` when switching to unrelated topics
- Example: After debugging → before adding new feature → run /clear
- Keeps context focused on current task

### Leverage Subagents for Context Preservation
Use Task tool with subagents for:
- Research tasks (tech stack, best practices)
- Investigation (bug root cause, performance analysis)
- Security reviews
- Complex planning

**Why**: Each subagent gets its own context window, preventing main session bloat

### Extended Thinking for Complex Problems
Use thinking keywords when you need deeper analysis:
- `think` - Standard thinking budget
- `think hard` - Increased thinking budget
- `think harder` - More thorough analysis
- `ultrathink` - Maximum thinking budget

**When to use**: Architecture decisions, security reviews, complex algorithms

---

## UI/UX Standards (2026)

### Requirements
- Accessibility: WCAG 2.2 AA compliance minimum
- Performance: Core Web Vitals (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- Responsive: Mobile-first design
- Progressive enhancement
- Dark mode support
- Internationalization (i18n) ready

### Research Market Needs
Before building features:
1. Research competitor features (what's table stakes in 2026?)
2. Check Reddit, HackerNews, Product Hunt for user pain points
3. Identify gaps we can fill (competitive advantage)
4. Document in `.claude/knowledge-base/market-research.md`

---

## Red Flags & Safety Checks

### Before Implementing Any Feature, Ask:
1. **Race conditions**: Could this run before dependencies are ready?
2. **Breaking changes**: What existing features might this affect?
3. **Error handling**: What happens if this fails? Is there graceful degradation?
4. **Edge cases**: What if user does X while Y is happening?
5. **Worst case scenario**: What's the most destructive thing that could happen?
6. **Multiple code paths**: Did I update all places this logic is used?

---

## Git Workflow

### Commit Standards
- Descriptive messages (why, not what)
- Co-authored: `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`
- Small, atomic commits
- Never commit secrets, credentials, or large binaries

### Branch Strategy
- `main`: production-ready code
- `develop`: integration branch
- `feature/*`: new features
- `fix/*`: bug fixes

---

## Communication Style

### Code Comments
- Docstrings for all public functions
- Comments for complex logic only
- No AI attribution ("Generated by Claude")
- Assume reader is skilled developer

### User Communication
- No emojis unless requested
- Concise and technical
- Include file paths with line numbers: `src/core/auth.py:42`
- No time estimates ("this will take 5 minutes")
- No superlatives ("You're absolutely right!")

---

## Tool Usage Policy

### Prefer Specialized Tools
- Read files: Use Read tool, not `cat`
- Search code: Use Grep tool, not `grep` command
- Edit files: Use Edit tool, not `sed`
- Write files: Use Write tool, not `echo >` or heredoc

### When to Use Task Tool (Agents)
- Open-ended codebase exploration: Use Explore agent
- Complex planning: Use Plan agent
- Multi-step research: Use general-purpose agent
- **Context preservation**: Use subagents for research/investigation to keep main session focused

### Automation & Headless Mode (Optional)
For CI/CD or automated workflows:
- Use `-p "prompt text"` flag for headless mode
- Use `--output-format stream-json` for streaming JSON output
- Note: Headless mode doesn't persist between sessions

---

## Temperature Settings

**MANDATORY**: Use Temperature 0 for:
- All code generation
- Logic and algorithms
- Mathematics
- Security-sensitive operations

Use higher temperature only for:
- Creative writing (documentation)
- Brainstorming features

---

## Common Pitfalls to Avoid (2026 Research-Based)

### Context Management Pitfalls
1. **Kitchen Sink Sessions**: Jumping between unrelated tasks in one session
   - **Fix**: Use `/clear` between unrelated topics
2. **Running to 90-95% Context**: Pushing sessions until nearly full
   - **Fix**: Exit at 75-80% utilization for quality
3. **Not Using Subagents**: Loading all research into main session
   - **Fix**: Delegate research/investigation to subagents

### Planning Pitfalls
4. **Jumping to Code**: Implementing before understanding the problem
   - **Fix**: Always use two-phase workflow (plan → execute)
5. **Skipping Research**: Not looking up best practices before choosing approach
   - **Fix**: Use "think hard" keyword and research step

### Security Pitfalls
6. **Auto-Accepting All Changes**: Blindly accepting without review
   - **Fix**: Review each change, especially security-sensitive code
7. **Secrets in Plain Text**: API keys in README or config files
   - **Fix**: Always use environment variables, scan before commits

### Code Quality Pitfalls
8. **Missing "Why" Comments**: Code without context for future developers
   - **Fix**: Add comments explaining business logic and decisions
9. **Excessive Information**: Overloading prompts with unnecessary details
   - **Fix**: Be concise, let Claude ask for clarification

### Operational Pitfalls
10. **Not Updating .claude/**: Forgetting to update state and lessons
    - **Fix**: Update after every significant change

*See `.claude/knowledge-base/lessons-learned.md` for project-specific lessons.*

---

## Quick Reference

### Starting New Project
```bash
# 1. Init git and .gitignore
git init && touch .gitignore

# 2. Research tech stack
# (use web search for current best practices)

# 3. Create .claude/ structure
mkdir -p .claude/{skills,commands,rules,knowledge-base,state,templates,workflows}

# 4. Copy this template
cp /path/to/template/CLAUDE.md ./CLAUDE.md

# 5. Initialize state
echo "# Current State\n\nProject: [name]\nPhase: initialization\n" > .claude/state/current-state.md
```

### Before Each Session
1. Read `.claude/state/current-state.md`
2. Review recent `.claude/knowledge-base/lessons-learned.md`
3. Check `.claude/knowledge-base/tech-stack-decisions.md`

### After Each Session
1. Update `.claude/state/current-state.md` with progress
2. Add any new lessons to `.claude/knowledge-base/lessons-learned.md`
3. Document blockers or next steps

---

## Maintaining This CLAUDE.md File

### Keep It Concise (Context Window Optimization)
**Principle**: Quality over quantity. Claude's performance degrades as context fills.

**What to Keep in CLAUDE.md**:
- Core principles (API-first, TDD, security-first)
- Non-obvious project-specific rules
- Critical workflows (two-phase, quality gates)
- Persistent state management instructions

**What to Move Out**:
- Detailed step-by-step guides → Move to `.claude/workflows/`
- Long checklists → Move to `.claude/templates/`
- Architecture details → Let Claude discover from code/README
- Command lists → Claude can see them via `ls`, `make help`, etc.

**Goal**: Keep CLAUDE.md under 400 lines. Detailed protocols go in `.claude/` subdirectories.

**Research**: A 54% reduction in initial context = more room for actual work, faster responses, lower costs, without sacrificing capability. ([Source](https://gist.github.com/johnlindquist/849b813e76039a908d962b2f0923dc9a))

---

*This CLAUDE.md serves as the system prompt for all Claude Code sessions in this project. Keep it updated as requirements evolve.*
