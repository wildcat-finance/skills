# Decision: Keep one complete Lazarus fixture in the portable runtime

## Status

Accepted, 2026-09-19.

## Context

The #1676 product at `e0afdb2640f1606f6493a7de344e89587e0962d4`
and main at `75e3a0c76faa0dfeb31f84aeff133b37ec3ad0d9` each fit the
portable package budget. Their composition twice produced 21,337,656 bytes.
The 26,214,400-byte cap reserves 5,242,880 bytes, so the complete package
ceiling is 20,971,520 bytes and this composition exceeded it by 366,136 bytes.
The count includes the runtime manifest and outer package files.

Six Lazarus Aave v4 v1 payloads occur with identical bytes and modes in both
`plugins/lazarus/examples/aave-v4-spoke-v1/` and
`plugins/lazarus/examples/aave-v4-spoke-v1-release/fixture/`:
`anchors.jsonl`, `header.json`, `plan.json`, `proofs.jsonl`,
`receipt-witness.json` and `rpc.jsonl`. Together they occupy 983,787 bytes in
each location. The second copy belongs to a complete preservation release.

## Decision

Keep the complete preservation release unchanged in the portable package and
omit only those six duplicate payloads from the standalone fixture directory.

Before any omission, the generator requires both copies to be tracked regular
files, rejects symlinked path components and compares exact bytes and modes.
A missing, untracked, linked or different copy refuses package generation.
Other files and other example directories remain outside this omission.

## Alternatives

Raising the cap or spending its reserve would remove the existing protection.
Omitting protocol schemas or verifier inputs would remove required runtime
content. Reformatting preserved JSON would change digest-bound evidence.
Deleting either source copy would change the checked full-source demonstration.
Keeping both packaged payload copies retains no additional evidence and fails
the composed package budget.

## Consequences

The source fixture, its program, manifest and complete preservation release stay
byte-identical in the source distribution. The installed release remains usable
by `verify-release`, and its nested complete fixture by `verify` and `replay`.
The package manifest declares the six omitted paths. The standalone manifest
and program remain as the historical demonstration record's named inputs;
their installed directory is incomplete and cannot run that demonstration.
`PORTABLE.md` directs reproduction to the full source checkout and ordinary
fixture operations to the complete retained copy.

The 25 MiB cap, 5 MiB reserve and 1,600-file tripwire remain unchanged. Package
checks verify exact retained release bytes and the complete package budget.
Focused guards reject a changed, missing, untracked or symlinked copy and a mode
mismatch. This is a distribution repair for the failed integration composition;
it does not change Lazarus verification, evidence classes or its frontier.
