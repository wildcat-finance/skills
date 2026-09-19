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

One further decision this design record covers is expected as an additional
section here, from a later step of this run: preserved provenance declared
per deployment in reviewed code.

## Plan format: a second version carries a subject set

### Context

Every function this collector used to validate a plan, filter provider
requests and attribute preserved logs assumed exactly one proxy address:
`validate_plan`'s required field set named `proxy`, `shard_requests` filtered
`eth_getLogs` and `trace_filter` by that one address, and
`proxy_log_positions` checked every preserved log against it before
`attribute_logs` walked one epoch table over the whole interval for it.
[#1731](https://github.com/wildcat-finance/skills/issues/1731) needs a plan
that can name many subjects at once, because the Wildcat V1 and V2 estates
later steps of this run register are each one venue with many deployed
contracts rather than one proxy, and every preserved log has to reach the
epoch table of its own subject rather than a shared one.

### Decision

`alexandria-interval-plan/v2` replaces the single `proxy` field with a
non-empty, duplicate-free `subjects` array
(`plugins/alexandria/schemas/interval-plan-v2.schema.json`); a v1 plan
carrying `proxy` still validates unchanged and still means exactly one
subject, because `validate_plan` compares the plan's exact key set against
whichever of the two required sets it matches before checking anything
else. `shard_requests` filters `eth_getLogs`'s `address` and
`trace_filter`'s `toAddress` by the whole declared array for a v2 plan and
by the one address, unwrapped, for a v1 plan, exactly as before.

`proxy_log_positions` accepts a log from any address in the declared set (a
plain string for v1, any non-empty collection for v2) and tags each row
with the subject that emitted it; a v1 call's rows keep their original
shape, with no added field. `attribute_logs` groups a v2 call's rows by
their own subject and walks each group against that subject's own epoch
table alone, so two subjects that emit in the same block and the same
transaction each reach their own epoch untouched by the other's presence.
`validate_epochs` and `validate_block_epochs` take either a flat list (v1,
tiling the whole interval as before) or a `{subject: [epoch, ...]}` table
(v2): each subject's own list tiles from its own first in-interval position
or block through the interval's end, `MAX_EPOCHS` bounds each subject's own
list rather than an estate-wide sum, and a subject whose extent starts
after the interval end carries no key at all rather than an empty list. A
duplicate address in a plan's declared `subjects` refuses when the plan is
validated.

No venue registers a multi-subject plan yet -- that is later steps of
[#1731](https://github.com/wildcat-finance/skills/issues/1731)'s work -- so
the Compound v3 path stays on `proxy` unedited and its demonstration still
builds and checks byte for byte.

### Consequences

A later step's venue module can declare `subjects` instead of `proxy` and
reach the same collector, builder and checker with no further change to
this format; reversing the plan-format branch would break every plan a
multi-subject venue has already written under it. The generic machinery is
proven here against synthetic subject sets at the V2 estate's declared
cardinality of 137 and the V1 estate's 16
(`docs/kickoff/1359/targets.json`'s `wildcat-v2-ethereum-mainnet` and
`wildcat-v1-ethereum-mainnet` rows), not against either estate's real
registry, which remains later steps' work.
