# TestPilot Core Learnings

> This file is the shared memory of TestPilot Core.
> After each completed run, the agent appends **generalized**, **secret-free**, **reusable** learnings here.
> These learnings improve future analysis, broken-test repair, and unit-test generation across projects.

## How it works
TestPilot Core uses this file to store:
- failure patterns that repeat across projects,
- framework-specific mocking and fixture rules,
- coverage-tool workarounds,
- DI and global-state cleanup tactics,
- high-value testing heuristics.

### What belongs here
- reusable techniques,
- tooling fixes,
- framework gotchas,
- stable coverage insights.

### What must never be stored here
- secrets,
- tokens,
- credentials,
- proprietary business logic,
- large source-code excerpts,
- personal data.

---

## Learnings Log

### Project: ioh-order-hub | Stack: Kotlin/Ktor/Koin | Date: 2025-05-25

**Fix Patterns Discovered:**
1. **Kotlin `object` singleton mocking** — `mockk<Configuration>()` does not safely replace Kotlin `object` singletons. Prefer direct assignment of mutable configuration state or supported object mocking with explicit teardown.
2. **`every` vs `coEvery` in MockK** — Use `every {}` for regular functions/properties and `coEvery {}` for suspend functions. Mixing them produces misleading coroutine failures.
3. **DTO drift across large test suites** — When production DTOs evolve, broad test suites break in many places. Fix shared builders/factories first, then direct constructor calls.
4. **JaCoCo on JDK 21 requires an explicit version** — Use `toolVersion = "0.8.12"` when JaCoCo fails on newer JDKs.
5. **`ignoreFailures = true` keeps coverage reporting alive** — Without it, even one failing test can suppress report generation and break the iteration loop.
6. **Mock placement matters** — Do not insert MockK setup into the middle of multi-line call arguments. Keep all arrangement before execution.
7. **`ExceptionInInitializerError` from top-level vals** — Top-level values can trigger constructor chains before tests can set configuration. Establish required config before class load or mark the seam as integration-heavy.
8. **Time-dependent assertions are brittle** — Replace `now()`-based assertions with fixed timestamps to avoid timezone and near-midnight failures.
9. **Koin state leaks between tests** — Use `stopKoin()` and `unmockkAll()` around tests that manipulate DI or static/object state.
10. **JaCoCo under-reports `inline reified` Kotlin functions** — Prefer Kover when inline coverage matters.
11. **Kover may need fallback handling** — If Kover is configured but unreliable in a project, fall back to JaCoCo while preserving report generation.

**Coverage Insights:**
- Quickest gains came from services, mappers, and utility layers.
- Repo/infrastructure-heavy classes remained poor unit-test candidates without broader seams.
- Coverage loops were safest when broken tests were repaired before any new test generation.

**Tech Stack Notes:**
- Ktor + Koin projects are highly sensitive to leaked global state.
- Kotlin-heavy projects benefit from a clear distinction between unit-test targets and startup/bootstrap code.

---

### Project: Sentinel | Stack: Python/FastAPI/pytest | Date: 2025-06-14

**Fix Patterns Discovered:**
1. **Cached settings require explicit reset** — When settings are exposed through an `@lru_cache` function such as `get_settings()`, tests must call `get_settings.cache_clear()` before and after env/config changes.
2. **Patch where used, not where defined** — Patching `app.notifier.send_email` does nothing if the code under test imports and calls `app.pipeline.send_email`. Patch the symbol in the module actually using it.
3. **Async tests need the right harness** — Async service and route tests should use `pytest-asyncio` with `@pytest.mark.asyncio` and `AsyncMock` for awaited collaborators.
4. **ASGI-native route testing is more stable** — `httpx.AsyncClient` with `ASGITransport` provides deterministic FastAPI/Starlette route tests without spinning up a real server.
5. **Override lifespan to avoid expensive startup** — Expensive startup hooks such as NLP/ML model loads should be bypassed or overridden in tests.
6. **Real isolated SQLite beats deep DB mocking for many service tests** — Using a real isolated SQLite database file often produces more trustworthy tests than mocking every repository/database interaction.
7. **Fallback chains need explicit tests** — Notification pipelines such as API → SMTP → console should be tested branch by branch with deterministic mocked failures.
8. **Global DB path state must be patched for isolation** — Module-level state such as `DB_PATH` should be patched per test or fixture so tests do not collide.
9. **Mock model boundaries, not the whole world** — For NLP/ML-backed endpoints, patch model loaders or prediction methods at the boundary rather than reproducing real model startup.
10. **Env-var config tests require cache discipline** — `monkeypatch.setenv()` is not enough on its own if settings are cached; pair env updates with cache clearing.

**Coverage Insights:**
- Highest ROI came from service functions, route handlers with dependency overrides, and notification/error-path tests.
- Deterministic async harnesses and settings-cache resets removed a large class of false negatives.
- Database-backed tests were most reliable when using isolated per-test DB state.

**Tech Stack Notes:**
- FastAPI projects often fail at import/startup boundaries rather than inside the actual business logic.
- Lifespan overrides and cache clearing are core test hygiene for production-grade FastAPI suites.

---

<!-- Append new learnings below this line. -->
