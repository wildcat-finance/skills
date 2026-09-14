# HOMOLOGIA

<!-- marketplace-context:start -->
## In one line

Homologia admits one pinned pair and its evidence-classed expected integers into deterministic checked inputs; it does not yet run the mirror or compare answers.

**Current frontier.** `check` admits one closed, cap-bounded manifest and its declared vectors into a deterministic checked-inputs record. It executes no mirror and produces no verdict, so nothing yet establishes that a pair agrees.

**Next Fiat job.** Use /hexaemeron:fiat to execute one pinned mirror over checked vectors through the adapter protocol, without judging its answers. The child boundary must use fixed argv with no shell, a minimal environment, bounded JSONL input and integer-only output, a timeout, atomic refusal and a recorded runtime identity and answer digest. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## START HERE

Homologia is the planned home for checking whether one pinned contract
calculation and one pinned off-chain mirror return the same integers over a
declared vector set. The contract correctly distinguishes agreement from
correctness: two implementations of the same mistake can agree perfectly.

That comparison does **not** run today. The plugin checks one closed manifest,
its pair identity, scales, declared vector files, canonical integers,
tolerances, paths, caps and expected-answer provenance. It writes one canonical
checked-inputs record with source digests. Mirror execution, comparison,
divergence specimens and verdicts still refuse rather than inventing a result.

## CHECK INPUTS

From the repository root:

```bash
python3 plugins/homologia/scripts/homologia.py check \
  --manifest plugins/homologia/examples/wad-interest-v0/manifest.json \
  --out build/homologia/checked-inputs.json
```

Success writes no standard output. A one-line JSON summary on standard error
names the manifest and output digests plus the vector-set and vector counts.
The checked record is not a verdict and says nothing about correctness or
agreement.

## INTENDED BOUNDARY

A protocol's arithmetic gets written twice. Once in Solidity, in unsigned
256-bit integers with an explicit rounding direction and a ray or wad scale.
Again off-chain, in the SDK that renders a balance or fills a signing prompt and
in the analytics job that produces a report somebody acts on, where it runs in
doubles, `BigInt`, `int` or `Decimal` with the token decimals applied by hand.

Nothing in an ordinary suite compares the two. A fuzzing campaign asks whether
the contract agrees with itself. A prose lint asks whether a signing prompt is
readable, not whether its number is right. So a mirror that is wrong by one
rounding direction, or by six orders of decimal magnitude, passes everything.

The completed design would take one pinned pair and a declared vector set whose
expected answers carry a provenance class, report whether the pair agrees
integer for integer, and preserve every divergence as a specimen. Exact
equality would be the default; any tolerance would be declared and repeated in
the verdict it weakens.

Such a verdict would say only that the pair agreed over the supplied vectors.
It would never say either side was correct.

## CONTRACTS

- [skills/homologia/SKILL.md](skills/homologia/SKILL.md), the canonical instructions.
- [skills/homologia/EVOLUTION.md](skills/homologia/EVOLUTION.md), the version and frontier ledger.
- [docs/homologia-study.md](docs/homologia-study.md) and [docs/homologia-runbook.md](docs/homologia-runbook.md), the specification this was built from.
- [docs/decisions/ADR-001-one-charter-for-numeric-agreement.md](docs/decisions/ADR-001-one-charter-for-numeric-agreement.md), why this is one member rather than three.
- [docs/decisions/ADR-002-chain-answers-are-evidence.md](docs/decisions/ADR-002-chain-answers-are-evidence.md), why the chain side arrives as evidence.
- [docs/schema-compatibility.md](docs/schema-compatibility.md), the closed version-1 shapes, caps and refusal codes.
- [examples/wad-interest-v0/checked-inputs.json](examples/wad-interest-v0/checked-inputs.json), the deterministic committed example.

## LICENCE

Apache-2.0. See [LICENSE](LICENSE).
