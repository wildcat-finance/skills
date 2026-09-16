Brevitas evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

## Frontier

- Current version: `brevitas-v0.4.0`
- Frontier status: `open`
- Frontier revision: `held-engineering-corpus`
- Current frontier: The linter has not been forward-tested across a held cross-model corpus of engineering reviews, and preservation of counterexamples and reproduction steps remains agent-checked.
- Next Fiat job: `Forward-test Brevitas across held x-ray, Solidity-auditor, gas, invariant and diff-review outputs, then add every confirmed structural bypass to the corpus without weakening evidence precedence. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.`
- Sources: [../../../../SOURCES.md](../../../../SOURCES.md)

## Held-corpus interface decision

Accepted, 2026-08-27. Brevitas will use a closed `evals/corpus.json`
manifest, digest-bound case files and a deterministic offline runner. A
qualifying case records its engineering family, provider and full returned
model identity, capture client version, source, prompt and output digests,
pre-lint classification, expected result and exact protected evidence spans.
The runner validates those records before comparing them with the linter.

A manual sweep was rejected because it would not preserve provenance,
classification or negative evidence. Live model calls in CI were rejected
because secrets, cost, network availability, provider drift and
nondeterministic responses would make the acceptance path irreproducible. A
model judge was rejected because it would make nondeterministic model output
the authority for evidence retention; a parser rewrite was rejected because
it expands this held-corpus job and may add a dependency without evidence that
the current line parser is the cause. This record establishes the design only.
It does not claim held-corpus or cross-model coverage and changes no frontier
field or history row.

## History

- `brevitas-v0.1.0` | baseline | `held-engineering-corpus` | `dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62` | [README marketplace-context](../../README.md) | Versioning starts with the executable linter and three audit-derived corpus cases.
- `brevitas-v0.2.0` | generation | `held-engineering-corpus` | `dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62` | Maintainer report: the per-point fence rule fired only on reference documents and the fence cap flagged command lists a reader is meant to copy whole | The one-fence-per-point rule is removed and the fence cap widens from 15 to 40 content lines. In one day of running the linter across this repository the per-point rule produced eight findings, none of which survived review, and obeying one duplicated ten headings. The cap keeps catching pasted dumps, including the 116-line tree it found. Frontier unchanged.
- `brevitas-v0.3.0` | generation | `held-engineering-corpus` | `dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62` | Issue #372 focused boundary, precedence, casing, duplicate, near-miss and B030 tests | Protect exact boundary-delimited bare 64-hex digests, `0x` plus 8-hex selectors, full 40-hex Git object ids, and 7-to-39-hex Git abbreviations only in Markdown code, explicit-label or `owner/repository@oid` contexts. A broad hexadecimal regex was rejected because it captures ordinary hex-like prose; Git subprocess resolution was rejected because it makes an offline text check repository-dependent. This establishes literal survival only, not validity or existence. Frontier unchanged.
- `brevitas-v0.4.0` | generation | `held-engineering-corpus` | `dcff4f6b1397570468dedb18a1ebaa5f45377272bcd2f71cd69ad6818eeb0b62` | [skills#453](https://github.com/wildcat-finance/skills/issues/453), [known-failure study](../../../../docs/known-failure-inoculation-study.md), and [runbook](../../../hexaemeron/docs/known-failure-inoculation/runbook.md) | Add explicit `fiat-audit-record` mode for a canonical Fiat audit ledger after its synopsis check. The mode retains report behaviour and every applicable rule while suppressing only B010 and B011 for Fiat-owned heading and table cardinalities; it does not parse or establish Fiat schema authority. The `held-engineering-corpus` frontier, digest, status, current frontier and Next Fiat job remain byte-identical.
