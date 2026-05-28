---
mode: agent
description: "Generate, parse, and compare backend coverage reports across Java, Kotlin, Python, Node.js, Go, Rust, C#, Ruby, and PHP with stack-specific fallbacks"
tools: ["bash", "glob", "grep", "view"]
---

# Generate Coverage Report

Generate coverage using the project’s configured tooling first, then apply stack-specific fallback chains.

## Step 1 — Use the project’s existing command first
Check, in order:
1. package/build scripts already named for coverage,
2. CI workflow commands,
3. existing coverage config/plugins,
4. framework-standard fallback commands.

Never invent a new coverage stack if the project already has one.

---

## Step 2 — Coverage tool matrix and fallback chains

| Language | Preferred Tool | Fallback 1 | Fallback 2 | Typical Reports |
|---|---|---|---|---|
| Java | Project JaCoCo config | Maven/Gradle JaCoCo | Surefire + JaCoCo XML/HTML | XML, HTML |
| Kotlin | Project Kover config | JaCoCo latest | JaCoCo default | XML, HTML |
| Python | pytest-cov | coverage.py | pytest with plugin-defined config | XML, HTML, terminal |
| Node.js | project script (`test:coverage`) | c8 | nyc / built-in Jest/Vitest coverage | lcov, cobertura, text |
| Go | `go test -coverprofile` | package-level coverprofile | `go tool cover -func` parsing | text, HTML |
| Rust | cargo-tarpaulin | cargo-llvm-cov | grcov if already configured | XML, HTML, text |
| C# | dotnet test + coverlet | collector-based cobertura | existing pipeline script | cobertura, json |
| Ruby | SimpleCov in suite | rspec/minitest coverage task | project script | HTML, text |
| PHP | PHPUnit coverage config | `phpunit --coverage-clover` | project script | XML, HTML, text |

---

## Step 3 — Stack-specific guidance

### Java / Maven
Typical commands:
- `mvn test`
- `mvn test jacoco:report`

### Java / Kotlin / Gradle
Typical commands:
- `./gradlew test`
- `./gradlew jacocoTestReport`
- `./gradlew koverXmlReport koverHtmlReport`

**JaCoCo JDK 21+ fix:**
```kotlin
jacoco { toolVersion = "0.8.12" }
```

**Duplicate class instrumentation fix:**
```kotlin
tasks.jacocoTestReport {
    classDirectories.setFrom(fileTree("build/classes") {
        exclude("**/generated/**", "**/META-INF/**", "**/shaded/**")
    })
}
```

**Keep reports generating despite failing tests:**
```kotlin
tasks.withType<Test> {
    ignoreFailures = true
}
```

**Kotlin note:** for `inline reified` coverage, prefer Kover over JaCoCo.

### Python
Typical commands:
- `pytest --cov=<package> --cov-report=term-missing --cov-report=xml --cov-report=html`
- `coverage run -m pytest && coverage xml && coverage html`

If the project already has `.coveragerc`, `pytest.ini`, or `pyproject.toml` coverage config, respect it.

### Node.js
Typical commands:
- `npm test -- --coverage`
- `npm run test:coverage`
- `npx c8 npm test`
- `npx nyc npm test`
- `vitest run --coverage`

Prefer scripts declared in `package.json`.

### Go
Typical commands:
- `go test ./... -coverprofile=coverage.out`
- `go tool cover -func=coverage.out`
- `go tool cover -html=coverage.out -o coverage.html`

For targeted mode, measure the package(s) containing the requested files.

### Rust
Typical commands:
- `cargo tarpaulin`
- `cargo llvm-cov --lcov --output-path lcov.info`
- use existing workspace script if present.

### C# / .NET
Typical commands:
- `dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=cobertura`
- `dotnet test --collect:"XPlat Code Coverage"`

Prefer existing test project settings and `Directory.Build.props` if present.

### Ruby
Typical commands:
- `bundle exec rspec`
- `bundle exec rake test`
- coverage usually emitted by `SimpleCov` when configured in test helper.

### PHP
Typical commands:
- `vendor/bin/phpunit --coverage-clover coverage.xml --coverage-html coverage-html`
- or framework-defined scripts in `composer.json`.

---

## Step 4 — Monorepo rules
In monorepos:
- run coverage per backend module first,
- avoid combining incompatible coverage formats unless the repo already does so,
- report per-module coverage and overall summary,
- in targeted mode, measure only the module(s) containing the targets.

---

## Step 5 — Parse reports
Prefer machine-readable reports when available.

### Parse in this order
1. XML / Cobertura / JaCoCo / Clover / coverage.xml
2. lcov / json summary
3. HTML index pages
4. terminal text summaries

Extract:
- overall line coverage,
- branch coverage if available,
- covered vs total lines,
- per-package or per-module breakdown,
- per-class breakdown for targets,
- top uncovered files with feasible test value.

### Exclusion-aware parsing
When an exclusion map is available from Phase 1.5:
- report coverage for included packages only in the primary metrics,
- report excluded package coverage separately as "correctness coverage" (does not affect primary metrics),
- flag any excluded packages where tests were generated for correctness purposes.

---

## Step 6 — Targeted mode parsing
If the user requested specific classes/files, produce:

| Target | Covered Lines | Total Lines | Coverage % | Notes |
|---|---:|---:|---:|---|

Do **not** dilute targeted results with unrelated modules.

---

## Step 7 — Comparison output
Always compare current coverage to the prior accepted state.

```markdown
## Coverage Report
- Overall line coverage:
- Overall branch coverage:
- Previous accepted coverage:
- Current coverage delta:

### Per-Module / Per-Package
| Scope | Covered | Total | Coverage % |
|---|---:|---:|---:|

### Priority Gaps
| File | Coverage % | Uncovered Lines | Feasible? | Reason |
|---|---:|---:|---|---|
```

---

## Step 8 — Rollback contract
If the newly generated coverage is lower than the previous accepted coverage:
- mark the run as a coverage regression,
- help identify which test batch caused it,
- provide the exact numbers needed for rollback decisions.
