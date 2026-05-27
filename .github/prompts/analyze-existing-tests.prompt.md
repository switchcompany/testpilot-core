---
mode: agent
description: "Audit the current test suite: frameworks, structure, mocks, utilities, failures, baseline execution, and coverage gaps"
tools: ["bash", "glob", "grep", "view"]
---

# Analyze Existing Tests

Audit the existing backend tests before generating anything new.

## Step 1 — Locate all tests
Use stack conventions to find tests.

- Java/Kotlin: `src/test/**/*Test.*`, `src/test/**/*Spec.*`
- Python: `tests/test_*.py`, `tests/**/*_test.py`
- Node.js: `**/*.test.*`, `**/*.spec.*`, `__tests__/`
- Go: `**/*_test.go`
- Rust: `#[cfg(test)]` modules, `tests/`
- C#: `*Tests.cs`, `*.UnitTests.cs`
- Ruby: `spec/**/*_spec.rb`, `test/**/*_test.rb`
- PHP: `tests/**/*Test.php`

## Step 2 — Learn suite conventions
Read representative tests and identify:
- framework and runner,
- assertion style,
- mocking style,
- fixture/factory pattern,
- teardown/reset pattern,
- shared utilities,
- golden file/snapshot usage,
- common naming conventions,
- test resources and data builders.

## Step 3 — Compile and run the current suite
Prefer the project’s existing test commands.

Collect:
- total tests,
- passed,
- failed,
- errored,
- skipped,
- compile failures,
- runtime failures,
- timeouts,
- coverage generation success/failure.

If failures exist, categorize them before touching code.

## Step 4 — Baseline coverage
Generate baseline coverage using the project’s configured tool first.
If it fails, note the failure and the likely fallback path.

Record:
- overall line coverage,
- branch coverage if available,
- per-module/per-package coverage,
- per-class coverage for requested targets.

## Step 5 — Gap analysis
Create a prioritized gap table.

### Full project mode
Include all relevant backend source files.

### Targeted mode
Include only:
- the requested files/classes,
- direct dependencies if needed for explaining mock seams.

Use this format:

| Source File | Has Tests? | Test Count | Coverage % | Priority | Missing Scenarios |
|---|---|---:|---:|---|---|

Priority should be based on:
- uncovered testable lines,
- business criticality,
- ease of isolation,
- likelihood of stable unit tests.

## Step 6 — Quality audit
For each representative test file, check:
- strong vs weak assertions,
- over-mocking,
- hidden shared state,
- time/env/network dependence,
- brittleness,
- duplication,
- unreadable fixtures,
- framework misuse.

## Step 7 — Failure classification
Group current failures into categories such as:
- DTO/model drift,
- signature drift,
- missing mock/stub,
- wrong async harness,
- singleton/global state,
- import-time side effects,
- DB state leakage,
- DI container leakage,
- wrong patch location,
- coverage tooling/config failures.

## Step 8 — Output format
Produce:

```markdown
## Existing Test Audit

### Suite Summary
- Test files:
- Test methods/cases:
- Passing:
- Failing:
- Skipped:
- Baseline line coverage:

### Conventions
- Framework:
- Assertion style:
- Mock style:
- Fixtures/utilities:

### Failures
| Category | Count | Example | Likely Fix |
|---|---:|---|---|

### Coverage Gaps
| Source File | Coverage | Priority | Why it matters |
|---|---:|---|---|

### Recommendations
1. ...
2. ...
```

This audit becomes the plan for fixing and generating tests.
