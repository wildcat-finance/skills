# Decision: Dispatch the interval collector's registry check on the plan's venue

## Status

Accepted, 2026-09-19. Numberless until the merge that lands it, under the
draft path [ADR-077](../ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md)
set out.

## Context

`plugins/alexandria/scripts/usdc_interval.py` collected only Ethereum USDC
Comet intervals. Its `Builder` validated every deployment registry by
importing `alexandria_lib.compound_registry.validate_registry` directly, and
its coverage-gap accounting for the `registry` component was one
Compound-specific sentence written inline. [#1731](https://github.com/wildcat-finance/skills/issues/1731)
asks the same collector to serve a second, Wildcat estate whose deployment
registry carries neither Compound's declared format
(`alexandria-compound-v3-registry/v1`) nor its pinned bytes
(`REGISTRY_SHA256` in `compound_registry.py`).

`.hexaemeron/design-evidence.json` (`protasis-design-evidence/v1`, selected
2026-09-19) graded four candidates against six selection criteria.
`venue-module-registry` passed all six. `registry-format-dispatch` (dispatch
on the registry document's own format string) failed
`venue-registry-agreement-checked`: a registry of some other venue's format
would never be compared against the venue the plan actually names.
`venue-parameter-table` (one code path, a per-estate parameter document
supplied alongside the plan) failed both
`venue-registry-agreement-checked` and `venue-pin-in-reviewed-code`: the pin
would live in an operator-supplied document rather than in reviewed code.
`separate-wildcat-collector` (a second collector for the Wildcat estate)
failed `existing-build-check-path`: it would fork the build/check path this
collector, its tests and its two other example demonstrations already share.

## Decision

Dispatch on the plan's own `venue` field (a plan already carries one; its
value for the shipped Comet interval is `compound-v3`) through one explicit
table, `VENUES` in
`plugins/alexandria/scripts/alexandria_lib/venues/__init__.py`, built from
each registered module's own `VENUE` name rather than restated as a second
list. `venues/compound_v3.py` is the one module registered so far: it
re-exports `compound_registry.validate_registry` unedited and supplies the
registry coverage-gap sentence `usdc_interval.py` used to compute inline,
unchanged word for word. `usdc_interval.py`'s `Builder.__init__` and the
`registry` branch of `_gaps` reach both through `VENUES[plan["venue"]]`
instead of importing `validate_registry` directly. `compound_registry.py`
itself is not edited.

A plan naming a venue absent from `VENUES` refuses by name
(`AlexandriaError: the interval plan names an unregistered venue ...`)
rather than falling back to Compound's validator. A registry whose declared
format does not match what the resolved venue's validator expects refuses
inside that venue's own check, which for Compound is
`compound_registry.validate_registry`'s existing format check, rather than
being compared against an unrelated venue's pinned bytes. The two refusal
specimens already recorded at `docs/kickoff/1374/evidence/commands.json`
(commands 5 and 6: a registry declaring the Wildcat V2 HooksFactory format,
and the pinned registry with one proxy address changed) fire the same
`usdc-interval: Compound registry format is unknown` and
`usdc-interval: Compound registry bytes do not match the pinned registry`
stderr through the table as they did importing `validate_registry` directly.

## Consequences

Registering a venue means adding one module under `venues/` and one table
entry; no second, hand-maintained list of venue names exists to drift from
it the way `plugins/tabularium/scripts/tabularium.py`'s argparse `choices`
tuple drifted from `tabularium_lib/release_v2.py`'s adapter dict. Compound's
registry pin, format check and gap wording are delegated unedited, so its
release identity and refusals are unchanged. An unregistered venue is a
fail-closed refusal naming that venue, never a silent default to Compound.

Two further decisions this design record covers are expected as additional
sections here, from later steps of this run: preserved provenance declared
per deployment in reviewed code, and the plan format gaining a second
version that carries a subject set.
