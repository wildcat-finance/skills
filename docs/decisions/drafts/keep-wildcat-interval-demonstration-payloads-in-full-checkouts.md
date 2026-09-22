# Decision: Keep Wildcat interval demonstration payloads in full checkouts

## Status

Accepted, 2026-09-22.

## Context

Composing #1731 with main produced 21,009,325 runtime payload bytes before
the manifest and outer package files. The unchanged 25 MiB cap and 5 MiB
reserve allow 20,971,520 bytes for the complete package. The source trees
fit separately; their composition does not.

## Decision

Omit direct JSON files and pre-plan probes from the portable copies of the
Wildcat V1 and V2 interval v0 demonstrations. Keep their documents and Python
entrypoints. Both metadata verification and rebuilding use the full source
checkout; rebuilding also needs the already external private staging archives.
Declare this boundary in the package manifest and PORTABLE.md.

## Alternatives

Raising the limit or consuming its reserve removes the existing protection.
Reformatting captured JSON changes digest-bound evidence. Removing collector,
verifier or schema files breaks runtime operations. Omitting source evidence
from the repository would prevent reproduction.

## Consequences

The source demonstrations, captured bytes and runtime code remain unchanged.
The portable metadata demonstrations are incomplete, so their entrypoints
must be run from a full checkout. Package checks verify retained documents
and programs, omitted payloads and the complete package budget. The 1,600-file
tripwire remains fixed. This is a distribution repair for the failed merge
composition; it changes neither Alexandria's capture contract nor its frontier.
