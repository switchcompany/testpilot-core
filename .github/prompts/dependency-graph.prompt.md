---
mode: agent
description: "Build a static project dependency graph to identify cascade coverage opportunities and prioritize tests with the highest coverage return"
tools: ["bash", "glob", "grep", "view"]
---

# Dependency Graph & Cascade Coverage Analysis

Purpose: Map function-to-function and layer-to-layer call relationships to find high-cascade test targets that unlock the most coverage from the fewest tests.

This is a **static analysis** phase. Do not execute application code. Infer relationships by reading source files, imports, declarations, handlers, service wiring, and call sites.

## Step 1 — Identify all source files in scope
Build the analysis scope from project source files while respecting earlier coverage filtering.

Rules:
- include only source files relevant to the requested backend scope,
- respect coverage exclusions identified in **Phase 1.5 — Coverage Exclusion Scan**,
- deprioritize generated files, pure constants, trivial DTO-only files, and framework boilerplate,
- preserve module/package boundaries for later reporting.

Output a scoped inventory of files/modules that are both:
1. test-relevant, and
2. coverage-measurable.

---

## Step 2 — Catalog callable structure per class/module
For each significant class, module, file, or package, catalog:
- public methods/functions,
- internal/private/helper methods called by public methods,
- constructor-injected or imported collaborators,
- outbound cross-class or cross-module calls,
- adapters/clients/repositories invoked downstream,
- mapping, transformation, validation, and utility hops.

Capture relationships like:
- **Route/Controller → Service**
- **Service → Adapter**
- **Adapter → Client**
- **Client → Mapper**
- **Mapper → Helper/Util**
- **Service → Validator → Policy → Mapper**

Prefer semantic call relationships over raw file adjacency.

---

## Step 3 — Build call chains from entry points
Trace call chains from meaningful entry points through downstream layers.

Typical entry points include:
- HTTP routes,
- controllers,
- handlers,
- service methods called directly by handlers,
- use-case classes,
- worker/job processors,
- message consumers,
- CLI commands.

For each entry point, trace the main downstream path through layers such as:
- routes/controllers,
- services/use cases,
- adapters,
- repositories/clients,
- mappers/transformers,
- validators/policies,
- utils/helpers.

Where exact resolution is ambiguous, make a reasoned static inference and mark confidence.

---

## Step 4 — Calculate cascade depth
For each entry point or high-level callable, calculate a practical **cascade depth** score.

Cascade depth should reflect how much downstream behavior a single test is likely to exercise, including:
- number of directly called collaborators,
- number of downstream functions/helpers reached,
- number of architectural layers traversed,
- whether the call chain fans out into multiple mappings/validators/helpers,
- whether the path reaches behavior-rich modules rather than trivial pass-through code.

Use a pragmatic heuristic, not a mathematically perfect graph algorithm.

Suggested scoring inputs:
- **Depth**: how many layers deep the chain goes,
- **Breadth**: how many downstream calls the entry point fans into,
- **Density**: whether downstream nodes contain real business logic,
- **Coverage eligibility**: whether those nodes are included in measured coverage.

---

## Step 5 — Identify cascade coverage opportunities
Highlight targets where one well-designed test can cover many downstream lines.

Treat these as high-value opportunities:
- entry points with **cascade depth > 3**,
- service methods that trigger adapters, clients, mappers, and helpers,
- orchestrator methods with multiple business-rule branches,
- transformation-heavy flows where one public method reaches many private helpers.

Example framing:
- testing `CartService.getCart()` may cascade through **Adapter → Client → Mapper → 12 helpers** and cover hundreds of lines from one test.

Also identify anti-patterns:
- low-level helpers with little fan-out that are poor first targets,
- targets in excluded packages that would not improve reported coverage,
- entry points whose downstream calls are mostly mocked away by necessity.

---

## Step 6 — Produce the cascade coverage strategy
Turn the graph into a phased testing strategy.

### Tier 1 — High-cascade integration-style unit tests
Prioritize high-level service/use-case methods that exercise many layers with controlled mocks only at external I/O seams.

Best candidates usually:
- traverse multiple layers,
- hit business logic plus mappers/helpers,
- produce broad measurable coverage,
- avoid full framework boot cost.

### Tier 2 — Mid-cascade tests
Target adapters, mappers, validators, or orchestrators that still exercise several internal helpers or transformations.

### Tier 3 — Targeted gap-fill tests
After high-ROI paths are covered, add focused tests for isolated logic that remains uncovered.

The strategy must explicitly prefer **coverage ROI** over brute-force one-test-per-helper behavior.

---

## Step 7 — Output the cascade coverage map
Produce a report that feels like a software architecture analysis artifact, not a generic test list.

### Cascade Coverage Map
| Entry Point | Cascade Depth | Estimated Lines Covered | Dependencies Exercised | Priority |
|---|---:|---:|---|---|

Priority guidance:
- **P1** — high cascade, high confidence, coverage-measurable, business-critical
- **P2** — meaningful cascade but smaller surface or more mocking required
- **P3** — isolated or lower-yield targets for later cleanup

---

## Coverage Impact Predictor
Estimate which tests are likely to deliver the best coverage return on effort.

For each recommended target, predict:
- likely downstream files/packages exercised,
- approximate line-coverage gain potential,
- whether the test is broad-ROI or narrow-gap,
- whether the path is stable enough for deterministic testing,
- whether exclusions or heavy mocks reduce the actual payoff.

Required predictor output:

| Candidate Test Target | Expected Cascade | Estimated Coverage ROI | Main Dependencies | Constraints |
|---|---|---|---|---|

Use plain-language ROI labels such as:
- **Very High**
- **High**
- **Medium**
- **Low**

---

## Required final output
```markdown
## Dependency Graph & Cascade Coverage Report
- Scope analyzed:
- Coverage exclusions respected:
- Static-analysis confidence:

### Key Call Chains
1. Entry point → ...
2. Entry point → ...

### Cascade Coverage Map
| Entry Point | Cascade Depth | Estimated Lines Covered | Dependencies Exercised | Priority |
|---|---:|---:|---|---|

### Coverage Impact Predictor
| Candidate Test Target | Expected Cascade | Estimated Coverage ROI | Main Dependencies | Constraints |
|---|---|---|---|---|

### Recommended Test Strategy
- Tier 1:
- Tier 2:
- Tier 3:
```

This phase is the missing architectural layer between raw coverage data and actual test generation. Use it to direct Forge Core toward the tests that unlock the largest measurable coverage gains first.
