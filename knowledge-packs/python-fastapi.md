# Knowledge Pack — Python / FastAPI

Use this pack when TestPilot Core detects a Python backend built with FastAPI, Starlette, or a similar ASGI stack.

## Mission
Generate deterministic unit and lightweight service/route tests without modifying production code.

---

## 1. Recommended test stack
- **Runner:** `pytest`
- **Async support:** `pytest-asyncio`
- **Mocking:** `unittest.mock`, `pytest-mock`, `AsyncMock`, `MagicMock`
- **ASGI route tests:** `httpx.AsyncClient` + `ASGITransport`
- **Coverage:** `pytest-cov`

Common command:
```bash
pytest --cov=app --cov-report=term-missing --cov-report=xml --cov-report=html
```

---

## 2. Fixture and `conftest.py` patterns
Prefer reusable fixtures for:
- application factory,
- settings override,
- database path override,
- seeded users/data,
- mocked external clients,
- fake mailer/notifier,
- fixed timestamps.

Example fixture structure:
```python
import pytest
from app.config import get_settings

@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
```

### Good fixture practices
- keep fixtures narrow and composable,
- use `autouse=True` only for truly global resets,
- isolate env var changes and cache clearing,
- prefer per-test DB state for mutation-heavy scenarios.

---

## 3. Async testing with `pytest-asyncio`
Whenever code under test is async:
- mark tests with `@pytest.mark.asyncio`,
- use `AsyncMock` for awaited collaborators,
- assert awaited calls with `assert_awaited_once*` helpers.

Example:
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_process_order_uses_gateway():
    gateway = AsyncMock()
    gateway.charge.return_value = {"status": "ok"}

    result = await process_order(gateway, order_id="123")

    assert result["status"] == "ok"
    gateway.charge.assert_awaited_once()
```

---

## 4. FastAPI route testing with `httpx.AsyncClient` + `ASGITransport`
Prefer ASGI-native route tests over spinning up a real server.

Example:
```python
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_healthcheck(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
```

### Why this matters
- no real network,
- fast and deterministic,
- closer to framework behavior than hand-calling route functions,
- works well with dependency overrides.

---

## 5. Mock where used, not where defined
This is one of the most important FastAPI/Python rules.

If a function is imported into `app.pipeline`, patch `app.pipeline.send_email`, not the original source module.

Example:
```python
with patch("app.pipeline.send_email", new=AsyncMock(return_value=True)):
    ...
```

If you patch the wrong import path, the real code still executes.

---

## 6. `AsyncMock` vs `MagicMock` vs `Mock`
Use:
- `AsyncMock` for `async def` functions,
- `MagicMock` for richer objects/protocols/context managers,
- `Mock` for simple sync call sites.

Typical mistakes:
- using `MagicMock` for awaited functions,
- returning plain dicts where a response object/interface is expected,
- forgetting `side_effect` for exception paths.

---

## 7. Database isolation with real SQLite
For data-access or service tests, prefer a real isolated SQLite database over deep repository mocks when the code path is SQL-heavy.

Recommended tactics:
- create a test-only DB file per test/session,
- monkeypatch the module-level `DB_PATH`,
- run migrations/DDL in fixture setup if needed,
- remove or reset state between tests.

Example:
```python
@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr("app.db.DB_PATH", str(db_file))
    return db_file
```

If `tmp_path` is unavailable in the actual project pattern, create an isolated DB file under the repo’s test workspace.

---

## 8. Settings caching and `@lru_cache`
If settings are provided by a cached function such as:
```python
@lru_cache
def get_settings() -> Settings:
    ...
```
then you must clear it in fixtures whenever env vars or settings inputs change.

Required pattern:
```python
get_settings.cache_clear()
```

Use before and after tests that mutate config state.

---

## 9. Lifespan override for expensive startup work
FastAPI apps often load expensive NLP/ML models, external clients, or caches during startup.

Testing pattern:
- override startup/lifespan hooks,
- replace expensive loaders with mocks/fakes,
- keep route behavior testable without the real heavyweight dependency.

Typical targets:
- embedding models,
- LLM clients,
- vector DB clients,
- SMTP/API notifiers,
- secrets/config fetchers.

---

## 10. Email / notification fallback testing
If the app has multiple notification channels, test the fallback chain explicitly.

Example chain:
- primary API provider
- SMTP fallback
- console/log fallback

Test each case deterministically:
1. API succeeds,
2. API fails and SMTP succeeds,
3. both fail and console fallback is used.

Use `AsyncMock(side_effect=...)` to drive branches.

---

## 11. NLP / ML model mocking
For model-dependent flows:
- mock the model boundary, not deep math internals,
- return stable deterministic embeddings/classifications,
- avoid downloading/loading real models during unit tests.

Good targets to patch:
- `load_model()`
- `embed()`
- external inference clients
- expensive startup registries

---

## 12. Configuration testing with env vars
Use `monkeypatch.setenv()` / `delenv()` to test:
- required env vars,
- optional defaults,
- invalid values,
- feature flags,
- mode switching.

Always pair env var mutation with settings cache clearing.

---

## 13. Prioritization guidance
Highest-value FastAPI targets:
1. service/business logic functions,
2. route handlers with dependency overrides,
3. mappers/serializers,
4. validation/error translation,
5. notifier/adapters with mocked external calls.

Lower priority:
- pure Pydantic models with no custom validators,
- bootstrap-only files,
- app launch scripts.

---

## 14. Common anti-patterns to avoid
- patching the wrong module path,
- using sync client for async app code,
- leaving cached settings uncleared,
- mocking the DB so deeply that queries are not meaningfully exercised,
- relying on wall-clock time,
- letting startup hooks load real models/services.

---

## 15. Sentinel-derived battle-tested checklist
Before finishing a FastAPI batch, confirm:
- `get_settings.cache_clear()` is handled,
- patches are applied where used,
- async tests are marked correctly,
- ASGI tests use `AsyncClient` + `ASGITransport`,
- expensive lifespan work is overridden,
- DB state is isolated,
- fallback behavior is explicitly tested,
- global DB/config paths are restored after tests.
