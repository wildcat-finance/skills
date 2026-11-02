# Decision: Version Wildcat fee-event meanings while preserving old releases

## Status

Proposed, 2026-11-01. This record selects the study design for issue #2089; no product implementation or final retained acceptance is claimed.

## Context

The amount-only `FeesCollected(uint256)` event is currently decoded and left unsupported in both Wildcat generations. V2's `ProtocolFeeBipsUpdated(uint256)` is also unsupported. Issue [#2089](https://github.com/wildcat-finance/skills/issues/2089) requests native canonical meanings for those three contexts. The release policy requires old published bytes to remain immutable.

## Decision

Use adapter mapping version `1.1.0` for the new meanings and retain explicit `1.0.0` reconstruction. The builder defaults to the new version and accepts an explicit supported version for reproduction. Verification selects the version declared by the preserved manifest and rederives the source descriptors, canonical rows, capture and coverage under that version. Unknown versions and old-version/new-rule combinations refuse. Mapping versions remain separate from package and skill versions.

`wildcat-v1.fees-collected` and `wildcat-v2.fees-collected` use family `fee-collection`, party `pool` only, and one `assets` amount from native `assets`, in underlying base units. The recipient remains `attribution:fees-collected:recipient`. A missing underlying asset remains null with `attribution:fees-collected:asset`. Fee collection has its own action, separate from repayment and withdrawal. No co-occurring transfer supplies a recipient or causal join.

`wildcat-v2.protocol-fee-bips-updated` uses family `pool-state`, party `pool` only and no amount. `protocolFeeBips` remains decoded native state, as the market closure timestamp does; no percentage or asset amount is derived. The updating actor remains an attribution gap. V1's factory `UpdateProtocolFeeConfiguration(address,uint16,address,uint256)` stays unsupported.

## Alternatives

The alternatives were an in-place extension of `1.0.0`, which would change a published fee-containing release, and reusing the repayment action, which would change the native meaning. The executed representation models reject each on its named gate. Their reports, selected candidate `versioned-native` and complete design matrix live in the issue's study packet. The model result authorizes runbook derivation, not product conformance.

## Consequences

Compatibility requires both every committed old release and a constructed old fee-containing release to reconstruct byte-identically under `1.0.0`. New fee actions are admitted only under `1.1.0`. Existing actions remain readable under both versions. The retained `1.0.0` recipe is the exact starting-tree interpretation; earlier batch and wrapper additions reused that same version token, so this dispatch does not establish universal reconstruction of every older recipe era. Later #2090 and #2091 mapping versions must preserve every lower-version result when integrated.

The available retained V1 release has no `FeesCollected`; the available retained V2 release has `FeesCollected` and no `ProtocolFeeBipsUpdated`. Constructed specimens can establish positive mapping controls, and both retained releases can establish bounded rebuild observations, but neither establishes a positive observation of an absent native event. Final acceptance is pending the user's clarification or separately preserved positive inputs. The retained-conformance criterion checks both verified inventories and every target event actually present, records per-signature absences and refuses when the combined target set is empty. That qualified result never establishes positive execution of an absent event or closes the separate historical-acceptance gap.

The public reproduction will preserve source release identifiers, digests and per-generation pass or refuse outcomes. Private capture payloads, custody paths and capture-derived counts stay local. Product build, schema parity, old-version reconstruction and retained observations remain separately checked transitions. A failed check leaves the old release and raw evidence intact; recovery builds a corrected superseding release into a fresh directory.
