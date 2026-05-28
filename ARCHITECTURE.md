# Forge Core — Architecture

## System Overview

Forge Core operates as a **3-layer architecture**: a central knowledge hub, per-project agent copies, and the Copilot runtime.

```
┌────────────────────────────────────────────────────────────────────────┐
│                         LAYER 1: Central Hub                          │
│                      (forge-core repository)                          │
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
Phase 1.5: COVERAGE EXCLUSION SCAN
     │  Read build/coverage config for exclusion patterns
     │  Classify excluded vs included packages
     │  Adjust target list to avoid wasted effort
     │
Phase 2: ANALYZE PROJECT
     │  HLD: system purpose, module map, integrations, communication patterns
     │  LLD: per-module classes, public APIs, data models, DI setup
     │  Flows: request lifecycle, business logic, error handling
     │
Phase 2.5: DEPENDENCY GRAPH & CASCADE COVERAGE
     │  Map function-to-function call relationships
     │  Calculate cascade depth scores per entry point
     │  Identify Tier 1/2/3 test targets
     │  Feed cascade map into Phase 4 prioritization
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
Phase 4: ITERATIVE TEST GENERATION + AUTO COMPILE-FIX LOOP (up to 10 rounds)
     │  ┌─ 4.1: Identify coverage gaps
     │  │  4.2: Generate tests (prioritized by impact)
     │  │  4.3: Compile, auto-fix, run, measure coverage
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

## Cascade Coverage Architecture

```
                    ┌─────────────┐
                    │ Entry Point │
                    │  (Route)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Service   │ ◀── Tier 1 target (cascade depth 5+)
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Adapter  │ │  Client  │ │  Mapper  │ ◀── Tier 2 (depth 3-4)
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │             │
             ▼             ▼             ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Helpers  │ │   DTOs   │ │  Utils   │ ◀── Tier 3 (depth 1-2)
        └──────────┘ └──────────┘ └──────────┘

One Tier 1 test cascades through all layers = maximum coverage per test
```

## Auto Compile-Fix Loop

```
Generate Test Batch
        │
        ▼
    Compile ──── Pass ──── Run Tests ──── Coverage
        │
      Fail
        │
        ▼
  Classify Error ──┬── DTO drift → fix constructors
                   ├── Missing import → add import
                   ├── Wrong mock type → fix every/coEvery
                   ├── Type mismatch → align types
                   └── DI setup → add Koin/Spring config
        │
        ▼
   Recompile (up to 3 retries)
        │
      Still failing?
        │
        ▼
   Isolate broken test → continue with working tests
```

## Speed & Parallel Execution Architecture

```
┌─────────────────────────────────────────────────────────┐
│               ORCHESTRATOR (full-workflow)               │
│                                                         │
│  Phase 1-2.5 ─── Sequential (architecture analysis)    │
│       │                                                 │
│       ▼                                                 │
│  ┌─────────────────────────────────────────┐            │
│  │        PARALLEL GENERATION ENGINE        │            │
│  │                                         │            │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │            │
│  │  │ Scope A │ │ Scope B │ │ Scope C │  │  Parallel  │
│  │  │ Agent   │ │ Agent   │ │ Agent   │  │  agents    │
│  │  │ (pkg.a) │ │ (pkg.b) │ │ (pkg.c) │  │  per scope │
│  │  └────┬────┘ └────┬────┘ └────┬────┘  │            │
│  │       │           │           │        │            │
│  │       ▼           ▼           ▼        │            │
│  │  ┌──────────────────────────────────┐  │            │
│  │  │          MERGE & VALIDATE        │  │            │
│  │  │    Full suite → Coverage report  │  │            │
│  │  └──────────────────────────────────┘  │            │
│  └─────────────────────────────────────────┘            │
│       │                                                 │
│       ▼                                                 │
│  .forge-cache/ ── Architecture + dependency graph       │
│       │            (cached for repeat runs)             │
│       ▼                                                 │
│  Target reached? ── YES → Early exit                    │
│                     NO  → Next iteration                │
└─────────────────────────────────────────────────────────┘
```

### Performance Optimization Layers

| Layer | Optimization | Impact |
|-------|-------------|--------|
| **Analysis** | Architecture caching in `.forge-cache/` | 60-70% faster on repeat runs |
| **Planning** | Lazy phase execution (skip unnecessary phases) | 2-5 min saved per run |
| **Generation** | Parallel agents per package scope | 4-6x throughput on large projects |
| **Compilation** | Smart batching (3-5 files, compile once) | ~3x fewer compile cycles |
| **Coverage** | Incremental (new tests only, full at boundaries) | ~50% faster iterations |
| **Scaffolding** | Pre-computed templates from knowledge packs | 30-40% faster per file |
| **Termination** | Early exit when target reached | No wasted generation |

## Security Model

- Agent runs entirely within Copilot's sandbox
- No external API calls (beyond project's own build tools)
- No credentials stored or transmitted
- LEARNINGS.md contains only patterns, never source code
- All operations are local to the developer's environment
