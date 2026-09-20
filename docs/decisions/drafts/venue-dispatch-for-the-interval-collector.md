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

One further decision this design record covers is recorded below:
[preserved provenance declared per deployment](#preserved-provenance-is-declared-per-deployment-in-reviewed-code).

## Plan format: a second version carries a subject set

### Context

Every function this collector used to validate a plan, filter provider
requests and attribute preserved logs assumed exactly one proxy address.
`validate_plan`'s required field set named `proxy`. `shard_requests` filtered
`eth_getLogs` and `trace_filter` by that one address. `proxy_log_positions`
checked every preserved log against it before `attribute_logs` walked one
epoch table over the whole interval for it.
[#1731](https://github.com/wildcat-finance/skills/issues/1731) needs a plan
that can name many subjects at once. The Wildcat V1 and V2 estates that later
steps of this run register are each one venue with many deployed contracts
rather than one proxy, and every preserved log has to reach the epoch table
of its own subject rather than a shared one.

### Decision

`alexandria-interval-plan/v2` replaces the single `proxy` field with a
non-empty, duplicate-free `subjects` array
(`plugins/alexandria/schemas/interval-plan-v2.schema.json`). A v1 plan
carrying `proxy` still validates unchanged and still means exactly one
subject, because `validate_plan` compares the plan's exact key set against
whichever of the two required sets it matches before checking anything
else. `shard_requests` filters `eth_getLogs`'s `address` and
`trace_filter`'s `toAddress` by the whole declared array for a v2 plan. A
v1 plan keeps one unwrapped `address` and a one-element `toAddress` list,
exactly as before.

`proxy_log_positions` accepts a log from any address in the declared set (a
plain string for v1, any non-empty collection for v2) and tags each row
with the subject that emitted it. A v1 call's rows keep their original
shape, with no added field. `attribute_logs` groups a v2 call's rows by
their own subject and walks each group against that subject's own epoch
table alone, so two subjects that emit in the same block and the same
transaction each reach their own epoch untouched by the other's presence.
`validate_epochs` and `validate_block_epochs` take either a flat list (v1,
tiling the whole interval as before) or a `{subject: [epoch, ...]}` table
(v2). Each subject's own list tiles from its own first in-interval position
or block through the interval's end. `MAX_EPOCHS` bounds each subject's own
list rather than an estate-wide sum, and a subject whose extent starts
after the interval end carries no key at all rather than an empty list. A
duplicate address in a plan's declared `subjects` refuses when the plan is
validated.

No venue registers a multi-subject plan yet; that work belongs to later
steps of [#1731](https://github.com/wildcat-finance/skills/issues/1731). The
Compound v3 path therefore stays on `proxy` unedited, and its demonstration
still builds and checks byte for byte.

### Consequences

A later step's venue module can declare `subjects` instead of `proxy` and
reach the same collector, builder and checker with no further change to
this format. Reversing the plan-format branch would break every plan a
multi-subject venue has already written under it. The generic machinery is
proven here against synthetic subject sets at the V2 estate's declared
cardinality of 137 and the V1 estate's 16
(`docs/kickoff/1359/targets.json`'s `wildcat-v2-ethereum-mainnet` and
`wildcat-v1-ethereum-mainnet` rows), not against either estate's real
registry. That remains later steps' work.

## Preserved provenance is declared per deployment, in reviewed code

### Context

A Wildcat release has to be testable offline before any collection and after
one. Its tests therefore collect from a constructed transport state,
`plugins/alexandria/tests/fixtures/wildcat-interval-transport.json`, whose
hashes, logs and code were written rather than observed. The registry beside
it is real, generated from merged records. Nothing in a release's bytes
separates a constructed journal from a collected one, so a constructed release
could pass as preserved chain evidence.
[#1442](https://github.com/wildcat-finance/skills/issues/1442) carries the
wider concern, release labels that no test holds. This section answers it for
the one label this run adds, and that issue stays open.

A plan field could not carry the distinction, because whoever writes the
staging tree also writes the plan. A per-venue flag could not either: once a
real capture lands, the flag flips for the whole venue and the fixture
inherits it.

### Decision

Each venue module names, in reviewed code, the set of plan `deployment` names
whose staging it admits as preserved. For Wildcat V2 that is
`PRESERVED_DEPLOYMENTS` in
`plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v2.py`, and it is
empty. Every other deployment name under the venue carries the
constructed-staging gap on every evidence scope, through the venue's
`evidence_gaps` contribution. `check` re-derives that contribution from the
release's own plan, registry and preserved logs. It refuses a release whose
coverage drops a sentence the venue owes.

The granularity is the deployment name, not the venue. Admitting one collected
interval therefore leaves every fixture, under its own name, still labelled.

`compound-v3` contributes no such gap, and its releases are unchanged byte for
byte. Its two demonstrations predate this decision.

### Consequences

Admitting a deployment is a reviewed change to one constant. No plan field,
registry field or operator document can add a name, and a plan carrying an
unknown field refuses when it is validated.

Admitting a name changes what every later build under that name claims. A
constructed tree that reused an admitted name would build without the label.
A name is therefore admitted only for staging that was collected, and a
fixture never takes an admitted name. A release built before its name was
admitted still carries the gap, and `check` accepts a gap the venue no longer
owes.

The same contribution carries what the venue's registry could not establish.
It names the one subject with no recorded creation block, each subject
deployed after the interval's end, and each disagreement between the preserved
`MarketDeployed` logs and the registry's declared markets. Each kind that
grows with the subject set lists 16 by name and then counts the rest, because
a capture holds at most 256 gap sentences.

## The subject receipt writes its epoch table as one list

### Context

`alexandria-interval-receipt/v3` first wrote `epochs` as an object keyed by
subject. A coverage selector has to resolve to a list, so that shape needed
one coverage collection per subject, and a capture holds at most 256
collections. A release was therefore capped at 256 in-interval subjects while
the plan admits 4096, and the build refused only after a whole collection.
`docs/kickoff/1359/targets.json` admits targets whose Ethereum contract counts
reach and pass that cap. No v3 receipt had been released when this was found.

### Decision

The receipt writes `epochs` as one list of `{"epochs": [...], "subject":
"<address>"}` rows in strictly ascending subject order, counted by one
collection at `/epochs`. `subject_epoch_rows` and `subject_epoch_table` in
`alexandria_lib/interval.py` convert between that list and the
`{subject: [epoch, ...]}` table every validator reads, so the Step 3
primitives are unchanged.

Raising the collection limit lost: it bounds every release already built, and
any fixed limit would still sit below the plan's. One collection per shard of
subjects lost: it keeps a growing list and adds a second split to explain.

### Consequences

The plan's subject limit is the bound on a release's subjects. The row order
is part of the format: `check` refuses a repeated subject and rows out of
order, so one table has one encoding. Once Steps 9 and 10 release captures in
this format its shape is fixed, and a later change is a v4.

## A subject with no recorded creation block opens where its code is first read

### Context

One Wildcat V2 subject, the collateral init-code storage, has no creation
block in the merged records, and other venues' registries will carry such
subjects too. The first rule opened its epoch at the interval's start. The
run's runbook records a read of the hosted transport on 2026-09-20: no code
for that subject at block 21,866,550, the start chosen for the V2 interval,
and 9,581 bytes of code from block 23,167,810. The first rule therefore
refused that interval, and did so in the opening phase, after every shard.

### Decision

Such a subject opens at the interval's start when it has runtime code there.
Otherwise the collector bisects between the interval's start and end for an
adjacent pair of blocks, empty code at one and runtime code at the next, and
opens the epoch at the second. It makes those reads before any shard, and
refuses there when the interval's end has no code either. The receipt's
`first_code` rows name the pair and the opening, and every evidence scope's
gap says which applied.

Dropping the subject lost: Step 9 requires all 137. Shortening the interval to
the subject's first code lost 1,301,260 blocks of every other subject. Writing
the observed block into the registry lost: the registry is generated from
merged records and pinned, and an observed block is not a recorded one.

### Consequences

An observed block is a claim about two reads, not about creation: code
destroyed before the interval, or between two blocks the bisection did not
read, is not seen. A checkpoint cannot commit an opening read while a shard is
uncollected, so the probes are held in memory and journaled after the last
shard; a run stopped among the shards asks them again. A subject with a
recorded block is never probed, and empty code at that block refuses as a
wrong registry.

## The two estates' shared subjects are attributed to both, never merged

### Context

`WildcatArchController` (`0xfeb516d9d946dd487a9346f6fee11f40c6945ee4`) and
`WildcatSanctionsSentinel` (`0x437e0551892c2c9b06d3ffd248fe60572e08cd1a`) were
each deployed once, at block 18,686,645, and are read by both the V1 and the
V2 estate: the V1 controller factory and the V2 HooksFactory both register
against the one arch controller, and both estates' markets read the one
sentinel's `chainalysisSanctionsList()`. Neither is a V1-only or a V2-only
contract, so a registry that declared it for one estate and not the other
would lose that estate's own registration events, and a single shared
registry entry would need a venue field no other subject carries.

### Decision

Both venues' registries declare both addresses as their own subject, each
under the `registry` and `sanctions-sentinel` roles its own generator already
uses, with its own code digest, deployment block and (for V1) source commit
read independently by that venue's generator. `wildcat_registry.SHARED_SUBJECTS`
names the two addresses once, and `wildcat_registry.validate_shared_subjects`
checks, in reviewed code, that the V1 and V2 registries' declared subject sets
intersect in exactly that pair; a third address either registry starts
declaring in common with the other fails that check rather than silently
widening the intersection. The union of the two declared sets is 151
addresses (16 + 137 − 2).

No new attribution path is added for the shared pair. Each venue's plan
declares its own subject set, and `proxy_log_positions` (`alexandria_lib/
interval.py`) already refuses a preserved log whose emitting address is not
one of the plan's own declared subjects; a V2-only subject's log can no more
be attributed under a V1 collection than under any other estate that never
declared it, and the reverse holds for a V1-only subject under V2. A log the
shared pair itself emits is attributed independently by each estate's own
collection, against that estate's own epoch table, because each estate
legitimately declares the address as its own subject.

### Consequences

Adding a third venue that also reads the arch controller or the sentinel
means widening `SHARED_SUBJECTS` and its reviewed check in the same change
that registers the venue, not a silent set union computed from whichever
registries happen to exist. Two registries independently re-deriving the same
address's code digest and deployment block from their own merged records
duplicates that work rather than sharing a cached read, which is the price of
keeping each venue's registry generator self-contained and independently
pinned by its own digest constant.

## The V1 checkout ambiguity is a recorded caveat, never a coverage gap

### Context

Fourteen of the sixteen Wildcat V1 subjects match the wildcat-protocol
repository at commit `da74452aa7d1a0f024d99efd22cc6d950a8116b7`, but the
row's own `source.equivalent_commits` names four further commits
(`ebb6cecc4e72ea90187bc10006f8aa35d7ae2da9`,
`e9552f0e8a093e214dd69947dc689023df09ff20`,
`e962bf37866483a3573016a3087331c5de9f0929`,
`016d0658d6d442b8f42e3bb68f01fae43c150307`) whose in-tree Sourcify sources are
byte-identical to that commit's. The controller factory deployed about an
hour after the license-header commit `6164ddd4` and its main-merge
`d46ecb80`, both of which carry post-rewrite blobs the deployed bytecode does
not match, so the deployer used a checkout that was not main's tip at deploy
time, and none of the five candidates can be distinguished from on-chain
evidence. This is not an absent identity: a source commit is established,
just not uniquely among five byte-identical checkouts.

### Decision

The registry records the row's recorded commit on every affected entry, and
carries the four equivalent commits and the row's own `equivalence_note`
alongside it as a caveat on an established identity. `validate_v1_registry`
refuses a document that names one of the four equivalent commits as an
entry's own `source_commit` in place of the recorded one
(`wildcat_registry._validate_v1_shape`), so a release cannot silently narrow
the ambiguity to a single guessed checkout. This is deliberately not modelled
as a source-identity coverage gap: unlike a subject whose row establishes no
commit at all (the mechanism `wildcat_v1._missing_source_commit_gap` still
carries for that case, though no real V1 subject falls into it), every one of
the fourteen subjects here has an established, sourced identity; what is
undetermined is only which of five byte-identical checkouts the deployer
used, and collapsing that into a "no identity" gap would misstate what the
record actually shows.

### Consequences

Every later release under either venue inherits this convention: an
unresolvable checkout among byte-identical commits is a caveat next to an
established identity, not a gap that a `coverage` reader would read as "we do
not know the source." A future source-match record that resolves the
ambiguity (for example, by dating the deployment transaction against each
candidate's tree more precisely) replaces the equivalence note rather than
this decision, and a genuinely sourceless subject still routes through the
gap mechanism this decision leaves untouched.
