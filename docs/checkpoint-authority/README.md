# Checkpoint authority protocol

## Current boundary

Step 1 preserves the adopted #862 specification, receipted P-862 study and
runbook, locked design and original selection reports. The protocol gates
remain unimplemented. The scaffold returns exit 3 and an unresolved result for
all four criteria; it establishes no signature, archive, journal or authority
claim. The decision is `adr/verify-checkpoint-authority-by-ordered-replay`.

## Governing sources

Read [the adopted specification](specimens/adopted-specification.md), [study](study.md)
and [delivery runbook](runbook.md). [Governing source identities](governing-sources.json)
bind their exact bytes, the original decision draft and the four historical
prefixes retained by the dated amendments. [The locked design](design-evidence.json)
and its ten reports under `reports/` are exact copies of study evidence.

These documents retain their original local paths, prospective wording and
historical results. The copies do not claim a fresh measurement, completion of
a later delivery step or publication of the ignored local evidence directories.
The original draft digest names the pre-integration draft; any later assigned
ADR path and heading are governed by the normal decision-assignment report.

## Layout and existing conventions

The separate implementation package is
`plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/`.
The [report interface](../../plugins/hexaemeron/skills/fiat/references/checkpoint-authority.md)
defines arguments, output, refusal and recovery. Closed schemas and fixtures
live below `plugins/hexaemeron/skills/fiat/checkpoint-authority/`; protocol
schema and behavioral fixture delivery starts in Step 2.

Reuse the root Apache-2.0 [license](../../LICENSE), exact Python pin in
[.python-version](../../.python-version), stdlib `unittest`, the Hexaemeron
runner and existing hosted workflows. This scaffold adds no dependency,
separate license, workflow or installer. `tests/check-map-v1.json` owns these
paths and selects the existing suites and lints. The normal tracked commit
hook requires greenlight on the staged tree.
