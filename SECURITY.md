# Security Policy

## Supported Version

| Version | Supported |
|---|---|
| 1.x | ✅ |

## Security Boundaries

Forge Core is designed to operate as a **sandboxed, prompt-driven backend test agent**.

### Security guarantees
- It is intended to work only on **test code, test fixtures, test resources, and test-only configuration**.
- It must **not modify production/source code**.
- It must **not store credentials or secrets**.
- It must **not depend on external API access** to function.
- Its long-term memory (`LEARNINGS.md`) must contain only generalized, secret-free learnings.

## Data Handling Rules

### Allowed in `LEARNINGS.md`
- generalized failure patterns,
- framework-specific testing guidance,
- coverage-tool workarounds,
- fixture and mocking techniques,
- safe build/test observations.

### Prohibited in `LEARNINGS.md`
- secrets,
- tokens,
- credentials,
- private keys,
- copied proprietary source code,
- personal data,
- internal-only operational details that should not be shared across projects.

## External Access

Forge Core should be configured to run without requiring external API access.
If a host environment provides network access, the agent should still avoid using it unless explicitly approved and required for repository-owned tooling.

## Credential Storage

No credentials should be committed to this repository.
No credentials should be written into prompt files, issue forms, setup scripts, knowledge packs, or learnings.

## Responsible Use

When contributing prompts or learnings:
- sanitize all examples,
- generalize stack learnings,
- avoid pasting customer or proprietary code,
- prefer short illustrative snippets over real source excerpts.

## Reporting a Vulnerability

If you discover a security issue in Forge Core:
1. **Do not** open a public issue containing sensitive details.
2. Report it privately through your organization’s secure disclosure channel or GitHub private security advisory process.
3. Include:
   - impact summary,
   - affected files/components,
   - reproduction steps,
   - proposed mitigation if known.
