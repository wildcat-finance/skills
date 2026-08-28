# Synkrisis schema compatibility

The four public schemas under `references/` are versioned artefacts:
`synkrisis-policy/v1`, `synkrisis-cohort/v1`, `synkrisis-rules/v1` and
`synkrisis-findings/v1`, plus the manifest identity `synkrisis-manifest/v1`
the command checks directly. The scale-fixture specification
`synkrisis-scale-fixture/v1` is a test artefact, not a public surface.

## What a version promises

A document naming one of these identities parses under exactly that version's
shape: the field set is closed, unknown fields refuse, and every identity
string is checked before any content is read. The command never guesses a
version from structure and never accepts a newer identity with older code.

## What may change without a new version

Nothing in a shipped shape. Prose around the schemas, examples and tests may
change freely; the accepted bytes of a `v1` document may not. A defect fix
that narrows what was already documented as refused is a repair, not a
version change, and lands with a red-to-green guard.

## What requires a new version

- Any new, removed, renamed or retyped field in a shipped shape.
- Any new rule kind, handoff target, disposition, reason code or refusal
  code semantics change.
- Any cap raise. The 100-run, 100,000-event, 8 MiB and 64 MiB ceilings come
  from the study; raising one needs a study amendment first, then a `v2`
  identity for the shapes that expose it.

A `v2` reader must keep accepting `v1` documents or say plainly that it does
not; silent coexistence of two meanings under one identity is the failure
this record exists to prevent.

## Digest stability

Cohort and findings documents are canonical JSON: sorted keys, compact
separators, ASCII, one trailing newline. Digests are SHA-256 over exactly
those bytes. Fingerprints hash the rule id, the subject and the sorted
run-and-event references, never a host path or mutable prose, so a harmless
reordering of the manifest leaves every fingerprint unchanged.
