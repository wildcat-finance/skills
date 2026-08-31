# Homologia evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `homologia-v1.1.0`
- Frontier status: `open`
- Frontier revision: `mirror-execution`
- Current frontier: Homologia admits one closed, cap-bounded manifest and its declared vectors into a deterministic checked-inputs record with source digests and closed expected-answer provenance. It executes no mirror and produces no verdict, so nothing yet establishes that a pair agrees.
- Next Fiat job: Execute one pinned mirror over checked vectors through the adapter protocol without judging its answers. Accepted when argv is pinned, no shell or output path enters the child, JSONL input and integer-only output are bounded, timeout and count or order failures refuse atomically, and the reference adapter records a repeatable runtime identity and answer digest.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `homologia-v0.1.0` | baseline | `first-parity-verdict` | `31adad2e425c951aba077fed750b889b03f0608ba52cde8fdde8afd6ab8b4729` | [the study](../../docs/homologia-study.md), [skills#458](https://github.com/wildcat-finance/skills/issues/458) | Versioning starts here. Homologia ships as a scaffold: both host manifests, the portable route, marketplace entries, the canonical contract with its three promises, this ledger, the committed study and runbook, ADR-001 and a help-only command. It consolidates three proposals from the collective's poll of 2026-08-22, Isopsephia, Homologia and Akribeia, which each named the same missing transition from a different seat. The held frontier is the first parity verdict, and nothing here compares anything yet. |
| `homologia-v1.1.0` | evolution | `mirror-execution` | `a6b4d86919fe9cd9c8d45d31541854aa51e23622ea7b39a2648febdccaaba391` | [checked-input study](../../docs/checked-inputs/study.md), [schema compatibility](../../docs/schema-compatibility.md), [ADR-002](../../docs/decisions/ADR-002-chain-answers-are-evidence.md), [focused guards](../../tests/test_check.py), [committed checked record](../../examples/wad-interest-v0/checked-inputs.json), [skills#458](https://github.com/wildcat-finance/skills/issues/458) | The first held job completes. `check` now admits one closed manifest and its declared JSONL vectors through fixed file, aggregate, set and vector caps; preserves proved, recorded and asserted expected-answer forms; binds source digests into canonical output; and refuses unsafe paths, scale or tolerance drift and incomplete provenance before an atomic write. Mirror execution becomes the held frontier. |
