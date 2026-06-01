# Knowledge Pack — Kotlin / Ktor

Use this pack when the backend is Kotlin-based and commonly uses Ktor, coroutines, MockK, Koin, Gradle, and JaCoCo/Kover.

---

## 1. Core testing stack
- **Runner:** JUnit 5 or existing project convention
- **Mocking:** MockK
- **Coverage:** Kover first for Kotlin-heavy projects, JaCoCo fallback
- **Coroutines:** `runTest` or project-standard coroutine test harness

---

## 2. Singleton mocking (`object`)
Kotlin `object` singletons are a common source of broken tests.

### Key rule
Do **not** assume `mockk<SomeObject>()` will replace a Kotlin `object`.

Preferred tactics:
- assign mutable test properties directly,
- use supported object mocking carefully,
- always tear down static/object mocks after each test.

Example pattern:
```kotlin
@BeforeEach
fun setUp() {
    stopKoin()
    Configuration.env = testConfig
}
```

---

## 3. `every` vs `coEvery`
Use:
- `every { ... }` for normal functions and properties,
- `coEvery { ... }` for suspend functions.

Mixing them causes coroutine-related failures and misleading test errors.

Also pair verifications correctly:
- `verify { ... }`
- `coVerify { ... }`

---

## 4. DTO drift / data-class changes
Large Kotlin test suites frequently break when DTO fields change.

Symptoms:
- missing constructor args,
- wrong named parameter,
- stale fixture JSON,
- type mismatch after model evolution.

Fix strategy:
1. read the current production data class,
2. update shared builders/factories first,
3. update direct constructor calls next,
4. recompile frequently in small batches.

---

## 5. JaCoCo on JDK 21
If JaCoCo fails on modern JDKs, pin:
```kotlin
jacoco { toolVersion = "0.8.12" }
```

If you see duplicate or bundled class errors, restrict class directories to compiled project classes.

---

## 6. `ignoreFailures = true`
Coverage reports often disappear entirely if any test fails.

Preserve report generation with:
```kotlin
tasks.withType<Test> {
    ignoreFailures = true
}
```

This is critical during repair and iteration phases.

---

## 7. Mock placement rules
Never insert mock/stub setup:
- inside multi-line function arguments,
- after the act step,
- mid-builder chain unless you are sure of scope.

Place all MockK arrangement before execution.

---

## 8. `ExceptionInInitializerError` from top-level vals
Top-level values such as:
```kotlin
val dao = DAOFacadeImpl()
```
can trigger constructor chains at class-load time.

If those constructors depend on config or infra, tests fail before setup runs.

Fix options:
- establish required config before the class is loaded,
- mock the static provider if safe,
- skip unit coverage if the seam is too hostile and document it.

---

## 9. Time assertions
Never assert against `LocalDateTime.now()` or similar wall-clock values.

Use fixed timestamps:
```kotlin
val now = LocalDateTime.of(2024, 1, 15, 10, 30, 0)
```

This avoids timezone and near-midnight failures.

---

## 10. Koin state leaks
Tests that pass alone but fail in suite often leak Koin or MockK state.

Recommended cleanup:
```kotlin
@BeforeEach
fun before() {
    stopKoin()
}

@AfterEach
fun after() {
    unmockkAll()
    stopKoin()
}
```

Use `@DirtiesContext`-style thinking sparingly; prefer explicit cleanup.

---

## 11. Kotlin inline reified coverage
JaCoCo may under-report or fail to instrument `inline reified` functions.

If coverage matters for inline-heavy clients/helpers, prefer **Kover**.
If the code executes but coverage is implausibly low, treat JaCoCo as the limitation, not necessarily the tests.

---

## 12. Ktor-specific notes
When testing Ktor handlers/routes:
- prefer project-standard Ktor test harness,
- mock downstream clients/services,
- isolate auth/context setup,
- verify serialization and status codes deterministically.

---

## 13. High-value target order
1. services/use-cases,
2. route handlers,
3. mappers,
4. utils,
5. adapter/client wrappers with mocked I/O.

Lower value:
- bootstrap,
- generated code,
- pure constants/data holders.

---

## 14. Kotlin/Ktor completion checklist
Before accepting a batch, confirm:
- correct `every`/`coEvery` usage,
- singleton config handled safely,
- Koin + MockK cleanup present,
- fixed time sources used,
- DTO builders aligned to current model,
- coverage tool behavior understood if inline functions are involved.

---

## 15. JaCoCo coverage exclusion detection
Before generating tests, always scan `build.gradle.kts` or `build.gradle` for JaCoCo exclusion patterns.

Common exclusion locations:
```kotlin
tasks.jacocoTestReport {
    classDirectories.setFrom(fileTree("build/classes") {
        exclude("**/config/**", "**/dto/**", "**/model/**", "**/exception/**", "**/util/**")
    })
}
```

Tests for excluded packages improve correctness but won't move coverage metrics. Prioritize included packages first.

---

## 16. NotImplemented adapter testing
When adapter classes implement interfaces but throw `NotImplementedError` for most methods:

```kotlin
@Test
fun `method throws NotImplementedError`() {
    assertThrows<NotImplementedError> { adapter.someMethod(params) }
}
```

Each test is 3 lines, covers 1-2 source lines. Highest coverage-per-effort pattern for large adapter interfaces.

---

## 17. Extension function imports
Kotlin extension functions in companion objects or top-level files must be imported explicitly:

```kotlin
import com.example.mapper.BBMapper.getAddToCartRequest
import com.example.mapper.BBMapper.formatPrice
```

The receiver type determines which overload resolves.

---

## 18. Global mutable adapter maps
Enterprise projects often use a global mutable map to route requests to adapters:

```kotlin
var serviceAdapter: HashMap<String, NCAdapter> = HashMap()
```

Tests must initialize this map in `@BeforeEach`. Forgetting causes `invalidProgramId()` exceptions.

---

## 19. Top-level val configuration
Mappers and adapters often depend on a top-level val like `val configProp = ConfigProps.configProp`. Tests must ensure config is set up before importing mapper/adapter classes.

---

## 20. Journey-based testing strategy
Prefer journey-based testing on enterprise services:
- Trace the complete user journey before writing any test
- Test `CartService.getCart()` understanding the full flow: Route → Service → Adapter → Client → Mapper
- Use the DTO registry for constructor signatures — never re-read DTO files
- Use journey-weighted prioritization: critical journeys → orchestration → adapters → mappers → utils → gap fill

---

## 21. Kotlin/Ktor enterprise completion checklist
Before accepting a batch on enterprise Kotlin projects:
- JaCoCo exclusions checked and respected,
- DTO constructors verified against current production signatures (or DTO registry),
- Extension function imports correct,
- Global mutable state initialized in `@BeforeEach`,
- Top-level config vals set up before class loading,
- Koin started with required bindings even for throw-only tests,
- NotImplemented patterns used for interface coverage,
- Journey-weighted targets prioritized over individual function tests.

---

## 22. MockEngine pattern for Kotlin inline reified functions

### The Problem
Kotlin `object` singletons with `suspend inline fun <reified T>` methods CANNOT be mocked by MockK. The bytecode is inlined at the call site — there's no virtual dispatch to intercept. This blocks testing of adapter layers that call these functions.

### Detection
Look for this signature pattern in HTTP client wrappers:
```kotlin
object SomeClient {
    suspend inline fun <reified T : Any> getResponse(
        url: String,
        client: HttpClient,  // ← KEY: accepts HttpClient as parameter
        ...
    ): T { ... }
}
```

### The Solution: MockEngine Injection
Don't mock the client object — mock the `HttpClient` it receives:

1. **Mock the HttpClient factory** to return a MockEngine-backed client:
```kotlin
mockkObject(ClientConfigFactory)
every { ClientConfigFactory.getClient(any()) } returns HttpClient(MockEngine) {
    engine {
        addHandler { request ->
            val path = request.url.encodedPath
            when {
                path.contains("/search") -> respond(searchJson, HttpStatusCode.OK, jsonHeaders)
                path.contains("/inventory") -> respond(inventoryJson, HttpStatusCode.OK, jsonHeaders)
                else -> respond("{}", HttpStatusCode.OK, jsonHeaders)
            }
        }
    }
    install(ContentNegotiation) { jackson { jsonMapper } }
}
```

2. **Mock config** so URLs route to MockEngine:
```kotlin
mockkObject(ConfigProps)
every { ConfigProps.configProp } returns ConfigPropDto(
    cromaClientUrl = "https://mock.test",
    ...
)
```

3. **The inline reified functions execute normally** — they just hit MockEngine instead of real HTTP endpoints. No MockK interception needed.

### Key Gotchas
- **Use existing MockEngine helpers** if the project has them (e.g., `HttpClientEngine.getClientEngine()`) — don't create custom ones that leak state
- **Top-level `val` HttpClients** (e.g., in `ClientDI.kt`) are initialized from the factory. Mock the factory BEFORE these vals load.
- **JUnit 5 return type**: `fun test() = runBlocking { assertNotNull(x) }` silently fails if `assertNotNull` returns non-Unit. Use `: Unit = runBlocking { ... Unit }`
- **Redis/cache mocking**: Mock cache to return "miss" so the adapter actually calls the HTTP client

### Coverage Impact
- assembler-service adapter/v4/impl: 2% → 43.5% LINE coverage with just 6 tests
- This pattern works for ANY Kotlin object with inline reified functions that accept HttpClient

---

## 23. Assembler-service deep engagement learnings (Kotlin/Ktor, 15K+ lines)

### Coverage progression: 36.3% → 55.5% over 7 waves
- **Wave 1 (CASCADE):** Services first → 43.2% (+6.9%). Highest ROI from service-level tests.
- **Wave 2-4 (MAPPERS):** Mapper v1/v2/v3 → 46.5%. Deep mapper logic requires precise DTO knowledge.
- **Wave 5-6 (DEEP):** Complex functions + all mappers → 54.4%. 429 new tests in parallel push.
- **Wave 7 (ADAPTER):** CromaAdapterDeepTest → 55.5%. Adapter validation code = easy coverage gains.

### Key patterns discovered
- **Suspend inline reified = testable via MockEngine**: `CromaClient` methods are `suspend inline fun <reified T>`. MockK cannot mock them directly, BUT they accept an `HttpClient` parameter. By injecting a MockEngine-backed HttpClient, the inline functions execute normally against fake endpoints. This bypasses the MockK limitation entirely.
- **MockEngine adapter testing pattern**: Mock `ClientConfigFactory.getClient()` to return a MockEngine client. All top-level HttpClient vals in `ClientDI.kt` are initialized from this factory, so they automatically get the MockEngine client. The inline reified functions in CromaClient execute their real code — they just hit MockEngine instead of real HTTP.
- **JUnit 5 silently drops non-Unit test methods**: `fun test() = runBlocking { assertNotNull(x) }` — if `assertNotNull` returns a non-Unit value, JUnit 5 doesn't see it as a valid test method. Fix: use `fun test(): Unit = runBlocking { ... }` with a trailing `Unit` statement.
- **Adapter try/catch pattern**: Wrap adapter calls in try/catch to cover validation code before the CromaClient call.
- **ConfigProps mockkObject pattern**: `mockkObject(ConfigProps); every { configProp } returns ConfigPropDto()` in @BeforeEach. Required by almost every class.
- **Import ambiguity**: Must use `import org.junit.jupiter.api.Test` NOT wildcard imports — ambiguity with `kotlin.test.Test`.
- **Coverage ceiling lifted**: Previous estimate of 85-88% ceiling was based on inline reified being untestable. With MockEngine approach, adapter/v4/impl went from 2% → 43.5% LINE coverage. Real ceiling is now much higher.

### Speed observations
- Parallel agents got stuck after ~10-15 tool calls on complex mapper methods
- DTO re-reading across waves wasted significant time (fixed by DTO Registry in v2)
- Static priority order missed high-value targets (fixed by Journey-Weighted Prioritization in v2)

---

## 24. Lambda/inner class coverage strategy

### The Problem
In Kotlin coroutine-heavy codebases, **42% of missed lines** can be inside lambda/inner classes (`$methodName$2`). These are coroutine blocks (`withContext`, `coroutineScope`, `async {}`) that only execute when HTTP calls succeed. Simple try/catch adapter tests cover the method entry (3-5 lines) but NOT the lambda body (15-30 lines each).

### Detection
JaCoCo reports lambda classes as `ClassName$methodName$N` where N is the lambda index. Look for patterns like:
```
CromaAdapterImpl$getCart$2  → missed: 25 lines
CromaAdapterImpl$placeOrder$1  → missed: 18 lines
```

### Two-phase testing approach
- **Phase A (shallow):** Write try/catch tests that cover method entry, validation, and error paths. Quick wins, 3-5 lines per test.
- **Phase B (deep):** Write MockEngine tests that return proper HTTP responses, triggering the coroutine lambda to execute. 15-30 lines per test but requires proper response bodies.

### Priority rule
Always complete Phase A for ALL methods before starting Phase B. Phase A gives 80% of methods covered. Phase B gives 80% of remaining lines.

---

## 25. ROI-based test prioritization

### Scoring formula
`ROI = lines_coverable / test_complexity`

| Test Type | Lines/Test | Complexity | ROI Score |
|-----------|-----------|------------|-----------|
| NotImplemented assertThrows | 1-2 | 1 | 10 |
| Mapper pure logic | 10-20 | 2 | 8 |
| Processor when-branch | 6-8 | 2 | 7 |
| Service mock delegate | 5-10 | 3 | 5 |
| Adapter try/catch | 3-5 | 2 | 3 |
| MockEngine deep | 15-30 | 8 | 4 |

### Generation order
1. NotImplemented methods (coverage gold — clear entire interfaces)
2. Mapper/transformer pure functions (highest lines per test)
3. Processor logic branches (when/if combinations)
4. Service delegates with mocked deps
5. Adapter try/catch (method entry coverage)
6. MockEngine deep tests (lambda body coverage)

---

## 26. @Serializable DTO construction workaround

### The Problem
Kotlin `@Serializable` data classes generate synthetic constructors with `seen0: Int` and `serializationConstructorMarker` parameters. Direct construction fails with cryptic compiler errors:
```
None of the following candidates is applicable:
  constructor(seen0: Int, ..., serializationConstructorMarker: SerializationConstructorMarker?)
```

### Detection
Look for `@Serializable` annotation on data classes during static analysis. The static analyzer now flags these automatically.

### Solution
Use `kotlinx.serialization.json.Json.decodeFromString` instead of direct construction:
```kotlin
import kotlinx.serialization.json.Json

val dto = Json.decodeFromString<CartModificationRequest>("""
    {"category": "test", "pinCode": "110001", "productCode": "SKU001"}
""")
```

### Important notes
- Not ALL `@Serializable` DTOs have this issue — only those where ALL constructor params have defaults or where the compiler generates the synthetic constructor as the only public one.
- The DTO registry now tracks `is_serializable` and `construction_strategy` to auto-select the right approach.

---

## 27. DTO namespace disambiguation

### The Problem
Enterprise codebases with API versioning (v1/v2/v3/v4) often have the SAME DTO class name in multiple packages:

| DTO Name | v1 Package | v2 Package | v3 Package |
|----------|-----------|-----------|-----------|
| OrderConfirmationRequest | model.dto.OrderDto | model.dto.v2.OrderDto | — |
| RemoveProductDto | model.dto | model.dto.v3 | — |
| CartModificationRequest | model.dto | model.dto.v3 | — |
| ProceedToPaymentRequestDto | model.dto | model.dto.v3 | — |
| OmniInStoreSearchRequest | model.dto.omni | model.dto.v2.omni | — |

### Solution
Use import aliases in test files:
```kotlin
import com.example.model.dto.OrderDto.OrderConfirmationRequest
import com.example.model.dto.v2.OrderDto.OrderConfirmationRequest as V2OrderConfirmationRequest
```

### Auto-detection
The DTO registry now detects namespace collisions via `registry.get_collisions()` and generates alias suggestions. Test generators should use `registry.get_qualified(name, package_hint)` to resolve the correct version.

---

## 28. Branch coverage pair generation

### The Problem
Branch coverage (if/when/?.let/?./!!) is much harder than line coverage. A project at 65% line coverage may be at only 35% branch coverage. Each conditional needs BOTH paths tested.

### Strategy
For each conditional, generate paired tests:

```kotlin
// Null path
@Test fun `handles null items`() {
    val response = mapper.transform(CartDto(items = null))
    assertEquals(emptyList<Item>(), response.items)
}

// Non-null path
@Test fun `handles populated items`() {
    val response = mapper.transform(CartDto(items = listOf(item1, item2)))
    assertEquals(2, response.items.size)
}
```

### Common branch patterns in Kotlin
- `?.let { }` → test with null AND non-null receiver
- `when(value) { }` → test every branch + else
- `if (list.isNullOrEmpty())` → test null, empty, non-empty
- `try { } catch { }` → test success AND exception paths
- `?.` safe calls → test null AND non-null

### Prioritization
Focus on branches in:
1. Mapper methods (high branch density)
2. Service validation logic
3. Adapter conditional flows (cache hit/miss, feature flags)

---

## 29. Compilation batching strategy

### The Problem
Running full test+coverage suite after every small change wastes time. Kotlin incremental compilation takes ~8s, but full test+JaCoCo takes ~100s+.

### Strategy
1. Write 50-100 tests in a batch
2. Run `compileTestKotlin` only (8-10s) — fix ALL compile errors
3. Only after clean compilation, run full `test jacocoTestReport`
4. If tests fail, fix in batches, not individually
5. Never run full suite more than once per iteration

### Forge Core implementation
- `max_compile_retries = 3` per batch
- `compile_only_command` should be used during iteration
- Full suite only at phase boundaries (end of each iteration)

---

## 30. Koin dependency auto-detection

### The Problem
Koin DI setup in test files must include ALL transitive dependencies. Missing one causes runtime crash (not compile error), which is harder to debug.

### Detection pattern
Scan adapter/service source for `get<Type>()` and `inject<Type>()` calls:
```kotlin
private val adapterV1: CromaAdapterImpl by inject()
private val adapterV3: CromaAdapterImplV3 by inject()
private val ldClient: LaunchDarklyClient by inject()
```

### Version-specific Koin dependency map (assembler-service example)
| Adapter | Required Koin Bindings |
|---------|----------------------|
| V1 | CromaAdapterImpl only |
| V2 | CromaAdapterImpl, CromaAdapterImplV3, LaunchDarklyClient, CromaAdapterImplV2 |
| V3 | CromaAdapterImpl, CromaAdapterImplV2, LaunchDarklyClient, CromaAdapterImplV3 |
| V4 | CromaAdapterImpl only |

### Auto-generation
The static analyzer now extracts `koin_dependencies` from source files. Test generators use this to build correct `startKoin { modules(...) }` blocks.
