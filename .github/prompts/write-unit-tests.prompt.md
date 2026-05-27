---
mode: agent
description: "Write production-grade backend unit tests in full-project or targeted mode with language-specific guidance and rollback-safe execution"
tools: ["bash", "glob", "grep", "view", "edit", "create"]
---

# Write Unit Tests

Generate or improve backend unit tests without touching production code.

## Hard Rules
1. **Never modify production/source code.**
2. Match the project’s existing test style where it is healthy.
3. Prefer new test files or additive test cases over risky rewrites.
4. Mock external I/O at the seam.
5. Keep tests deterministic and isolated.
6. Compile and run after each batch.

---

## Mode handling

### Full project mode
Write tests for the highest-value uncovered backend files.

### Targeted mode
Write tests only for the user-requested classes/files.
- Read the target fully.
- Identify all collaborators/imports.
- Mock collaborators; do not create separate tests for them unless requested.
- Measure coverage only for the targets.

---

## Prioritization order
Use this order by default:
1. **Services / business logic**
2. **Adapters / handlers / controllers / routes**
3. **Utils / helpers**
4. **Mappers / transformers**
5. Clients with mocked I/O
6. Repositories if isolation is straightforward
7. DTOs only when they contain logic/validation

---

## Test design checklist
Each test should:
- validate one behavior,
- follow AAA or equivalent clear structure,
- have a descriptive name,
- cover happy path and meaningful error branches,
- avoid hidden shared state,
- use stable fixtures,
- assert behavior, not implementation trivia.

---

## Batch workflow
For each batch:
1. read the target source file(s),
2. trace dependencies,
3. identify uncovered branches,
4. write tests,
5. compile/run,
6. generate coverage,
7. compare against prior accepted coverage,
8. keep or roll back the batch.

---

## Rollback rules
If the batch causes coverage regression or suite instability:
1. diagnose the reason,
2. try one deterministic fix pass,
3. rerun tests and coverage,
4. if still worse, revert only that iteration’s test changes,
5. move to a different target set.

Never keep a batch that lowers accepted coverage.

---

## Language-specific playbooks

### Python (pytest / FastAPI / Flask / Django)
Preferred patterns:
- `pytest` fixtures in `conftest.py`
- `pytest.mark.asyncio` for async tests
- `AsyncMock`, `MagicMock`, `patch`, `monkeypatch`
- `httpx.AsyncClient` + `ASGITransport` for ASGI apps
- isolated SQLite or transactional DB fixtures when needed

Example:
```python
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_send_welcome_email_falls_back_to_console(app):
    transport = ASGITransport(app=app)
    with patch("app.pipeline.send_email", new=AsyncMock(side_effect=RuntimeError("smtp down"))), \
         patch("app.pipeline.write_console", new=AsyncMock()) as console_mock:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/notify", json={"email": "a@test.com"})

    assert response.status_code == 200
    console_mock.assert_awaited_once()
```

### Java / Kotlin
Preferred patterns:
- JUnit 5 where present
- Mockito for Java, MockK for Kotlin
- use existing Spring/Ktor conventions
- use fixed clocks and builders for test data

Kotlin example:
```kotlin
class OrderServiceTest {
    private val repo = mockk<OrderRepository>()
    private val mapper = mockk<OrderMapper>()
    private val service = OrderService(repo, mapper)

    @BeforeEach
    fun setUp() {
        stopKoin()
    }

    @AfterEach
    fun tearDown() {
        unmockkAll()
        stopKoin()
    }

    @Test
    fun `getOrder returns mapped response`() = runTest {
        coEvery { repo.fetch("123") } returns OrderEntity("123")
        every { mapper.toDto(any()) } returns OrderDto("123")

        val result = service.getOrder("123")

        assertEquals("123", result.id)
    }
}
```

Java example:
```java
@ExtendWith(MockitoExtension.class)
class PaymentServiceTest {
    @Mock PaymentGateway gateway;
    @InjectMocks PaymentService service;

    @Test
    void charge_throws_when_gateway_fails() {
        when(gateway.charge(any())).thenThrow(new RuntimeException("boom"));

        assertThrows(RuntimeException.class, () -> service.charge(new ChargeRequest()));
        verify(gateway).charge(any());
    }
}
```

### Go
Preferred patterns:
- table-driven tests,
- `httptest`,
- `testify/assert` or standard library assertions,
- `gomock` or small hand-written interface fakes.

Example:
```go
func TestNormalizeStatus(t *testing.T) {
    cases := []struct {
        name string
        input string
        want string
    }{
        {"trimmed", " ok ", "OK"},
        {"empty", "", "UNKNOWN"},
    }

    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            got := NormalizeStatus(tc.input)
            if got != tc.want {
                t.Fatalf("want %s, got %s", tc.want, got)
            }
        })
    }
}
```

### Node.js (Express / Fastify / Nest)
Preferred patterns:
- Jest or Vitest based on project choice,
- Supertest for HTTP layers,
- `jest.mock`, `jest.spyOn`, or `vi.mock`,
- reset modules/mocks between tests.

Example:
```ts
import request from "supertest";
import { app } from "../src/app";
import * as userService from "../src/services/user-service";

jest.spyOn(userService, "getUser").mockResolvedValue({ id: "1", name: "A" });

describe("GET /users/:id", () => {
  afterEach(() => jest.restoreAllMocks());

  it("returns the user", async () => {
    const response = await request(app).get("/users/1");
    expect(response.status).toBe(200);
    expect(response.body.id).toBe("1");
  });
});
```

### Rust
Preferred patterns:
- module-local unit tests for pure logic,
- `mockall` or trait-based seams for collaborators,
- explicit arrangement of inputs and expected outputs.

Example:
```rust
#[test]
fn normalize_status_defaults_empty_input() {
    let got = normalize_status("");
    assert_eq!(got, "UNKNOWN");
}
```

### C# / .NET
Preferred patterns:
- xUnit or NUnit per project convention,
- Moq or NSubstitute,
- `WebApplicationFactory` only when controller-level testing is intended,
- direct service tests for business logic.

Example:
```csharp
public class InvoiceServiceTests
{
    [Fact]
    public async Task CreateAsync_Throws_WhenRepositoryFails()
    {
        var repo = new Mock<IInvoiceRepository>();
        repo.Setup(r => r.SaveAsync(It.IsAny<Invoice>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new InvalidOperationException("db"));

        var service = new InvoiceService(repo.Object);

        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            service.CreateAsync(new InvoiceRequest(), CancellationToken.None));
    }
}
```

---

## Stack-specific reminders
- **FastAPI:** clear cached settings, patch where used, override lifespan when needed.
- **Kotlin/MockK:** use `every` vs `coEvery` correctly; clean up Koin and MockK state.
- **Spring:** prefer slice tests (`@WebMvcTest`, `@DataJpaTest`) over full context when possible.
- **Node:** reset env vars and mocks between tests.
- **Go:** prefer table-driven cases for branch-heavy pure functions.
- **Rust:** prefer trait seams over global state.
- **C#**: isolate DI setup and avoid unnecessary full-host bootstraps.

---

## Required iteration report
After each batch, report:
- files created/updated,
- tests added,
- suite result,
- coverage before/after,
- whether the batch was accepted or rolled back,
- next best target areas.
