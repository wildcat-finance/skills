# Decision: Keep one complete Lazarus fixture in the portable runtime

## Status

Accepted, 2026-09-19.

## Context

The #1731 delivery at `1fd0abdad1acfdac6f560ba80d5667f6df00e7a0` measured a
complete package of 20,971,411 bytes after its step 6 audit had shortened
prose in packaged files to fit. Restoring that prose produces 20,973,160 bytes.
The 26,214,400-byte cap reserves 5,242,880 bytes, so the complete package
ceiling is 20,971,520 bytes and the restored tree exceeds it by 1,640 bytes.
The count includes the runtime manifest and outer package files. `origin/main`
adopted this decision on 2026-09-19 for the #1676 integration composition, in
merge `229f5856e03b9cd60c2265281696944281b35308`; this branch carries it ahead
of its own sync.

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
this branch's package budget.

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
mismatch. This is a distribution repair for a package at its ceiling;
it does not change Lazarus verification, evidence classes or its frontier.
