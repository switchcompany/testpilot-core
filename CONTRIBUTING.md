# Contributing to Forge Core

Thank you for helping improve Forge Core.

## What to contribute
We welcome contributions in four main areas:
1. **New learnings** from real project runs
2. **Prompt improvements** that make the agent safer or more effective
3. **New stack support** for backend frameworks and languages
4. **Bug reports and fixes**

---

## 1. Submit learnings from real projects
The most valuable contribution is a reusable learning discovered in practice.

### Good learning contributions
- a repeatable failure pattern,
- a framework-specific mocking rule,
- a reliable coverage-tool workaround,
- a high-ROI testing heuristic,
- a deterministic fixture pattern.

### Before submitting
- remove secrets and proprietary details,
- generalize file paths and identifiers if needed,
- keep only the reusable pattern,
- append it to `LEARNINGS.md` in the established format.

---

## 2. Improve prompts
Prompt improvements are welcome for:
- better stack detection,
- clearer analysis output,
- safer test-writing behavior,
- stronger rollback logic,
- better self-learning hygiene.

### Prompt PR checklist
- explain the problem,
- explain the proposed prompt change,
- include before/after evidence when possible,
- verify the change improves behavior on a real or representative backend project,
- update related files if the pattern spans multiple prompts.

---

## 3. Add stack support
To add or improve support for a new language/framework:
1. update `.github/prompts/detect-tech-stack.prompt.md`,
2. update `.github/prompts/generate-coverage-report.prompt.md`,
3. update `.github/prompts/write-unit-tests.prompt.md`,
4. add or expand a knowledge pack in `knowledge-packs/`,
5. seed `LEARNINGS.md` if there is a battle-tested discovery worth preserving.

Examples:
- new Python backend framework patterns,
- new .NET slice-testing guidance,
- Rust coverage-tool fallback improvements,
- Ruby or PHP backend testing support.

---

## 4. Report bugs
Please report:
- incorrect stack detection,
- unsafe prompt behavior,
- coverage rollback failures,
- flaky test generation patterns,
- bad setup/update script behavior,
- issue template or workflow problems.

When possible, include:
- language/framework/build tool,
- expected vs actual behavior,
- sanitized logs or error output,
- relevant prompt or file path,
- reproduction steps.

---

## Pull request guidelines
- Keep PRs focused.
- Prefer one logical improvement per PR.
- Update documentation that is directly affected.
- Preserve the “never modify production code” contract.
- Do not add secrets, credentials, or proprietary code.
- Validate shell scripts and any changed automation.
- If you change prompts, consider whether knowledge packs and `LEARNINGS.md` should also change.

---

## Quality standards
A strong contribution is:
- reusable,
- deterministic,
- backend-focused,
- safe for commercial use,
- clear enough that another team can apply it without extra context.

---

## PR review tips
Helpful PR descriptions include:
- problem statement,
- files changed,
- rationale,
- validation steps,
- screenshots or sample output where relevant,
- any follow-up work still needed.

Thanks for helping make Forge Core sharper, safer, and more effective.
