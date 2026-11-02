# Decision: Keep Wildcat parameter events as native state

## Status

Proposed, 2026-11-01

## Context

Issue #2090 asks for canonical meanings for the first four event groups and specific reasons for unsupported administrative events. The current ABI table contains 29 required generation, role and signature contexts across 58 concrete-ABI declarations. The issue leaves role enums, parameter value-versus-difference meaning and the market of a marketless hook event unchecked. Published Wildcat releases use adapter `1.0.0`, and the release policy preserves their bytes.

## Decision

Select `native-fields` from the checked design matrix. Map each admitted state event through its generation, emitter role and signature. Preserve exact decoded ABI fields beside the raw log, including the empty-string field name of V1 lender authorisations. State events carry empty financial amounts. Parties identify the emitter and only additional accounts, providers or markets actually emitted; a marketless hooks/controller event acquires no inferred pool party. Numeric roles stay numeric, and basis points and timestamps stay native values.

Add adapter `1.2.0` for this issue and preserve explicit `1.0.0` replay. Verification selects a supported recorded version and still rebuilds every semantic byte. New public constructed releases occupy fresh directories. The signed integration base may also contain #2089's `1.1.0` fee interpretation; integration preserves that version and composes its delivered fees into `1.2.0` before revalidating affected schemas and verification. No unmerged sibling source supplies evidence.

The final administrative group keeps `unsupported-canonical-meaning` and its canonical coverage gap, with a reason specific to each recognised ABI signature. Constructed fixtures exercise all required contexts. Retained releases establish only meanings actually observed within their verified scope; absent signatures remain explicit private missingness. The user's acceptance of any absent historical positives remains required before integration.

## Alternatives

`contextual-projection` interprets role labels, converts parameters and supplies a market from contextual or neighbouring records. It fails the source-bound-fields selection criterion because those interpretations exceed the issue's evidence. A generic state object on the canonical row would add another representation of values already preserved in `mapping_records[].decoded` and require another schema surface; the existing decoded record supplies the required home. Keeping all events unsupported would leave the user's first four groups undelivered.

## Consequences

Consumers receive venue-qualified actions and directly emitted parties while preserving native-state uncertainty. The closed Python and schema tables must agree on all actions, party cardinalities, instruments, empty amounts and supported versions. Existing releases remain verifiable without rewriting historical bytes. New reports must prove safe-path imports, create-only writes, non-vacuous retained checks and semantic tamper refusal. Private captures, paths, counts and per-signature historical inventories stay outside Git; the public retained record carries only release identifiers, digests and pass/refuse booleans. No access-policy replay, standing, settlement, identity or chain-proof conclusion follows.
