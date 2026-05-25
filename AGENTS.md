# Superpowers — Integrated Skills for Antigravity

> **Source:** [obra/superpowers v5.0.7](https://github.com/obra/superpowers)
> **Installed:** Skills cloned to `.superpowers/` directory
> **Adapted for:** Antigravity agent (non-native plugin mode)

---

## Instruction Priority

1. **User's explicit instructions** — highest priority
2. **Superpowers skills below** — override default system behavior
3. **Default system prompt** — lowest priority

---

## Skills Reference

Full skill files are available in `.superpowers/skills/` for deep reference.
Below is an integrated summary of each skill's core principles.

---

## 🧠 Skill 1: Brainstorming

**When:** Before ANY creative work — creating features, building components, adding functionality, or modifying behavior.

**HARD GATE:** Do NOT write any code, scaffold any project, or take any implementation action until you have presented a design and the user has approved it.

**Process:**
1. Explore project context — check files, docs, recent commits
2. Ask clarifying questions — one at a time, prefer multiple choice
3. Propose 2-3 approaches — with trade-offs and your recommendation
4. Present design — in sections scaled to complexity, get user approval after each
5. Write design doc — save to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
6. Self-review spec — check for placeholders, contradictions, ambiguity, scope
7. User reviews written spec — wait for approval before proceeding
8. Transition to implementation — create implementation plan

**Key Principles:**
- One question at a time — don't overwhelm
- YAGNI ruthlessly — remove unnecessary features
- Explore alternatives — always propose 2-3 approaches
- Incremental validation — present design, get approval before moving on

---

## 📋 Skill 2: Writing Plans

**When:** You have a spec or requirements for a multi-step task, before touching code.

**Task Granularity:** Each step is one action (2-5 minutes):
- "Write the failing test" → step
- "Run it to make sure it fails" → step
- "Implement the minimal code" → step
- "Run tests, make sure they pass" → step
- "Commit" → step

**Requirements:**
- Exact file paths always
- Complete code in every step
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
- **No Placeholders** — never write "TBD", "TODO", "implement later", "add appropriate error handling"

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`

---

## 🧪 Skill 3: Test-Driven Development (TDD)

**When:** Implementing ANY feature or bugfix, before writing implementation code.

### The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. No exceptions.

### Red-Green-Refactor Cycle

1. **RED** — Write one minimal failing test showing what should happen
2. **Verify RED** — Run test, confirm it fails for the expected reason (not errors/typos)
3. **GREEN** — Write simplest code to make the test pass
4. **Verify GREEN** — Run test, confirm it passes and other tests still pass
5. **REFACTOR** — Clean up (remove duplication, improve names, extract helpers)
6. **Repeat** — Next failing test for next feature

**Good Tests:**
- One behavior per test
- Clear name describing behavior
- Real code (no mocks unless unavoidable)

**Common Rationalizations to REJECT:**

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "TDD will slow me down" | TDD is faster than debugging. |
| "Need to explore first" | Fine. Throw away exploration, start with TDD. |

---

## 🔍 Skill 4: Systematic Debugging

**When:** Encountering ANY bug, test failure, or unexpected behavior, BEFORE proposing fixes.

### The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

### The Four Phases

#### Phase 1: Root Cause Investigation
1. **Read error messages carefully** — don't skip past errors, read stack traces completely
2. **Reproduce consistently** — exact steps, every time
3. **Check recent changes** — git diff, recent commits, config changes
4. **Gather evidence** — add diagnostic logging at component boundaries
5. **Trace data flow** — where does the bad value originate? Keep tracing up.

#### Phase 2: Pattern Analysis
1. Find working examples in same codebase
2. Compare against references — read completely, don't skim
3. Identify every difference, however small
4. Understand dependencies and assumptions

#### Phase 3: Hypothesis and Testing
1. Form single hypothesis: "I think X because Y"
2. Test with SMALLEST possible change
3. One variable at a time
4. Didn't work? Form NEW hypothesis, don't add more fixes on top

#### Phase 4: Implementation
1. Create failing test case
2. Implement single fix — ONE change, no "while I'm here" improvements
3. Verify fix — test passes, no other tests broken
4. **If 3+ fixes failed:** STOP and question the architecture

**Red Flags — STOP and follow process:**
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "I don't fully understand but this might work"
- Proposing solutions before tracing data flow

---

## ✅ Skill 5: Verification Before Completion

**When:** About to claim work is complete, fixed, or passing.

### The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

### The Gate Function

```
BEFORE claiming any status:
1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
5. ONLY THEN: Make the claim
```

**Red Flags — STOP:**
- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Done!")
- Trusting partial verification
- ANY wording implying success without having run verification

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Linter passed" | Linter ≠ compiler |

---

## 📝 Skill 6: Executing Plans

**When:** You have a written implementation plan to execute.

**Process:**
1. **Load and Review Plan** — read critically, identify concerns
2. **Execute Tasks** — follow each step exactly, run verifications as specified
3. **Complete** — verify all tests pass, present options to user

**When to STOP:**
- Hit a blocker
- Plan has gaps preventing progress
- Don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

---

## 🔎 Skill 7: Code Review

**When:** After completing tasks, implementing major features, or before merging.

**Mandatory reviews:**
- After each task completion
- After completing a major feature
- Before merge to main

**Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if wrong (with reasoning)

---

## 🧭 Core Philosophy

| Principle | Description |
|-----------|-------------|
| **Test-Driven Development** | Write tests first, always |
| **Systematic over ad-hoc** | Process over guessing |
| **Complexity reduction** | Simplicity as primary goal |
| **Evidence over claims** | Verify before declaring success |
| **YAGNI** | You Aren't Gonna Need It — remove unnecessary features |
| **DRY** | Don't Repeat Yourself |

---

## Project-Specific Notes

- **Tech Stack:** PySide6, Python, SQLite
- **Application:** Pizzas Pastra — Point of Sale system
- **Design System:** Dark theme with warm accents
- **Testing Framework:** (configure as needed — e.g., pytest)

---

> For full skill definitions, see `.superpowers/skills/<skill-name>/SKILL.md`
