---
mode: agent
description: "Scan coverage tooling exclusions before test generation so excluded packages do not consume effort without moving reported coverage"
tools: ["bash", "glob", "grep", "view"]
---

# Coverage Exclusion Scan

Purpose: Detect coverage tool exclusions **before** test generation so Forge Core does not waste effort on code that cannot improve reported coverage.

## Step 1 — Detect the active coverage tool
Identify the project’s effective coverage stack before scanning exclusions.

Check in this order:
1. existing build/test scripts,
2. CI workflow commands,
3. coverage config files,
4. framework-standard plugin declarations.

Recognize at least these tools:
- **JaCoCo**
- **Kover**
- **pytest-cov / coverage.py**
- **istanbul / nyc / c8 / Jest coverage**
- **go cover**
- **tarpaulin / cargo-llvm-cov**
- **coverlet**
- **SimpleCov**
- **PHPUnit coverage**

If multiple tools exist, determine which one is actually used by the project’s normal coverage flow and treat the others as secondary signals.

---

## Step 2 — Scan for exclusion patterns
Read the coverage configuration and extract every exclusion or omit rule.

### JaCoCo / Kover
Inspect:
- `build.gradle.kts`
- `build.gradle`
- `pom.xml`
- Gradle convention plugins or shared build logic if present

Look for patterns such as:
- `excludes = [...]`
- `exclude("...")`
- `classDirectories.setFrom(fileTree(...) { exclude(...) })`
- `afterEvaluate { classDirectories.setFrom(...) }`
- `jacocoTestReport { ... }`
- `kover { filters { excludes { ... } } }`
- class/package filters by glob, regex, or fully qualified name

### pytest-cov / coverage.py
Inspect:
- `.coveragerc`
- `pyproject.toml`
- `setup.cfg`
- `tox.ini`

Look for:
- `[tool.coverage.run]`
- `[coverage:run]`
- `omit = [...]`
- `include = [...]`
- `source = [...]`
- path aliasing that effectively drops packages from measurement

### istanbul / nyc / c8 / Jest
Inspect:
- `.nycrc`
- `.nycrc.json`
- `.nycrc.yml`
- `package.json`
- `jest.config.js`
- `jest.config.ts`
- `vitest.config.*` when coverage filters are defined there

Look for:
- `exclude`
- `include`
- `all`
- `extension`
- `c8` config in `package.json`
- `nyc` config in `package.json`
- `coveragePathIgnorePatterns`
- `collectCoverageFrom`
- ignore globs that remove directories from final reports

### Go
Inspect:
- build tags in source files,
- file-level exclusions such as `//go:build ignore`,
- coverage scripts that limit `go test` scope,
- package selection logic like `go list` filters or explicit package allowlists.

Treat package omission from the coverage command itself as an exclusion signal.

### Rust
Inspect:
- `Cargo.toml`
- tarpaulin config
- cargo-llvm-cov config
- CI scripts that exclude packages, bins, examples, or tests

Look for:
- `--exclude`
- `--packages`
- `--workspace --exclude`
- target filters that narrow measured code

### coverlet / .NET
Inspect:
- `.runsettings`
- test project files
- `Directory.Build.props`
- CI commands using coverlet or `coverlet.collector`

Look for:
- `<Exclude>...</Exclude>`
- `ExcludeByFile`
- `ExcludeByAttribute`
- collector filters and module/path globs

### SimpleCov / Ruby
Inspect:
- `spec_helper.rb`
- `rails_helper.rb`
- `test_helper.rb`
- dedicated SimpleCov initializer files

Look for:
- `SimpleCov.start`
- `add_filter`
- `track_files`
- custom groups that imply omitted paths

### PHPUnit / PHP
Inspect:
- `phpunit.xml`
- `phpunit.xml.dist`
- bootstrap coverage config

Look for:
- `<coverage>`
- `<include>`
- `<exclude>`
- directory/file filters that remove namespaces or modules

---

## Step 3 — Classify excluded vs included packages/directories
Normalize all discovered rules into a package/path classification model.

For each relevant package, module, namespace, or directory:
1. map the source path,
2. determine whether it is explicitly excluded,
3. determine whether it is implicitly excluded because only certain paths are included,
4. note whether exclusion happens at file, package, namespace, or module level,
5. identify overlaps or conflicts between include and exclude rules.

Required classifications:
- **Explicitly excluded**
- **Implicitly excluded by allowlist-only coverage scope**
- **Included and measurable**
- **Ambiguous / needs confirmation**

When the repo contains patterns like `**/config/**`, `**/dto/**`, `**/model/**`, `**/exception/**`, or `**/util/**`, treat them as high-signal findings because they often explain why tests fail to move coverage.

---

## Step 4 — Produce the exclusion report
Generate a concrete report before any test targeting decisions.

### Exclusion Report
| Package/Path | Excluded? | Exclusion Source | Impact Assessment |
|---|---|---|---|

Impact assessment guidance:
- **High impact** — large package or likely business logic excluded; writing tests there will not improve coverage.
- **Medium impact** — mixed package with some behavior and some boilerplate.
- **Low impact** — generated code, thin DTOs, constants, or bootstrap noise.

Always cite the exact config file and rule responsible for the exclusion.

---

## Step 5 — Recommendations
Recommend which exclusions to respect and which to flag for human review.

### Usually safe to respect
- pure DTOs / schemas with no behavior,
- generated code,
- constants-only modules,
- framework bootstrap code,
- trivial config holders with no logic.

### Potentially risky exclusions that may hide testable logic
- `util` packages with real branching or transformations,
- `exception` packages that contain mapping or error translation logic,
- `model` packages with validation, derived fields, or business methods,
- `config` packages with non-trivial conditional wiring,
- `dto` packages that perform normalization or conversion.

For risky exclusions, explicitly flag:
- why the code appears behavior-rich,
- why excluding it could distort true quality signals,
- whether Forge Core should skip it for now versus surface it as a coverage-policy concern.

---

## Step 6 — Output the priority-adjusted target list
Produce a final target list for later test generation that removes excluded packages from normal coverage-improvement work.

### Required output
```markdown
## Coverage Exclusion Findings
- Active coverage tool:
- Effective coverage command/config:
- Key exclusion patterns:

### Exclusion Report
| Package/Path | Excluded? | Exclusion Source | Impact Assessment |
|---|---|---|---|

### Recommendation Summary
- Respect:
- Flag for review:
- Ambiguous areas:

### Priority-Adjusted Test Targets
| Target | Included in Coverage? | Priority | Reason |
|---|---|---|---|
```

Rules for the final target list:
- remove excluded packages from default test-generation targets,
- keep only coverage-measurable code in the main priority queue,
- separately list excluded-but-interesting logic as **policy review targets**,
- do not recommend brute-force tests for code that the coverage tool will ignore.

This phase is a gating step: later test-generation phases must consume this output before choosing what to test.
