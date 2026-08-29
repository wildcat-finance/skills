# ADR-001: one charter for numeric agreement, named Homologia

## Status

Accepted, 2026-08-23. Raised by [skills#458](https://github.com/wildcat-finance/skills/issues/458)
and [the study](../homologia-study.md).

## Context

Three members answered the same poll on 2026-08-22 and, from three different
seats, named one missing transition: nothing in the roster establishes that an
off-chain reimplementation of a contract's arithmetic produces the integer the
contract produces.

Kronos proposed **Isopsephia**, exact-integer parity between a pinned on-chain
computation and its Python or TypeScript reimplementations, arguing from the
ranking seat that no charter and no open issue named the JS or TSX surface at
all, so the work could never become a held job.

Fizz proposed **Homologia**, differential vectors driven through both a contract
and its off-chain reference model, arguing that Echidna and Medusa run pure EVM,
so every property it asserts is the Solidity agreeing with itself.

Phylax proposed **Akribeia**, fidelity of the off-chain numeric mirrors that
re-derive scaled balances and accrued interest for display and signing, noting
that its own lint already guarantees a signing prompt is readable while nobody
owns whether the number in it is right.

## Decision

One member, named **Homologia**.

Three charters over one subject would have produced three vocabularies for the
same verdict and three boundaries to police between them. The three proposals
differ in scope, not in subject: exact-integer parity is the default judgement,
differential vectors are how the comparison is fed, and application mirrors are
the most common thing on the off-chain side.

The name is the relation rather than either party. *Homologia* is agreement, and
agreement between two implementations is a narrower and more honest claim than
correctness of either.

## Alternatives

- **Three members, one per proposal.** Rejected: the three proposals differ in
  scope, not in subject, so this would have produced three vocabularies for the
  same verdict and three boundaries to police between them.
- **A new skill inside Hexaemeron, beside Fizz.** Rejected: Hexaemeron's skills
  are phases of a delivery loop, and this one answers a question about a
  protocol rather than about a run.
- **The name Isopsephia.** Rejected: it names only the exact-integer case, and
  a declared tolerance is a real, if weakening, mode.
- **The name Akribeia.** Rejected: it names a virtue of one side. The subject is
  the relation between two implementations, not the precision of the mirror.

## Consequences

- Exact integer equality is the default and a tolerance must be declared, so the
  Isopsephia discipline survives as behaviour rather than as a name.
- Vector generation stays outside the charter, with Fizz and Foundry, so this
  member consumes declared files and never mutates or minimises them.
- The failure classes Phylax named, decimals, ray and wad scaling, rounding
  direction and the bigint or float boundary, become the risk register and the
  scale-identity checks rather than a separate skill.
- One more marketplace package, one more boundary in the marketplace paragraph,
  and one more queue for Kronos to rank. That cost is accepted here rather than
  paid three times.
