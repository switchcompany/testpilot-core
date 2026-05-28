# 🔥 Forge Core — AI Backend Test Generation Agent

> **Drop-in agentic workflow that auto-generates unit tests for any backend project, in any language.**
> Zero production code changes. 90%+ coverage. Self-learning.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Agent: Copilot](https://img.shields.io/badge/Agent-GitHub%20Copilot-black.svg)](https://github.com/features/copilot)
[![Stacks: 9+](https://img.shields.io/badge/Stacks-9%2B%20Languages-green.svg)](#supported-stacks)

---

## 🎯 What It Does

Forge Core is an **AI-powered test engineer** that analyzes your backend codebase and generates comprehensive unit tests — automatically. It understands your architecture, detects your tech stack, writes idiomatic tests, and iterates until coverage targets are met.

```
Your Backend Project + Forge Core = 90%+ Test Coverage
```

### Key Capabilities

| Feature | Description |
|---------|-------------|
| 🔍 **Auto Stack Detection** | Detects language, framework, test tools, and coverage system automatically |
| 🧠 **Deep Architecture Analysis** | Understands HLD/LLD, dependency chains, DI containers, and data flows |
| ✍️ **Intelligent Test Generation** | Writes idiomatic tests using your project's existing patterns and conventions |
| 🔄 **Iterative Coverage Loop** | Runs up to 10 iterations, each time targeting the biggest coverage gaps |
| 🛡️ **Rollback Protection** | Never allows coverage to drop — automatically reverts harmful changes |
| 📚 **Self-Learning** | Captures new patterns after each run, making itself smarter for every future project |
| 🎯 **Targeted Mode** | Generate tests for specific classes only (with dependency mocking) |
| 🏗️ **Monorepo Support** | Works with multi-module projects (Gradle, npm workspaces, etc.) |
| 🎯 **Coverage Exclusion Detection** | Detects excluded packages before generating tests — zero wasted effort |
| 🌊 **Cascade Coverage** | Maps call chains to find high-cascade test targets for maximum coverage ROI |
| 📊 **Coverage Impact Predictor** | Estimates which tests will cover the most lines before writing them |
| ⚡ **Auto Compile-Fix** | Autonomously fixes compilation errors — zero human intervention needed |
| 🏢 **Enterprise Pattern Library** | Structured, searchable patterns that grow with every engagement |
| 🚀 **Speed-Optimized** | Parallel generation, smart batching, incremental coverage, architecture caching — enterprise projects in under 45 minutes |

---

## 🚀 Quick Start

### 1. Clone Forge Core (once per team)
```bash
git clone https://github.com/switchcompany/forge-core.git
cd forge-core
```

### 2. Set Up Your Project
```bash
./setup.sh /path/to/your/backend/project
```

This copies the agent files into your project's `.github/` directory.

### 3. Run with Copilot
Open your project in VS Code / IntelliJ with GitHub Copilot, then:

**Option A — Full Project Run:**
```
@workspace Run the full-workflow prompt to analyze this project and generate unit tests
```

**Option B — Specific Classes:**
```
@workspace Run full-workflow for these classes: UserService, OrderController, PaymentAdapter
```

**Option C — Via GitHub Issue:**
Create an issue using the "Analyze & Test" template → Copilot agent picks it up automatically.

---

## 📊 Supported Stacks

| Language | Frameworks | Test Runner | Mock Library | Coverage |
|----------|-----------|-------------|--------------|----------|
| **Python** | FastAPI, Django, Flask, Starlette | pytest | unittest.mock, pytest-mock | pytest-cov |
| **Java** | Spring Boot, Micronaut, Quarkus | JUnit 5 | Mockito | JaCoCo |
| **Kotlin** | Ktor, Spring Boot | JUnit 5, Kotest | MockK | Kover, JaCoCo |
| **Node.js** | Express, Fastify, NestJS, Koa | Jest, Vitest, Mocha | jest.mock, sinon | c8, istanbul |
| **Go** | stdlib, Gin, Echo, Fiber | testing | testify, gomock | go cover |
| **Rust** | Actix, Axum, Rocket | built-in | mockall | tarpaulin |
| **C#** | ASP.NET Core, Minimal APIs | xUnit, NUnit | Moq, NSubstitute | coverlet |
| **Ruby** | Rails, Sinatra, Hanami | RSpec, Minitest | rspec-mocks | simplecov |
| **PHP** | Laravel, Symfony, Slim | PHPUnit | Mockery, Prophecy | phpunit --coverage |

---

## 🔄 How It Works

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Forge Core — Workflow                           │
│                                                                      │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Load    │─▶│ Detect  │─▶│ Exclusion│─▶│ Analyze  │─▶│Cascade │  │
│  │Learnings│  │ Stack   │  │  Scan    │  │ Project  │  │ Graph  │  │
│  └─────────┘  └─────────┘  └──────────┘  └──────────┘  └───┬────┘  │
│                                                              │       │
│  ┌─────────┐  ┌──────────────────────────────────────┐      │       │
│  │ Self-   │◀─│     Iteration Loop (×10)             │◀─────┘       │
│  │ Learn   │  │ Fix → Generate → Auto-Fix → Rollback │              │
│  └─────────┘  └──────────────────────────────────────┘              │
│                                                                      │
│  Output: Tests + Coverage Report + Cascade Map + Learnings           │
└──────────────────────────────────────────────────────────────────────┘
```

### Phase Breakdown

| Phase | Action | Output |
|-------|--------|--------|
| **-1** | Load learnings from central hub + local | Pattern library |
| **0** | User confirmation (full/targeted/analyze) | Mode selection |
| **1** | Detect tech stack from build files | Stack profile |
| **1.5** | Scan coverage exclusions | Exclusion map |
| **2** | Deep project analysis (HLD/LLD/flows) | Architecture map |
| **2.5** | Build dependency graph & cascade map | Cascade coverage targets |
| **3** | Scan & run existing tests, measure baseline | Baseline coverage % |
| **3.5** | Fix broken tests (10+ battle-tested patterns) | Fixed test suite |
| **4** | Iterative test generation with auto compile-fix (up to 10 rounds) | New test files |
| **5** | Final report (before/after, gaps, files) | Coverage report |
| **6** | Capture new patterns to LEARNINGS.md | Updated knowledge |

---

## 🛡️ Safety Guarantees

- ✅ **Zero production code changes** — only test files are created/modified
- ✅ **Rollback protection** — coverage never goes backwards
- ✅ **No flaky tests** — deterministic assertions, no random/network/timing
- ✅ **Existing tests preserved** — never deletes passing tests
- ✅ **No secrets in learnings** — LEARNINGS.md contains patterns, never source code

---

## 📚 Knowledge Packs

Pre-seeded knowledge for common stacks (in `knowledge-packs/`):

| Pack | Patterns | Source |
|------|----------|--------|
| `python-fastapi.md` | 15+ patterns | Learned from production FastAPI project |
| `kotlin-ktor.md` | 11+ patterns | Learned from production Ktor/Koin project |
| `java-spring.md` | 12+ patterns | Spring Boot best practices |
| `node-express.md` | 10+ patterns | Express/NestJS patterns |
| `go-stdlib.md` | 10+ patterns | Go testing idioms |

These grow automatically as the agent runs on more projects.

---

## 📁 Repository Structure

```
forge-core/
├── .github/
│   ├── copilot-instructions.md          # Agent brain — 500+ lines of instructions
│   ├── copilot-setup-steps.yml          # Environment verification
│   ├── agent-config.yml                 # Central hub path config
│   ├── ISSUE_TEMPLATE/
│   │   └── analyze-and-test.yml         # GitHub Issue trigger template
│   └── prompts/
│       ├── full-workflow.prompt.md      # Main orchestrator
│       ├── detect-tech-stack.prompt.md  # Stack detection playbook
│       ├── coverage-exclusion-scan.prompt.md  # Coverage exclusion scan
│       ├── analyze-project.prompt.md    # Architecture analysis
│       ├── dependency-graph.prompt.md   # Cascade dependency graph
│       ├── analyze-existing-tests.prompt.md  # Test audit
│       ├── generate-coverage-report.prompt.md  # Coverage tools
│       ├── write-unit-tests.prompt.md   # Test writing playbook
│       ├── fix-broken-tests.prompt.md   # Fix patterns
│       └── self-learn.prompt.md         # Knowledge capture
├── knowledge-packs/
│   ├── python-fastapi.md
│   ├── kotlin-ktor.md
│   ├── java-spring.md
│   ├── node-express.md
│   └── go-stdlib.md
├── LEARNINGS.md                         # Cross-project knowledge base
├── setup.sh                             # Project setup script
├── update.sh                            # Update script
├── ARCHITECTURE.md                      # System architecture docs
├── CONTRIBUTING.md                      # Contribution guide
├── SECURITY.md                          # Security policy
└── LICENSE                              # MIT License
```

---

## 📈 POC Results

### Sentinel — AI Social Media Monitor (Python/FastAPI)

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| **Line Coverage** | 0% | 89% | +89% |
| **Test Files** | 0 | 8 | +8 |
| **Test Cases** | 0 | 145 | +145 |
| **Iterations** | — | 3 | — |
| **Production Files Modified** | — | 0 | ✅ |

**Patterns Discovered:** 11 (cached settings, async mocking, ASGI testing, DB isolation, lifespan override, fallback behavior testing, NLP model mocking)

### Assembler-Service — Enterprise E-Commerce Backend (Kotlin/Ktor)

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| **Line Coverage** | 35.1% | 36.3% | +1.2% |
| **Method Coverage** | 44.2% | 48.2% | +4.0% |
| **Test Files** | 60 | 69 | +9 |
| **Test Cases** | 269 | 416 | +147 |
| **Patterns Discovered** | — | 9 | — |
| **Production Files Modified** | — | 0 | ✅ |

**Key Achievement:** Enterprise-grade Kotlin codebase with 209 source files, 15K+ lines, Koin DI, MockK, complex adapter patterns. Discovered 9 new reusable patterns.

---

## 🏢 Enterprise Features

- **Cross-project learning** — patterns from Project A help Project B automatically
- **Central knowledge hub** — team-wide learnings sync via git
- **Targeted mode** — test specific classes without analyzing the entire project
- **Monorepo support** — works with multi-module builds
- **CI/CD integration** — trigger via GitHub Issues or Copilot CLI
- **Audit trail** — every decision logged in the final report

---

## 📄 License

MIT © 2025 [TheSwitchCompany](https://theswitchcompany.online)

---

<p align="center">
  <strong>Forge Core</strong> — Part of the <a href="https://theswitchcompany.online">TheSwitchCompany</a> AI Agent Suite<br/>
  <em>Forge Core · Forge UI · More agents coming soon</em>
</p>
