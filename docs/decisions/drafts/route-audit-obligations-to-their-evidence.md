# Decision: Route audit obligations to their evidence

## Status

Proposed, 2026-09-20. The study selects this design. Step 1 publishes it at
`docs/decisions/drafts/route-audit-obligations-to-their-evidence.md`. Implementation and conformance remain pending.

## Context

A service scaffold cannot reproduce a failure in a native boundary that it
has not implemented. Historical repairs, upstream limitations and new target
requirements have different meanings. Counting each as a present regression
would encourage an import failure or a fabricated assertion to stand in for
behavior. Elenchus's parent runner deliberately forbids child processes.

Fiat already owns source-bound command execution for declared success criteria.
That execution proves a recorded command ran on its bound source. It does not
prove that the command tests a claim or that the host isolates an untrusted
workload.

## Decision

Add a checked applicability record that preserves source status and joins a
local regression to the existing guard route or a new integration requirement
to the existing observed-criteria route. Historical and excluded rows remain
visible and supply no success evidence. Freeze the captured routes for the run.

## Alternatives

Adding a process-capable parent runner opens another execution boundary and
still requires a parent defect where no feature exists. Accepting a manual
conformance report leaves execution unbound. The selected join uses the
execution owner already present and leaves Elenchus's promises unchanged.

## Consequences

The checker verifies source bytes, status witnesses, closed classifications
and target identities. Applicability itself remains an operator judgment.
An upstream limitation stays open or unknown even when a service later
demonstrates its own mitigation. Native tests must exercise actual behavior;
constant assertions and source-shape checks do not establish an OS boundary.

New captures refuse changed routing and stale or missing evidence. Historical
runs keep their old receipts and cannot acquire the new init marker by
amendment. A different classification requires a fresh reviewed run. This
delivery adds no service implementation or sandbox and publishes no private
checkpoint or credential material.
