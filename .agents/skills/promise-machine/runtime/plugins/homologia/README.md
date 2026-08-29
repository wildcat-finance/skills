# Homologia

<!-- marketplace-context:start -->
## In one line

Homologia compares one pinned on-chain computation with one pinned off-chain mirror over declared vectors, and preserves every divergence as a specimen.

**Current frontier.** Homologia ships its contracts, packaging and a help-only command. No manifest is checked, no mirror is executed and no verdict is produced, so nothing yet establishes that a pair agrees.

**Next Fiat job.** Use /hexaemeron:fiat to validate a declared manifest, its vector sets and their expected-answer provenance into checked, cap-bounded inputs, refusing a `proved` class with no backing reference and any cap breach before state is written. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

A protocol's arithmetic gets written twice. Once in Solidity, in unsigned
256-bit integers with an explicit rounding direction and a ray or wad scale.
Again off-chain, in the SDK that renders a balance or fills a signing prompt and
in the analytics job that produces a report somebody acts on, where it runs in
doubles, `BigInt`, `int` or `Decimal` with the token decimals applied by hand.

Nothing in an ordinary suite compares the two. A fuzzing campaign asks whether
the contract agrees with itself. A prose lint asks whether a signing prompt is
readable, not whether its number is right. So a mirror that is wrong by one
rounding direction, or by six orders of decimal magnitude, passes everything.

Homologia takes one pinned pair and a declared vector set whose expected answers
carry a provenance class, then reports whether the pair agrees integer for
integer and preserves every divergence as a specimen. Exact equality is the
default; a tolerance must be declared and is echoed in the verdict it weakens.

A verdict says the pair agreed over the vectors it was given. It never says
either side is correct, because two implementations of the same misunderstanding
agree perfectly.

## Contracts

- [skills/homologia/SKILL.md](skills/homologia/SKILL.md), the canonical instructions.
- [skills/homologia/EVOLUTION.md](skills/homologia/EVOLUTION.md), the version and frontier ledger.
- [docs/homologia-study.md](docs/homologia-study.md) and [docs/homologia-runbook.md](docs/homologia-runbook.md), the specification this was built from.
- [docs/decisions/ADR-001-one-charter-for-numeric-agreement.md](docs/decisions/ADR-001-one-charter-for-numeric-agreement.md), why this is one member rather than three.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
