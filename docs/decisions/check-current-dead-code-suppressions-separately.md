# Decision: Check current dead-code suppressions separately

## Status

Accepted, 2026-08-31. Integration assigns the next free `ADR-NNN` identity
against the current default branch and moves current references with it.

## Context

The dead-code baseline verifies its recorded source commit. That historical
proof does not validate `.dead-code/suppressions.json` at the checkout. A stale,
malformed, or unused current entry could therefore pass the existing workflow
when the recorded source copy remained valid.

[ADR-053](ADR-053-keep-dead-code-discovery-report-only.md) keeps findings
advisory and suppressions exact. [ADR-059](ADR-059-report-baseline-currency-without-failing-the-check.md)
keeps baseline currency separate from historical validity.
[ADR-045](ADR-045-select-and-schedule-repository-checks-from-one-graph.md)
puts repository check selection in `tests/check-map-v1.json`. The new check must
fit those decisions without changing their contracts.

## Decision

Add `python3 scripts/dead_code.py suppressions --check` as a dedicated,
read-only current-commit validator. It builds the fixed `python,repository`
report and reads the suppression file from the same clean commit. Existing
size, regular-file, duplicate-key, canonical JSON, exact identity, path, and
symbol checks decide validity. Failed, unavailable, or missing analyser states
refuse a result.

Register the literal command as its own check in the existing `dead-code`
scope. The workflow continues to invoke only
`python3 scripts/run_checks.py --scope dead-code`, so command ownership stays
in the checked graph and is not copied into workflow prose.

Keep `report` and `baseline --check` unchanged. A valid suppression remains an
exception record over a report-only candidate. It does not establish that the
candidate is dead and does not authorise deletion.

## Alternatives

Add suppression validation as a `report` mode. Rejected because this creates
interactions with the existing JSON, output, analyser, and coverage options. It
would change a command whose default deliberately runs no analyser, with no
measured time or output benefit.

Make `baseline --check` reconstruct the recorded source and current checkout.
Rejected because it combines two proofs and repeats the analyser work. The
measured sequential path was 67.54 seconds, above the 46-second baseline-check
ceiling.

Put a direct command in the workflow without adding it to the check map.
Rejected because the repository would then have two selection authorities and
local `dead-code` scope runs could omit the live check.

## Consequences

Every checked `dead-code` scope runs the focused suite and the live committed
suppression validator. The added analyser pass costs roughly the existing live
static report and must remain within the recorded 46-second wall-time ceiling.
The command writes no durable artefact and emits one bounded success line.

Operators have one correction-and-rerun entrypoint for current suppressions.
The historical baseline keeps its source-commit suppression read, `published`,
`currency`, and `status` summary. Reversing the public command or its check-map
placement requires another decision because CI and operator instructions now
depend on both.
