# Lemma evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `lemma-v0.2.1`
- Frontier status: `open`
- Frontier revision: `abi-return-and-mutability`
- Current frontier: Callable-surface ABI validation does not independently check return types or state mutability.
- Next Fiat job: Make callable-surface ABI validation cover return types and state mutability as well as names and input types, with any divergence rejecting the output. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `lemma-v0.1.0` | baseline | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `lemma-v0.1.1` | epoch | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [ADR-013](../../../../docs/decisions/ADR-013-make-lemma-the-canonical-skill-name.md) | Correct the mistaken `chunk` identity to `lemma` across discovery and invocation without changing the held frontier. |
| `lemma-v0.2.1` | generation | `abi-return-and-mutability` | `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c` | [SKILL.md Promise Machine contract](SKILL.md) | Chunk corpora carry a provenance record beside the chunks and print the capture-dataset flags that match it, under a new `lemma-corpus-provenance` promise. The held frontier is untouched. |
