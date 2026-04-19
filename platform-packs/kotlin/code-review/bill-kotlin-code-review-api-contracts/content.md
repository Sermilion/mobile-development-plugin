## Focus
- Request validation and boundary enforcement
- Serialization/deserialization mismatches
- Backward compatibility of request/response schemas
- Status-code and error-contract correctness
- Pagination, filtering, and idempotency semantics on public endpoints

## Ignore
- Pure style feedback
- Internal refactors that do not change externally observable behavior

## Applicability

Use this specialist for backend/server Kotlin code routed through the built-in Kotlin pack. It is most relevant for Ktor, Spring, Micronaut, Quarkus, http4k, Javalin, gRPC, or similar transport layers.

## Project-Specific Rules

- Validate untrusted input at the boundary before business logic depends on it
- Distinguish absent vs null vs defaulted fields when that changes semantics
- Do not leak internal/domain/persistence models directly as public API contracts unless that coupling is an explicit, stable decision
- Breaking contract changes require explicit versioning, coordinated migration, or a compatibility story
- Error mapping should be stable, intentional, and not collapse distinct client outcomes into the same generic failure
- Mutating endpoints, commands, and webhook handlers should define idempotency behavior clearly when retries are plausible
- Pagination and filtering should preserve deterministic ordering and bounded result sizes
- Serialization defaults must match the compatibility expectations of existing clients

## Output Rules
- Report at most 7 findings.
- Include client-visible consequence for each finding.
- Include `file:line` evidence for each finding.
- Severity: `Blocker | Major | Minor`
- Confidence: `High | Medium | Low`
- Include a minimal, concrete fix.

## Output Format

Every finding must use this exact bullet format for downstream tooling:

```text
- [F-001] <Severity> | <Confidence> | <file:line> | <description>
```

Do NOT use markdown tables, numbered lists, or any other format for findings.
