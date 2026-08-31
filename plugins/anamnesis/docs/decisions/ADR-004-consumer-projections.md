# ADR-004: Give Elenchus and Synkrisis projections, not ownership

## Status

Accepted, 2026-08-31.

## Context

The corpus is worth having because two existing members can use it. Elenchus
works a present failure to its cause and guards it; a past case that looks the
same is a useful place to start. Synkrisis compares declared observations; a
corpus cohort is more of the same kind of input.

Both connections can be made in a way that breaks the member on the other end.
If Elenchus can read a past `guarded` verdict and carry it forward, similarity
becomes proof and the guard rule stops meaning anything. If Synkrisis takes the
corpus as a general data source, it acquires the capture and custody boundary it
explicitly refuses.

## Decision

Each consumer reads a closed, versioned, read-only projection through a named
adapter.

The Elenchus projection returns source-linked historical analogues and no
verdict. It cannot carry `guarded`, `unguarded`, `passed` or `inconclusive`
from a past case into a present one. Elenchus still reproduces the current
failure and still earns its own guard; the analogue is a hypothesis.

The Synkrisis projection emits only the audit-corpus observation schema
Synkrisis explicitly admits, with cohort, denominator, inclusion policy,
missingness and exclusions intact. It transfers no custody and no authority to
act.

Restricted material crosses neither adapter. An adapter refusal does not mutate
the corpus or relax its schema.

## Alternatives

**One general query interface.** Fewer moving parts, and every consumer reads
what it likes. It has no place to state what a given consumer may not see, so
the two failures above become possible by default rather than refused by
construction.

**Let each consumer own its own reader.** Puts the boundary inside the member
that benefits from crossing it. The adapter would then be maintained by the
party with the least reason to keep it narrow.

## Consequences

Two schemas to version rather than one interface, and a new consumer needs a
new adapter rather than a query.

Each adapter is a written statement of what that consumer may see, so widening
one is a visible change with an owner, not a query someone wrote differently.

An aggregate that leaves the Synkrisis adapter carries its denominator and its
exclusions, so a corpus figure cannot be read as a claim about the wider
ecosystem.
