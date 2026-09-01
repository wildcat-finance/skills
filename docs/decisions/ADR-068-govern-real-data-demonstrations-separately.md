# ADR-068: Govern real-data demonstrations separately

## Status

Accepted, 2026-09-01.

## Context

The root README says what the collective can do. Nothing in the repository
bound one of those claims to a path a reader could run. A capability paragraph
and a demonstration were the same sentence, written once, checked by nobody,
and left to drift as the skill behind it changed.

The evidence is uneven and the unevenness matters. Lazarus replays a preserved
Ethereum mainnet view of Goldfinch at block 13097494. Alexandria rebuilds a
pinned Comet registry and RPC corpus. Anamnesis curates a preserved audit
corpus. Berean's grounded-agent example pairs a real Goldfinch corpus with
model records written for the example. Synkrisis compares runs that were
constructed to be compared. Most governed skills have a test suite over
fixtures and no demonstration at all. Calling all of that "what it can do"
flattens a distinction the reader is entitled to.

Two lanes were then obvious and one was not. `EVOLUTION.md` already governs
what a skill can do, with a held next job, a digest over the frontier line, and
a version the marketplace tests, Kronos, issue review and Fiat version
resolution all read. Adding demonstration state to that record changes the
meaning and digest of every skill's established behaviour lane, and a demo
improvement would then look like a behaviour advance. That was rejected on
compatibility grounds before anything was built.

## Decision

Demonstrations get their own lane, their own ledger, and their own frontier.

**One ledger per skill.** Every governed skill keeps `DEMONSTRATION.md` beside
its `SKILL.md` and `EVOLUTION.md`, holding one fenced
`shoggoth-demonstration/v1` record. Discovery is the registry: the checker
walks the same directories as `scripts/shoggoth_topology.py` and requires
exactly one record in each. There is no central inventory to fall out of date,
and one skill owner advances one ledger.

**Status is decided by inputs.** The five values are `real-data`, `mixed`,
`constructed`, `absent` and `not-applicable`, and the contract in
`plugins/hexaemeron/skills/DEMONSTRATIONS.md` fixes what each means. One
material constructed input stops a record being `real-data`. The checker
enforces that mechanically rather than trusting the prose above the fence.

**The lanes do not touch.** A demonstration ledger never changes an
`EVOLUTION.md` digest, held job or version, and an evolution ledger never
decides a demonstration status. Each carries its own version counter, its own
frontier revision, and its own digest over its own frontier line.

**Co-delivery.** One Fiat run may satisfy a behaviour frontier and a demo
frontier at once. It does so by meeting both acceptance sets independently and
advancing both ledgers on their own evidence. It does not get to advance one
because it advanced the other.

**Issue reuse.** `{skill}-demo` and `demo-frontier` are governed title and
label conventions for a demo job. A name in that shape is a convention, not
evidence that an issue exists. Where one issue can satisfy both acceptance
sets, both ledgers point at that one issue; a second is not filed to make the
queue look symmetric.

**The demo lane is read-only in this generation.**
`scripts/demonstrations.py frontier --lane demo --dry-run` ranks the open demo
frontiers and prints the one it would take. It reads only `DEMONSTRATION.md`.
It files no issue, dispatches no run, advances no ledger, and writes no
`.kronos/` state. Kronos keeps its default and phase-only modes reading only
`EVOLUTION.md`.

## Alternatives

**Put demonstration state in `EVOLUTION.md`.** The facts would sit beside the
skill and need one owner hop, which is the shape this repository already uses.
It was rejected on compatibility grounds: the versioning grammar hashes the
current frontier line, and Kronos, the marketplace tests, issue review and Fiat
version resolution all read that digest. A second frontier inside that record
changes the meaning and the digest of every skill's behaviour lane, so every
demonstration edit would read as a behaviour advance.

**One central demonstration registry.** A single file listing every skill's
demonstration would be easy to read and easy to check in one pass. It was
rejected because a global inventory drifts: a skill can be added, renamed or
removed without the registry noticing, and the registry becomes a second place
to be wrong. Discovery over the governed directories cannot fall out of date,
because the directories are what discovery reads.

**Prose alone.** Keep the capability paragraphs and mark the good ones by hand.
That is the status quo the run set out to fix. Nothing binds the paragraph to a
path, nothing notices when the path stops working, and the reader has no way to
tell a preserved capture from a fixture written last week.

## Consequences

A public capability card can now be bound to a record digest, and a card whose
record is absent, downgraded or stale fails a check rather than a reading.

Most records start at `constructed` or `absent`, and the repository says so out
loud. That is the point: the honest count of real-data demonstrations is small,
and the demo frontier exists to raise it.

The cost is one more ledger per skill and one more frontier to keep current.
The alternative was a second frontier inside a record whose digest a dozen
other checks already depend on, which would have made every demo edit look like
a behaviour change.
