# ADR-092: Stage reviewed corpus reconciliation before publication

## Status

Selected, 2026-09-13, for [issue #1513](https://github.com/wildcat-finance/skills/issues/1513).
Step 2 implements the staged repair and completes the fresh law demonstration.
The three integration resolvers remain required before delivery.

## Context

The current repair selects `fiat-study-runbook-phase` alone. A law edit can
therefore refuse as unrelated drift, and re-pinning its digest alone can report
`nothing-to-reconcile` while deeper bindings remain stale. The six live passes
also lack a transaction. [ADR-076](ADR-076-digest-neutral-measured-corpus.md)
retains v1 absolute offsets, so moving a reviewed span can change measured
model and compact bytes even when its meaning is unchanged.

## Decision

Use `staged-general-v1`: prepare every fixture bound to one explicit source
against an accepted immutable baseline, admit the complete staged corpus and
its owner evidence, then apply through a recoverable publication journal.

The [study](../agent-instruction-reconciliation/study.md) and
[checked matrix](../agent-instruction-reconciliation/design-evidence.json)
hold the contract. Preparation uniquely relocates exact reviewed spans and
nodes, keeps the contributor's edit, and refuses unexplained sibling drift.
Moved measured inputs require fresh complete measurement and parity records
under unchanged profile authority. Apply records intent before writing;
recovery restores only targets matching the recorded bytes and stable
identities. Atomic exchange keeps displaced files in journal-bound publication
and restoration slots. A concurrent version remains preserved, with its target,
path and digest in the refusal; recovery refuses while that conflict remains.
Unsupported hosts or filesystems refuse without replacement fallback.
Manifest and coverage follow their inputs.

## Alternatives

| Candidate | Observed selection result | Reason rejected or selected |
| --- | --- | --- |
| `fixed-live-v1` | Correctly classifies 1/6 placements | Fails the six-placement gate and has no checked recovery primitive. |
| `sequential-general-v1` | Classifies 6/6; restores 1/4 injected faults | Fails the preimage-recovery gate. |
| `staged-general-v1` | Classifies 6/6; restores 4/4 injected faults | Passes selection gates at 24,092 extra old/new bytes for four law targets. |

Classification includes a before-span evidence refusal. It does not mean six
accepted corpora. The nearest-rank p95 values are 226, 263 and 227 ms in row
order, from six preparation samples per candidate; they establish no speed
improvement. That selection probe handles injected `OSError` only. The subsequent
[implementation demonstration](../agent-instruction-reconciliation/demonstration.json)
records durable intent, actual killed-process recovery, coverage publication
and one fully checked law repair with fresh owner evidence.

## Consequences

The v1 schema, three fixtures and 15 reviewed bindings stay intact. Reports
distinguish `needs-evidence` from a completed repair. Integration still requires
boundary conformance, a completed fresh law demonstration and final currency,
through the three selected resolvers in the immutable matrix. Stage and journal
files are capped at 1 MiB, with at most 256 targets and 32 MiB total staged
content. Existing checker subprocess limits remain 600 seconds and 1 MiB output.
The package must retain at least 5,242,880 bytes below its 26,214,400-byte cap.

Issue #1192 retains relative offsets; #1198, #1199, #1200 and #1267 retain
their study-listed carryovers. #1467 is delivered through PR #1554 and receives
package-reserve verification after this run. This decision extends ADR-076's
operational repair without changing its text or claiming hardware power-loss
atomicity, model quality or independent token-count truth. Final integration
assigns the draft's number.
