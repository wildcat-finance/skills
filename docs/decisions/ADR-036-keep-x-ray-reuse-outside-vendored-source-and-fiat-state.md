# ADR-036: Keep X-Ray reuse outside vendored source and Fiat state

## Status

Accepted, 2026-08-25.

## Context

Fiat audit rounds give X-Ray the complete current Solidity scope. When one
source changes, X-Ray repeats preparation for every source even though some
source-bound facts remain usable. Reuse can reduce that repeated extraction,
but stale dependency facts, a changed source inventory, or partial final
outputs can narrow the analysis without making the loss obvious.

The X-Ray skill under `plugins/hexaemeron/skills/x-ray/` is vendored Pashov
source. Wildcat binds its accepted result through a digest-pinned Promise
Machine overlay and does not edit those upstream-owned bytes. Fiat controls
delivery receipts; it is not an analysis artefact store or an authority on the
validity of X-Ray facts.

## Decision

Keep reuse in the first-party adapter
`plugins/hexaemeron/lib/xray_reuse.py`, outside the vendored X-Ray tree. The
adapter caches only validated per-source preparation entries. Each entry binds
the source digest, analyser and configuration identity, declared direct
dependencies, and every relevant transitive dependency digest.

A byte or dependency change dirties that source and its reverse dependants. An
added or removed source forces named full recomputation, as does missing,
malformed, incomplete, mismatched, cyclic, or otherwise uncertain cache
material. The current scope is always authoritative; a cache row cannot add a
source to it.

Assembly combines fresh entries with still-valid entries only when their union
equals the exact current scope. It rebuilds the complete write-site map and all
property, call, and transition inputs from that union. It does not reuse final
findings or derived security conclusions.

Promotion requires `architecture.json`, `entry-points.md`, `invariants.md`, and
`x-ray.md`, plus a source-inventory manifest whose four digests match those
exact files. The manifest also binds the canonical digest of the candidate
facts and synthesis. Atomic replacement occurs only after that manifest covers
the candidate's exact current source inventory. Cache keys, entries, plans,
and verdicts do not enter Fiat state, receipts, or ledgers.

## Alternatives

- Edit the vendored X-Ray instruction. This would make invocation shorter, but
  it would fork upstream behaviour and invalidate the repository's digest
  ownership boundary.
- Store cache content in Fiat state. This would make run lookup convenient, but
  it would make a delivery controller attest analysis validity and expand a
  receipt schema for unrelated data.
- Add a selectable reuse skill. This would give the operation its own router
  identity, but it would widen the marketplace for an internal preparation
  layer that has no independent evidence promise.
- Reuse final reports or global conclusions. This would avoid more synthesis,
  but it cannot prove that a local change left cross-contract properties or
  complete write sets unchanged.

## Consequences

Unchanged, source-bound preparation entries can survive another X-Ray run
without changing the four-output X-Ray promise. Dependency bytes and exact
scope membership remain part of cache validity, while global synthesis and
final output generation remain current-run work.

The audit path gains a scope manifest, a preparation-entry format, an output
manifest, and one first-party adapter to maintain. A source addition or removal
recomputes more than the common rows strictly require, and every run still pays
the cost of global synthesis and all four final outputs. Those costs are the
price of keeping cache uncertainty from masquerading as analysis evidence.
