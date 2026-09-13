# Decision: Rebind a runbook amendment on a holding verdict rather than dropping it

## Status

Proposed, 2026-09-13. Unnumbered until the integration composition assigns it.

## Context

`hexctl amend runbook` records the current study digest in each runbook amendment, and `source_runbook_step` in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` admits an amendment into the Mason and Warden packet only when that digest equals the current study digest. Every `hexctl amend study` changes the study digest, so every earlier runbook amendment leaves the effective step at once, with no printed line, no refusal and no ledger record. Run 856 reissued one step's repaired fields five times for this reason, and run 857 recorded the same loss as finding S1-R2-02. Issue #1264 asks for a transition that keeps the causal binding without silently reverting effective fields.

## Decision

At `hexctl amend study`, for each runbook amendment that is effective under the old study digest, the controller reads the new amendment's `Still holding` verdicts. When every step the runbook amendment touches has `entry holds; exit holds`, the controller records a rebind from the old study digest to the new one with decision `retained`; otherwise it records `displaced` and prints the step and the replaced fields. The rebind list is written inside the study amendment record, so it enters the existing `amend:study` ledger event and the existing write-ahead marker and recovery path. `source_runbook_step` and `amendment_block` admit an amendment when its recorded digest, followed through retained rebinds in study-amendment order, reaches the current study digest. A displaced amendment stays displaced; the operator reissues it under review. `verify` recomputes every rebind list from the two receipt histories and refuses a mismatch.

## Alternatives

`refuse-then-reissue`: refuse the study amendment while any effective runbook amendment would be displaced and print the list. It passed every hard gate but measured 17 operator reissues per unrelated study amendment against 0 for the chosen design, so it was dominated on the one selection metric.

`announce-only`: keep the drop and print the displaced count and fields. It failed the `stale-packet` gate: the next packet after an accepted study amendment is still built from baseline fields, which requirement 2 of the issue forbids.

## Consequences

An unrelated study correction no longer costs one reissue per effective runbook amendment. A study amendment that breaks a step's verdict still displaces every amendment touching that step, so a related change cannot pass through without review. Old runs verify unchanged because a study amendment record without a rebind list means no rebinds. The `amend:study` event data grows by one record per effective runbook amendment, measured at 288 bytes per record. The paragraph in `plugins/hexaemeron/skills/fiat/SKILL.md` that says a later study amendment makes an older repair no longer apply must be rewritten, which moves the agent-instruction manifest digests, and every edit to `hexctl.py` starts the four-stage digest re-pin chain named in the study.
