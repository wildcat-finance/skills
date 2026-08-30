# ADR-054: Report baseline currency without failing the check

## Status

Accepted, 2026-08-30.

The runbook for issue #936 allocated this decision as ADR-054 and required the
number to be re-confirmed before the record was written. `ADR-053` was the
highest identity in `docs/decisions` on `origin/main` at that point, so the
allocation held.

## Context

`python3 scripts/dead_code.py baseline --check` refused whenever any tracked
path changed between the commit that published `.dead-code/baseline.json` and
the checkout. Issue #936 reproduced it on workflow run 33291365525, where the
five named paths were the ones a Fiat first step always writes: the refreshed
Horos boundary, an audit round with its synopsis, and the tracked copies of a
run's study and runbook.

That refusal established nothing about the record. The command rebuilds its
expected document at the recorded source commit, not at the checkout, so the
comparison it exists to perform reads the exact tree the baseline names and a
later commit cannot change the answer. ADR-053 fixes when this command fails,
and a checkout that has moved on is none of the cases it lists.

The check gates no merge, because it is not a required status. It stops an
agent instead: a delivery told to wait for its gates waits for a green that
never arrives.

## Decision

Separate currency from validity in the exit status.

Validity keeps the exit status. Every refusal that establishes the recorded
document is the document recomputed at its own source commit still exits 2:
a dirty checkout, an unreadable or oversized record, a record that fails
validation or is not canonical JSON, a source commit equal to the checkout or
not an ancestor of it, a publication commit that changed more than its owned
record, any drift the recorded and recomputed documents show, and any
suppression refusal at the source commit.

Currency becomes an observation. When tracked paths changed after the
publication commit, the command names up to five of them on a `currency` line
and exits 0. When none did, the line says so.

Discover the publication commit rather than assume the checkout is it.
`git rev-list -1 <checkout> -- .dead-code/baseline.json` names the commit that
wrote the checked-out record. The check refuses when no reachable commit wrote
it, and refuses when the record changed after the commit that discovery
returned, so the two diffs it then takes are anchored to a commit whose bytes
are the checkout's. `source..publication` must still change exactly
`.dead-code/baseline.json`, which keeps the older publication refusal against
the commit it always described.

Keep the currency result out of machine-readable output. It is printed in the
command's text summary and copied into the workflow step summary, and nowhere
else.

## Alternatives

Split the existing source-to-checkout diff in place and report whatever is not
the record. Rejected because the remaining set can no longer tell a publication
commit that also changed source from a later commit that did, so the refusal
against a publication commit touching other paths would be lost in silence.

Add an opt-in `--allow-stale` flag. Rejected because the default would stay the
broken one, every caller would have to remember the flag, and the command would
remain unusable by hand on any checkout that has moved.

Compute currency in the workflow instead of the command. Rejected because it
copies the contract into a file with no tests and leaves the command unusable
locally.

Record currency in the baseline document, or emit it as JSON. Rejected because
currency is a relation between the record and a checkout that moves after the
record is written, so the document cannot hold it, and no consumer gates or
routes on it today. A consumer that needs to would need its own schema
decision.

## Consequences

CI goes red for this command on validity alone. A repository whose checkout has
moved past the publication commit reads green with a stale currency line, and a
reader who needs to know how far behind the record is finds the changed paths
on that line and the publication commit on the `published` line above it. The
workflow step summary carries both lines as the command wrote them.

The command now depends on `git rev-list` path history, which history
simplification can shape. The blob check is the price of trusting the answer:
a discovered commit that does not hold the checkout's record bytes refuses
rather than being used.

Nothing serialised changes. The recorded document gains no field, its schema
definition is untouched, and the tool identity stays `dead-code 1`.

Reversing this means every run that has learned to read a green-and-stale check
goes back to waiting on a red one, so the reversal is a decision of its own.
ADR-053 stays as it is; whether a stale baseline should eventually expire is
still the separate decision it defers.
