# Decision: Confine the worker before admitting its output

## Status

Accepted, 2026-09-13. Implementation follows the issue 508 runbook.

## Context

Issue 508 requires out-of-target writes to be denied regardless of the tool a
worker uses. Its other modules preserve exhausted audit evidence and validate
runbook commands before receipt. The receipted study selects
`whole-worker-sandbox` using native macOS process specimens.

## Decision

Launch every enabled worker executor beneath one native OS policy, keep
controller authority outside, and admit only a verified private output snapshot.
Bind replacement-run carryover to one complete cumulative packet and bind
runbook command validation to declared parser interfaces and source digests.

## Alternatives

`optional-tool-mediation` leaves another writer exposed; that writer succeeded
in the comparative specimen. A mandatory broker without bypass could satisfy
the same requirement but was not the rejected candidate. A disposable VM remains
with programme issue 873; no VM measurement was made for this selection.

## Consequences

The finite macOS executable prototype must refuse unsupported hosts and external
deputies. The current conversation's tools remain outside that enforcement.
Workers cannot write live controller or shared Git metadata. Detached workers
cannot change the private snapshot admitted by the controller; uncertain
cleanup blocks scratch reuse. The conformance matrix requires executed evidence
before each dependent transition. Primitive measurements alone cannot pass it.

One carryover packet must preserve full changed-file payloads, findings, guards,
lineage and signed fixed-tree identity. Complete reconstruction precedes every
execution gate. Command validation preserves source-owned report declarations
and bytes while checking absolute execution destinations. These choices leave
programme issues 872, 873, 875 and 878 with their existing owners.
