---
mode: agent
description: "Forge Core orchestrator for analysis, audit, repair, iterative unit-test generation, rollback protection, and self-learning"
tools: ["bash", "glob", "grep", "view", "edit", "create"]
---

# Full Workflow — Forge Core

Use this prompt as the **main orchestrator** for backend test generation across any supported language.

## Core Mission
- Work only in **test files, test fixtures, test resources, and test-only configuration**.
- Never modify production/source code.
- Improve coverage safely toward the requested target.
- Preserve or improve suite stability.

---

## Phase -1 — Load Past Learnings
1. Read `.github/agent-config.yml`.
2. If `central_agent_path` exists, load:
   - `{central_agent_path}/LEARNINGS.md`
   - relevant files in `{central_agent_path}/knowledge-packs/`
3. Read local `LEARNINGS.md` if present.
4. Carry those learnings into all later phases.

---

## Phase 0 — User Gate
Ask the user which mode to run:
1. **Full project run**
2. **Specific classes/files only**
3. **Analyze only**
4. **Analyze + Review existing tests**

### Mode rules
- **Full project:** full backend scope.
- **Specific classes/files:** test only requested files; mock dependencies.
- **Analyze only:** stop after architecture and testability analysis.
- **Analyze + Review:** stop after architecture + test audit + baseline coverage.

Record:
- requested targets,
- requested coverage target (default 90),
- max iterations (default 10).

---

## Phase 1 — Detect Tech Stack
Run `detect-tech-stack.prompt.md`.

Required outputs:
- language/framework/build tool,
- module layout,
- source/test roots,
- existing test and coverage commands,
- monorepo boundaries,
- likely backend-only modules.

---

## Phase 1.5 — Coverage Exclusion Scan
Run `coverage-exclusion-scan.prompt.md`.

Collect:
- excluded packages/paths per coverage tool,
- exclusion sources (build files, config files),
- packages with testable logic hidden behind exclusions,
- adjusted target list removing excluded packages.

Feed the exclusion map into all later phases.

---

## Phase 2 — Analyze Project
Run `analyze-project.prompt.md`.

Collect:
- HLD,
- LLD,
- request/data/event flows,
- security model,
- dependency seams,
- testability map.

---

## Phase 2.5 — Dependency Graph & Cascade Coverage
Run `dependency-graph.prompt.md`.

Collect:
- call chain map (entry points → downstream functions),
- cascade depth scores per entry point,
- coverage impact predictions,
- tiered target list (Tier 1/2/3).

Feed the cascade map into Phase 5 prioritization.

---

## Phase 3 — Analyze Existing Tests
Run `analyze-existing-tests.prompt.md`.

Collect:
- test framework and style,
- shared fixtures/utilities,
- current failures,
- baseline pass/fail counts,
- baseline coverage,
- prioritized gap list.

If the mode is **Analyze only**, stop after Phase 2 and report.
If the mode is **Analyze + Review existing tests**, stop after Phase 3 and report.

---

## Phase 4 — Fix Broken Tests
Run `fix-broken-tests.prompt.md` before writing new tests.

Goals:
- restore broken tests where reasonable,
- preserve existing passing behavior,
- improve the quality of baseline coverage data,
- avoid carrying unstable state into the generation loop.

After fixes, rerun coverage and record:
- `BASELINE_COVERAGE`
- `POST_FIX_COVERAGE`
- `BEST_COVERAGE = max(BASELINE_COVERAGE, POST_FIX_COVERAGE)`

---

## Phase 6 — Iterative Test Generation Loop
Run `write-unit-tests.prompt.md` in batches.

### Speed rules
- **Parallel scopes**: Split targets into independent scopes and generate tests simultaneously when runtime supports parallel agents.
- **Smart batching**: Group 3-5 related test files per batch. Compile once per batch.
- **Incremental coverage**: After baseline, run only new tests for fast feedback. Full suite at iteration boundaries.
- **Early exit**: Stop immediately when target coverage is reached — don't finish remaining planned batches.

### Required control variables
```text
TARGET_COVERAGE = user value or 90
MAX_ITERATIONS = user value or 10
ITERATION = 1
STALL_COUNT = 0
STALL_THRESHOLD = 2.0
BEST_COVERAGE = post-fix coverage
PREVIOUS_COVERAGE = post-fix coverage
BEST_STATE = current accepted test state
ROLLBACKS = 0
```

### Iteration flow
1. Read the latest coverage report.
2. Identify the top **feasible** uncovered files/classes.
3. Prioritize:
   - services,
   - adapters/handlers/routes,
   - utils,
   - mappers,
   - other testable logic.
   If a cascade map is available from Phase 2.5, use cascade-aware prioritization (Tier 1 → Tier 2 → standard → Tier 3 gap-fill).
4. Generate a focused batch of tests.
5. Compile and run the relevant suite.
6. Regenerate coverage.
7. Compare `NEW_COVERAGE` to `BEST_COVERAGE` and `PREVIOUS_COVERAGE`.

### Coverage tracking
Maintain an iteration table:

| Iteration | Files Touched | Coverage Before | Coverage After | Delta | Accepted? | Notes |
|---|---|---:|---:|---:|---|---|

### Rollback protection algorithm
```text
if NEW_COVERAGE < BEST_COVERAGE:
    diagnose the cause
    try one repair pass
    rerun tests and coverage
    if still lower:
        revert only tests added/changed in this iteration
        restore BEST_STATE
        confirm coverage restored
        ROLLBACKS += 1
        mark iteration as rolled back
        STALL_COUNT += 1
else:
    accept iteration
    if NEW_COVERAGE > BEST_COVERAGE:
        BEST_COVERAGE = NEW_COVERAGE
        BEST_STATE = accepted current state
    if (NEW_COVERAGE - PREVIOUS_COVERAGE) < STALL_THRESHOLD:
        STALL_COUNT += 1
    else:
        STALL_COUNT = 0
    PREVIOUS_COVERAGE = NEW_COVERAGE
```

### Exit conditions
Stop when any one is true:
1. `BEST_COVERAGE >= TARGET_COVERAGE`
2. `ITERATION >= MAX_ITERATIONS`
3. `STALL_COUNT >= 2`
4. remaining uncovered code is clearly infra-bound or coverage-excluded

### Rollback notes
A rollback must include:
- failing files,
- reason coverage dropped,
- what was attempted,
- confirmation that the repo ended in `BEST_STATE`.

### Auto compile-fix loop
After generating a batch:
1. Compile immediately.
2. If compilation fails, classify errors and apply fix patterns from Phase 4 (fix-broken-tests).
3. Retry up to 3 times per batch.
4. If still failing, isolate the broken test file and proceed with working tests.
5. Never leave the suite in a broken state.

### DTO constructor pre-validation
Before generating tests that reference DTOs:
1. Read the current DTO/data class constructor.
2. Verify required params, types, and defaults.
3. Use exact signatures in test data.

---

## Phase 7 — Final Report
Produce:
- mode,
- targets (if any),
- stack summary,
- starting coverage,
- final accepted coverage,
- iteration history,
- rollback count,
- files created,
- files updated,
- tests fixed,
- remaining gaps and why,
- explicit statement: **production code modified: none**.

---

## Phase 8 — Self-Learning
Run `self-learn.prompt.md`.

Capture:
- new failure patterns,
- stack-specific test tactics,
- coverage tool workarounds,
- dead ends worth avoiding next time,
- new knowledge-pack-worthy content.

---

## Error Recovery Rules
If any phase fails:
1. read the full error message,
2. use stack-appropriate fallback commands/tools,
3. prefer fixing deterministic and reproducible issues,
4. skip only clearly infra-dependent or brittle targets,
5. never let final coverage end lower than the best observed value,
6. never solve test failures by changing production code.

---

## Success Criteria
A run is complete only when:
- the requested mode is fully executed,
- all accepted test changes compile and run,
- coverage is measured and reported,
- rollback protection has been honored,
- production code remains untouched,
- self-learning is updated if new patterns were discovered.

---

## Speed Optimization Rules
Apply these at every phase to minimize total run time:

1. **Merge Phase 1 + 1.5** into a single scan pass when possible.
2. **Skip Phase 4** (Fix Broken Tests) if baseline passes 100%.
3. **Skip Phase 2.5** (Dependency Graph) in targeted mode for ≤ 3 files.
4. **Generate tests in parallel** — split project into independent package scopes, assign each to a parallel agent with pre-loaded context.
5. **Batch 3-5 test files per iteration** — compile once per batch, not per file.
6. **Use incremental coverage** during iteration — full suite only at iteration boundaries.
7. **Exit immediately** when target coverage is reached mid-batch.
8. **Cache architecture analysis** — on repeat runs, check `.forge-cache/` and skip Phases 1-2.5 if recent.
9. **Pre-compute test scaffolds** from knowledge packs before writing test methods.
10. **Never re-analyze already-covered code** — focus only on gaps.
