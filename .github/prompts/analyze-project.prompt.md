---
mode: agent
description: "Perform deep backend architecture analysis covering HLD, LLD, request/data flows, integrations, security model, and unit-test seams"
tools: ["bash", "glob", "grep", "view"]
---

# Analyze Project

Perform a deep architecture and testability analysis for the backend scope.

## Step 1 — Repository reconnaissance
- map the directory tree to depth 2–3,
- identify backend modules,
- read build files and dependency manifests,
- inspect README/docs/ADR files,
- locate entry points, startup hooks, and environment/config sources,
- note CI commands for build/test/coverage.

## Step 2 — High-Level Design (HLD)
Document the following.

| Area | What to capture |
|---|---|
| System Purpose | What the backend does and who consumes it |
| Module Map | Each backend module/package and its responsibility |
| Architecture Style | Layered, hexagonal, clean architecture, MVC, event-driven, etc. |
| External Integrations | DB, cache, queue, SMTP, storage, third-party APIs, ML services |
| Communication Model | REST, gRPC, GraphQL, workers, consumers, cron, webhooks |
| Security Model | Authentication, authorization, token handling, roles, middleware |
| Operational Risks | Startup side effects, shared state, heavy initialization |

## Step 3 — Low-Level Design (LLD)
For each relevant module/package/class, identify:
- responsibilities,
- public endpoints/APIs,
- service/use-case methods,
- repositories/clients/adapters,
- DTOs/entities/schemas,
- validation logic,
- error handling patterns,
- dependency injection or service construction,
- boundaries where unit tests should mock dependencies.

## Step 4 — Flow analysis
Trace the main flows.

### Required flow categories
1. **Request lifecycle**
   - request entry,
   - middleware/filters,
   - validation,
   - handler/controller,
   - service/use case,
   - repository/client,
   - response mapping.

2. **Business logic flows**
   - happy path,
   - error path,
   - fallback path,
   - retry path,
   - edge-case branches.

3. **Data transformation flows**
   - input DTO → domain → persistence → response DTO.

4. **Async/event flows**
   - queues,
   - scheduled jobs,
   - background workers,
   - pub/sub,
   - consumer handlers.

## Step 5 — Security model review
Identify:
- auth entry points,
- middleware/filters,
- session vs token vs API key,
- role/policy enforcement,
- user-context propagation,
- security-sensitive branches worth testing.

## Step 5.5 — Dependency graph preparation
Prepare data for Phase 2.5 dependency graph analysis:
- identify the main call chains from entry points through service → adapter → client → mapper → util layers,
- note which functions call the most downstream functions,
- flag methods with high "cascade depth" — these are prime candidates for cascade coverage,
- identify shared utility functions called from many places (hub nodes).

This data feeds into the dependency-graph prompt for full cascade coverage analysis.

## Step 6 — Testability map
Classify backend files by unit-test suitability.

| Category | Definition |
|---|---|
| Easy wins | Pure logic, stateless services, mappers, utils |
| Moderate | Services with mockable repositories/clients |
| Heavy mocking | Handlers/controllers with framework setup |
| Integration-prone | DB-heavy repositories, infra bootstraps, messaging consumers |
| Excluded | Generated code, constants, bootstrap, pure DTOs with no behavior |

## Step 7 — Targeted mode rules
If the user requested specific classes/files:
- read those files completely,
- trace direct dependencies and imports,
- explain what must be mocked,
- scope all later analysis and coverage decisions to those targets.

## Step 8 — Required output
Produce:

```markdown
## Architecture & Testability Report

### HLD
- Purpose:
- Architecture style:
- Modules:
- Integrations:
- Security model:

### LLD
| Module/Package | Key Types | Responsibility | Test Seam |
|---|---|---|---|

### Flows
1. ...
2. ...

### Testability Priorities
1. ...
2. ...

### Risks for Unit Testing
- import-time side effects
- global state
- heavy framework bootstrap
```

Focus on information that directly improves later testing decisions.
