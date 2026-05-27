# Knowledge Pack — Java / Spring Boot

Use this pack when the backend is Java-based and built with Spring Boot or Spring Framework.

---

## 1. Recommended testing layers
Choose the lightest test that proves the behavior.

| Goal | Preferred Tool |
|---|---|
| Pure service logic | JUnit + Mockito |
| MVC/controller behavior | `@WebMvcTest` + `MockMvc` |
| JPA repository slice | `@DataJpaTest` |
| Full application wiring | `@SpringBootTest` |

Default to slice or pure unit tests before full-context tests.

---

## 2. `@SpringBootTest`
Use when you need:
- full application wiring,
- multiple real Spring-managed collaborators,
- complex configuration/property interactions.

Cautions:
- slower,
- more context leakage risk,
- harder to keep deterministic if overused.

---

## 3. `@WebMvcTest`
Use for controller-layer tests when you want:
- request mapping,
- validation,
- serialization,
- auth filter behavior (where relevant),
- response status/body assertions.

Mock downstream service beans with `@MockBean`.

Example:
```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean OrderService orderService;
}
```

---

## 4. `@DataJpaTest`
Use for repository behavior, query methods, and JPA mapping checks.

Good for:
- entity mapping,
- JPQL/native query verification,
- transactional repository behavior.

Pair with H2 or TestContainers depending on project realism needs.

---

## 5. `MockMvc` patterns
Common assertions:
- HTTP status,
- JSON body,
- validation errors,
- content type,
- headers,
- security failure branches.

Example:
```java
mockMvc.perform(get("/orders/123"))
    .andExpect(status().isOk())
    .andExpect(jsonPath("$.id").value("123"));
```

---

## 6. `@MockBean` vs `@Mock`
Use:
- `@Mock` for plain unit tests outside Spring context,
- `@MockBean` when replacing a bean inside a Spring test context.

Do not mix them casually; choose based on whether Spring is managing the object graph.

---

## 7. TestContainers for database realism
Use TestContainers when repository logic depends on real database behavior that H2 cannot reproduce safely.

Best use cases:
- PostgreSQL-specific SQL,
- migrations,
- indexing/constraint behavior,
- dialect-specific quirks.

Do not default to containers for simple unit/service tests.

---

## 8. ApplicationContext caching
Spring caches contexts between compatible tests.

Implications:
- good for performance,
- dangerous if tests mutate static/global state,
- use `@DirtiesContext` only when isolation truly requires it.

Prefer resetting mutable collaborators instead of blowing away context caches.

---

## 9. Profile-based config
Use test profiles to isolate configuration:
- `@ActiveProfiles("test")`
- test-specific properties files
- property overrides for endpoints, feature flags, DB settings

Keep secrets and real endpoints out of tests.

---

## 10. Security test utilities
For Spring Security, test:
- authenticated vs unauthenticated,
- role/authority branches,
- forbidden vs not found vs bad request behavior.

Useful patterns:
- `@WithMockUser`
- security request post-processors
- verifying filter behavior in `MockMvc` tests

---

## 11. Service-layer pure unit tests
For most business logic, prefer plain JUnit + Mockito over full Spring context.

Typical template:
```java
@ExtendWith(MockitoExtension.class)
class InvoiceServiceTest {
    @Mock InvoiceRepository repository;
    @InjectMocks InvoiceService service;
}
```

This gives faster, more stable coverage gains.

---

## 12. High-value target order
1. service/use-case classes,
2. controllers with `MockMvc`,
3. mappers/validators,
4. repository slices where queries matter,
5. security branches.

Lower value:
- application bootstrap,
- Lombok-only DTOs,
- auto-generated code.
