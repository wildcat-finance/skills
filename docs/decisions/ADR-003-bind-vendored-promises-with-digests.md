# ADR-003: Bind vendored promises with digests

## Status

Accepted, 2026-08-20. Promise Machine contract: `promise-machine/v1`.

## Context

Five Hexaemeron skills are vendored from an upstream source. Their instruction
files must remain attributable and byte-exact, but the Wildcat suite still
needs to state what evidence it accepts from those operations and what each
result authorises. Writing the suite contract into a vendored instruction
would silently fork the upstream work. An unbound note elsewhere could survive
an upstream change while describing behaviour the new bytes no longer have.

## Decision

Keep each upstream `SKILL.md` unchanged. Hold the Wildcat declarations in the
single first-party file `plugins/hexaemeron/PROMISES.md`. Every declaration
names one discovered vendored canonical path and the SHA-256 of that file's
exact bytes, followed by the nine Promise Machine fields.

The repository checker recomputes each digest and rejects a missing overlay,
an extra overlay location, an unsafe or absent path, a first-party target, a
duplicate path or promise identifier, incomplete fields, uncovered vendored
skills and byte drift. A runtime that selects a vendored skill reads its block
and compares the recorded digest before relying on the overlay. Digest drift
blocks the Wildcat promise; it does not authorise editing the upstream file.

## Alternatives

- Editing vendored instructions would create an unattributed local fork and
  make upstream comparison unreliable.
- A notice without a digest would not show whether the declaration still
  described the instruction actually installed.
- Separate overlay files beside each vendored skill would widen discovery and
  make omission and duplicate ownership harder to check.

## Consequences

An upstream update now fails closed until its changed instruction is reviewed
and the corresponding declaration and digest are deliberately updated. The
overlay remains Wildcat-authored; the upstream instruction and attribution
remain intact. The digest binds bytes, not truth: executable and review
evidence must still satisfy the declaration before it authorises anything.

Rollback is all-or-nothing. Remove the overlay, its runtime binding, checker
component and tests together; do not leave an unchecked promise beside
vendored instructions.
