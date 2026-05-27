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
