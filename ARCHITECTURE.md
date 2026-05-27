# TestPilot Core — Architecture

## System Overview

TestPilot Core operates as a **3-layer architecture**: a central knowledge hub, per-project agent copies, and the Copilot runtime.

```
┌────────────────────────────────────────────────────────────────────────┐
│                         LAYER 1: Central Hub                          │
│                    (testpilot-core repository)                        │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐   │
│  │   Prompts    │  │  Knowledge   │  │     LEARNINGS.md          │   │
│  │  (workflow)  │  │   Packs      │  │  (cross-project memory)   │   │
│  └──────────────┘  └──────────────┘  └───────────────────────────┘   │
│                                                                       │
│  setup.sh distributes to projects ──────────────────────┐            │
└────────────────────────────────────────────────────────────┼───────────┘
                                                            │
┌──────────────────────────────────────────────────────────┐│
│              LAYER 2: Per-Project Copy                   ││
│          (your-project/.github/)                         ◀┘
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  copilot-    │  │   prompts/   │  │ agent-config  │  │
│  │ instructions │  │  (workflow)  │  │   .yml        │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              LAYER 3: Copilot Runtime                    │
│                                                          │
│  Copilot reads .github/copilot-instructions.md           │
│  and executes prompts using available tools:             │
│  bash, glob, grep, view, edit, create                    │
│                                                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────────┐  │
│  │Analyze │▶│Generate│▶│  Run   │▶│ Report + Learn  │  │
│  │ Code   │ │ Tests  │ │ Tests  │ │                 │  │
│  └────────┘ └────────┘ └────────┘ └─────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Knowledge Flow

```
                    ┌─────────────┐
                    │ Central Hub │
                    │ LEARNINGS   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │Project A │ │Project B │ │Project C │
        │(Python)  │ │(Kotlin)  │ │(Go)      │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    ┌─────────────┐
                    │ Central Hub │
                    │ LEARNINGS   │
                    │ (enriched)  │
                    └─────────────┘

Bidirectional sync: Read at start, Write at end
```

## Phase Pipeline Detail

### Detection → Analysis → Generation → Learning

```
Phase -1: Load LEARNINGS.md from central hub + local project
     │
Phase 0: User selects mode (Full / Targeted / Analyze Only)
     │
Phase 1: DETECT STACK
     │  Read build files (pom.xml, build.gradle, package.json, go.mod, etc.)
     │  Determine: language, framework, test runner, mock library, coverage tool
     │  Detect monorepo structure if applicable
     │
Phase 2: ANALYZE PROJECT
     │  HLD: system purpose, module map, integrations, communication patterns
     │  LLD: per-module classes, public APIs, data models, DI setup
     │  Flows: request lifecycle, business logic, error handling
     │
Phase 3: AUDIT EXISTING TESTS
     │  Scan test directories
     │  Compile and run existing tests
     │  Generate baseline coverage report
     │  Produce gap analysis table
     │
Phase 3.5: FIX BROKEN TESTS
     │  Apply 10+ battle-tested fix patterns
     │  Re-run coverage, update baseline
     │
Phase 4: ITERATIVE TEST GENERATION (up to 5 rounds)
     │  ┌─ 4.1: Identify coverage gaps
     │  │  4.2: Generate tests (prioritized by impact)
     │  │  4.3: Compile, run, measure coverage
     │  │  4.4: Rollback protection (revert if coverage drops)
     │  │  4.5: Check exit conditions (target reached / max iterations / stall)
     │  └─ Loop back to 4.1 if not done
     │
Phase 5: GENERATE FINAL REPORT
     │  Before/after coverage, files created/modified, remaining gaps
     │
Phase 6: SELF-LEARN
        Capture new patterns → LEARNINGS.md → sync to central hub
```

## Coverage Rollback Algorithm

```
BEST_COVERAGE = baseline
STALL_COUNT = 0

for iteration in 1..MAX_ITERATIONS:
    generate_tests()
    NEW_COVERAGE = measure_coverage()

    if NEW_COVERAGE < BEST_COVERAGE:
        # Coverage dropped — try to fix
        fix_failing_tests()
        NEW_COVERAGE = measure_coverage()

        if NEW_COVERAGE < BEST_COVERAGE:
            # Still dropping — rollback
            delete_new_test_files()
            log("Iteration {N} rolled back")
            STALL_COUNT += 1
    else:
        delta = NEW_COVERAGE - BEST_COVERAGE
        BEST_COVERAGE = NEW_COVERAGE

        if delta < 2.0:
            STALL_COUNT += 1
        else:
            STALL_COUNT = 0

    # Exit conditions
    if BEST_COVERAGE >= TARGET: break    # Target reached
    if STALL_COUNT >= 2: break           # Diminishing returns
```

## Security Model

- Agent runs entirely within Copilot's sandbox
- No external API calls (beyond project's own build tools)
- No credentials stored or transmitted
- LEARNINGS.md contains only patterns, never source code
- All operations are local to the developer's environment
