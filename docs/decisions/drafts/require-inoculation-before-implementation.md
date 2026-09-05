# Decision: Require inoculation before implementation

## Status

Proposed, 2026-09-05. Stable identity
`adr/require-inoculation-before-implementation`; the integration composer
assigns its number.

## Context

Fiat receipts a runbook and currently opens implementation directly. Mason can
therefore edit product code before the run has shown that the failures already
named by its audit history are caught by tests. Elenchus can classify a test on
an unfixed commit as `guarded`, but the existing controller retains only that
word. It does not bind the result to a complete known-failure inventory, the
step parent, the test-only paths, the exact report bytes, or the step that must
consume it.

This is a cross-cutting permission boundary, not one skill's local parsing
choice. A partial result must survive resume without becoming a complete one,
and a deliberately red guard commit must not become the step's publishable
head. The selected construction and its evidence are in the
[known-failure inoculation study](../../known-failure-inoculation-study.md).
The delivery order and checks are in the
[runbook](../../../plugins/hexaemeron/docs/known-failure-inoculation/runbook.md).

## Decision

Use the selected `receipted-inoculation` design: add an explicit `inoculate`
phase between runbook receipt and implementation for new contract-aware Fiat
runs. Protasis supplies one immutable,
source-digest-bound inventory with an exact independent finding-id set, one
consuming step per finding, declared guard paths, and fixed reporter commands.

For each step with assigned findings, Mason first creates one signed guard-only
commit whose sole parent is the exact step parent and whose changed paths are
exactly the union declared for that step's findings. Product paths are
inadmissible in this commit. Each declared command runs through Elenchus
against that object. The controller retains the bounded report bytes and a
manifest that binds their digest, command, format, counters, finding, parent,
commit, paths, and test blobs. Only the exact `guarded` verdict counts. The
assigned set is receipted atomically; a subset, runner fault, empty run, skip,
expected failure, unexpected success, error, or any other verdict leaves
implementation closed.

A valid digest-bound no-known-findings claim has no guard commit or Elenchus
run. The controller receipts that explicit empty set before implementation.

After the product fix, the same finding identities and command shapes must run
on the final step tree with positive, complete, non-skipped, error-free, and
assertion-free reports. The root and Hexaemeron suites must also pass before
the step can finish. The transient red commit remains in the open step's local
ancestry; it is neither pushed as the finished head nor described as green.
Mason authors guards and product changes. Warden audits only after inoculation
and final-green evidence exist.

Pre-contract states keep their prior transition shape and receive no invented
inventory or receipt. A run delivering this controller cannot claim that its
not-yet-installed phase protected itself. It uses the runbook's manual signed
guard bootstrap, retains that evidence outside Git, and states the limit. Once
the new contract is installed, resume and verification reconstruct the
inventory, remaining ids, parent, reports, and manifests before exposing any
later transition.

## Alternatives

- Keep the current phase list and require a guard-only commit followed by a
  product commit inside implementation. This avoids a controller round trip,
  but the controller learns about an early product edit only at the end, and a
  restart cannot distinguish a valid guard interval from a bypass.
- Run Warden before implementation and treat the audit as inoculation. This
  provides an earlier stop, but reverses the worker order and makes Warden
  author Mason's test artefacts.
- Record the inventory and inspect it only during the ordinary post-build
  audit. This preserves the existing controller, but it cannot prevent the
  production changes whose ordering is the subject of the decision.

## Consequences

Known failures become a pre-edit permission check with reconstructible
evidence. A resume can name what remains, and verification can replay the join
from source inventory through guard bytes and fixed-tree results. Missing or
ambiguous evidence stops at the boundary instead of being inferred from a
later green suite.

Each guarded step gains one controller round trip, a temporary signed red
commit, retained reports, manifests, and receipts. The implementation must
maintain native Git, bounded no-follow file, and exact command checks across
that evidence. Recovery takes longer because the complete assigned set must be
replayed after drift, but it has one defined route: restore the exact inputs,
rerun the guards, and receipt the set again.

The phase proves only the failures declared in the immutable inventory. It
does not discover unknown failures, establish that a source locator supports a
claim, change Elenchus's four verdict meanings, or replace Warden's later
review. New findings enter a later receipted inventory; they do not silently
rewrite the one that authorised an existing run.
