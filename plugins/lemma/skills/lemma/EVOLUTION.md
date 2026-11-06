# Lemma evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `lemma-v0.5.1`
- Frontier status: `open`
- Frontier revision: `abi-return-and-mutability`
- Current frontier: Callable-surface ABI validation does not independently check return types or state mutability.
- Next Fiat job: Make callable-surface ABI validation cover return types and state mutability as well as names and input types, with any divergence rejecting the output. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.
- Sources: [../../../../SOURCES.md](../../../../SOURCES.md)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `lemma-v0.1.0` | baseline | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `lemma-v0.1.1` | epoch | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [ADR-013](../../../../docs/decisions/ADR-013-make-lemma-the-canonical-skill-name.md) | Correct the mistaken `chunk` identity to `lemma` across discovery and invocation without changing the held frontier. |
| `lemma-v0.2.1` | generation | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [SKILL.md Promise Machine contract](SKILL.md) | Chunk corpora carry a provenance record beside the chunks and print the capture-dataset flags that match it, under a new `lemma-corpus-provenance` promise. The held frontier is untouched. |
| `lemma-v0.3.1` | generation | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [Event agreement study](../../../../docs/lemma-event-agreement/study.md) | Select compiler-membership: resolve usedEvents IDs across all AST sources and compare event descriptor multisets before chunking. An inheritance-only walk misses qualified library and interface events. Step 1 covers elementary wire types and names unsupported shapes. Step 2 adds arrays, nested struct tuples, contract addresses, enums, user-defined value types and external function types, and refuses missing, malformed, cyclic or excessive wire shapes before delivery. The held return/mutability frontier is unchanged. |
| `lemma-v0.4.1` | generation | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [Pinned compiler membership study](../../../../docs/lemma-compiler-membership/study.md) | Select pinned-inheritance for the exact 0.8.10 fc410830 and 0.8.19 7dd6d404 builds when usedEvents is absent. Retain the first AST declaration per external signature in compiler linearization order, with aggregate traversal bounds. Strict usedEvents-only validation was rejected because it refuses both healthy pinned builds. Universal inheritance fallback was rejected because modern ABIs include qualified library events. Present malformed membership still refuses, and descriptor fields remain independently compared. The held return/mutability frontier is unchanged. |
| `lemma-v0.5.1` | generation | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [Remaining venue study](../../../../docs/kickoff/1366/remaining-study.md) | Select prepared-events: exact compiler admission, distinct event quotations and explicit digest-bound input preparation. Step 1 admits six more observed legacy builds under the existing AST membership rule; later steps own quotation handling, preparation and full corpus conformance. Current-pins refuses healthy legacy builds. Exact-pins alone leaves valid quotation and captured-input failures unresolved. Neither alternative meets the whole study. The held return/mutability frontier is unchanged. |
