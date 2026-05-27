# Knowledge Pack — Node.js / Express

Use this pack for JavaScript or TypeScript backends built with Express or similar HTTP middleware stacks.

---

## 1. Recommended stack
- **Runner:** Jest or Vitest (follow project convention)
- **HTTP tests:** Supertest
- **Mocking:** `jest.mock`, `jest.spyOn`, `vi.mock`, manual fakes
- **Coverage:** project script → c8 → nyc/istanbul → built-in runner coverage

---

## 2. Supertest patterns
Use Supertest for route and middleware testing without real network I/O.

Example:
```ts
import request from "supertest";
import { app } from "../src/app";

it("returns 200 for health", async () => {
  const response = await request(app).get("/health");
  expect(response.status).toBe(200);
});
```

Good use cases:
- route status/body assertions,
- validation behavior,
- auth middleware branches,
- error mapping.

---

## 3. Jest mocking patterns
Use:
- `jest.mock()` for full module mocks,
- `jest.spyOn()` for selective override,
- `mockResolvedValue` / `mockRejectedValue` for async functions,
- `jest.restoreAllMocks()` or `jest.resetAllMocks()` after each test.

Typical rule:
- mock at the service/client seam,
- avoid mocking internal pure helpers unless necessary.

---

## 4. Database mocking
### Sequelize
Mock repository/model methods at the module boundary.

### Mongoose
Mock model static methods and query chains carefully, or isolate service logic above the ORM layer.

### Better approach when possible
Test service logic against a repository abstraction rather than mocking every chained ORM call.

---

## 5. Middleware testing
Common targets:
- auth middleware,
- validation middleware,
- error middleware,
- request-context propagation.

Check:
- `next()` invocation,
- response short-circuiting,
- status/body on failures,
- request decoration side effects.

---

## 6. Environment variable handling
Node apps often read config at module load.

Safe test pattern:
- save original env,
- set required vars in `beforeEach`,
- reset modules if config is cached on import,
- restore env in `afterEach`.

Example:
```ts
const OLD_ENV = process.env;

beforeEach(() => {
  jest.resetModules();
  process.env = { ...OLD_ENV, FEATURE_FLAG: "true" };
});

afterEach(() => {
  process.env = OLD_ENV;
  jest.restoreAllMocks();
});
```

---

## 7. Async error handling
Always test:
- resolved path,
- rejected dependency path,
- Express async error propagation,
- fallback behavior.

Use `await expect(promise).rejects.toThrow(...)` for service logic and Supertest assertions for HTTP behavior.

---

## 8. High-value target order
1. services/use-cases,
2. controllers/routes,
3. middleware,
4. validators/mappers,
5. client wrappers.

Lower value:
- bootstrap-only files,
- generated types,
- simple constant modules.

---

## 9. Common anti-patterns
- not resetting mocks/modules between tests,
- patching the wrong import path,
- using real timers for time-sensitive logic,
- deep-mocking ORM chains instead of isolating a repository boundary,
- allowing env vars to leak across tests.
