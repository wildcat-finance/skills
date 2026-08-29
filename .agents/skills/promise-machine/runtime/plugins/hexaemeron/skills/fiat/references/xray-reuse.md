# X-Ray source reuse

Use the first-party adapter only to prepare one complete X-Ray run. It is not a
selectable skill, a final-analysis cache, or evidence that a reused fact was
correct when first produced. The digest-matched vendored X-Ray instruction
still owns the analysis and its four outputs.

## Preconditions

Before each round, recompute the SHA-256 of
`<plugin-root>/skills/x-ray/SKILL.md` and
`<plugin-root>/lib/xray_reuse.py`. They must match the
`hexaemeron-x-ray-preaudit` overlay in `<plugin-root>/PROMISES.md`. A mismatch
stops reuse until the overlay and changed source have been reviewed; it never
authorises an edit to the vendored X-Ray tree.

Build a fresh `hexaemeron.xray.scope.v1` manifest from the full logical scope
for the current step. It names every current source, every declared direct
dependency, the analyser identity, the current X-Ray instruction digest, and
the configuration digest. Preserve the pinned X-Ray operation: read and digest
every current source before planning, even when its prior preparation entry
could be reusable. An unsafe, unreadable, incomplete, or internally
inconsistent current scope is a refusal, not a cache fallback.

## One run

1. Run `xray_reuse.py plan` against the fresh scope and the operator-owned
   prior cache, if one exists. Any missing, malformed, mismatched, cyclic,
   incomplete, or otherwise uncertain cache produces `mode: full` with a
   named full-recomputation reason. A source addition or removal is a scope
   mismatch and also recomputes the full current scope. Never reuse common
   rows across a changed inventory.
2. Keep the pinned full-scope source reads and verification calls. Reuse
   replaces only preparation-fact regeneration. Regenerate an entry for every
   source in `dirty`; accept a reusable entry only after the current source and
   dependency digests validate. Each closed, capped entry carries declarations,
   types, inheritance, imports, roles, access, state and value facts, fund
   flows, entry points, calls, key logic, guards, symbolic deltas, transitions,
   `invariant_inputs` facts, and write sites. It supplies neither a command nor
   an unchecked filesystem path.
3. Run `xray_reuse.py assemble` with every fresh entry and any validated
   reusable entry. The resulting union must equal the exact current source
   inventory. Removed sources are absent. Rebuild the complete source-fact,
   write-site, property, call, and transition inputs from that union.
4. Run fresh coverage, history, integration, and cross-source analysis over the
   exact current union, then run fresh global synthesis. Regenerate all four
   final outputs: `architecture.json`, `x-ray.md`, `entry-points.md`, and
   `invariants.md`. Do not reuse a global synthesis, report fragment, finding,
   or security conclusion.
5. Run `xray_reuse.py bind-outputs`, then `xray_reuse.py promote`. Promotion
   requires an output manifest that binds the candidate digest, exact current
   source inventory, and current digests of all four outputs. A refusal or
   interruption leaves the previous cache untouched.

## Fiat boundary

Scope manifests, plans, preparation entries, candidates, output manifests,
cache paths, cache keys, cache payloads, and cache verdicts remain
operator-owned X-Ray working material. Do not add them to `hexctl` state, its
ledger, a Warden brief or audit directive, an audit-round receipt, or any other
Fiat receipt. Fiat continues to carry only its existing source-bound step,
risk, branch, suite, log, round, and audit-filter fields.

The adapter is a preparation layer only. Its JSON results answer whether the
plan was full or incremental and why, which sources were dirty, reusable,
removed, or reverse-invalidated, whether assembly covered the exact current
inventory, and whether promotion bound all four outputs. These one-shot
results are not retained telemetry and add no daemon, metric, trace, alert, or
controller authority.

## Refusal and recovery

Invalid current scope or fresh entries stop the round. Any cache uncertainty
never narrows work: discard it and use the plan's named full recomputation.
Assembly or promotion uncertainty stops before cache replacement. Repair the
named input, rerun the same operation, regenerate fresh global synthesis and
all four outputs, and promote only the complete digest-bound candidate.
