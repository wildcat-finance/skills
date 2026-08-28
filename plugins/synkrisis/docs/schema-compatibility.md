# Synkrisis schema compatibility

The public schemas under `references/` are versioned artefacts. Steps 2 and 3
ship `synkrisis-policy/v1`, `synkrisis-cohort/v1`, `synkrisis-rules/v1` and
`synkrisis-findings/v1` as JSON Schema documents, and the command checks the
manifest identity `synkrisis-manifest/v1` directly. The catalogue shipped at
`references/rules-v1.json` declares the rules identity and is checked against
it before any rule is applied.

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
- Any new disposition, reason code or refusal-code semantics change.
- Any cap raise. The 100-run, 100,000-event, 8 MiB and 64 MiB ceilings come
  from the study; raising one needs a study amendment first, then a `v2`
  identity for the shapes that expose it.

A `v2` reader must keep accepting `v1` documents or say plainly that it does
not; silent coexistence of two meanings under one identity is the failure
this record exists to prevent.

## Digest stability

Cohort documents are canonical JSON: sorted keys, compact separators, ASCII,
one trailing newline. The manifest, policy and cohort digests are SHA-256
over exactly those canonical bytes, and the cohort digest covers the cohort
body with the digest field itself excluded, so any reader can recompute it.
