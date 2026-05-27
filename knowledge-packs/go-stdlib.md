# Knowledge Pack — Go

Use this pack for Go backends using the standard `testing` package, optionally with `testify` and `gomock`.

---

## 1. Table-driven tests
This is the default pattern for branch-heavy logic.

Example:
```go
func TestNormalizeStatus(t *testing.T) {
    cases := []struct {
        name  string
        input string
        want  string
    }{
        {name: "trimmed", input: " ok ", want: "OK"},
        {name: "empty", input: "", want: "UNKNOWN"},
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

---

## 2. `httptest.NewServer` and request testing
Use `httptest` for handler-level tests.

Common patterns:
- `httptest.NewRecorder()` for direct handler invocation,
- `httptest.NewServer()` for higher-level HTTP flows,
- avoid real network dependencies beyond the local test server.

---

## 3. Testify assertions and suites
If the project already uses Testify, match it.

Useful pieces:
- `assert`
- `require`
- `mock`
- suites only if already established in the repo

Prefer plain `testing` + table-driven tests unless the suite pattern is already standard.

---

## 4. Interface mocking with gomock
Go is easiest to test when dependencies are interfaces.

Use `gomock` when:
- the project already uses it,
- interaction verification matters,
- handwritten fakes would be noisy.

Prefer small repository/client interfaces over mocking concrete types.

---

## 5. `t.Parallel()`
Use `t.Parallel()` only when tests are truly isolated.

Do **not** use it when tests share:
- environment variables,
- filesystem paths,
- global singletons,
- mutable package-level state,
- shared DB fixtures.

---

## 6. `TestMain` for setup/teardown
Use `TestMain` for package-wide setup only when necessary.

Good uses:
- initializing shared test infrastructure,
- seeding deterministic config,
- cleaning shared resources.

Keep it small; most setup should stay inside fixtures/helpers local to the test package.

---

## 7. Build tags for integration tests
If the project separates integration tests with build tags, keep unit tests independent from them.

Do not accidentally move integration-only behavior into the fast unit-test path.

---

## 8. Coverage basics
Typical commands:
```bash
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out
go tool cover -html=coverage.out -o coverage.html
```

For targeted mode, focus coverage analysis on the package containing the target files.

---

## 9. High-value target order
1. pure service/use-case functions,
2. HTTP handlers,
3. mappers/parsers/validators,
4. repository abstractions with fakes/mocks,
5. concurrency logic only when it can be tested deterministically.

---

## 10. Common anti-patterns
- relying on real time without control,
- unguarded `t.Parallel()` on shared state,
- testing concrete infra instead of interface seams,
- hiding assertions inside helpers so failures become opaque.
