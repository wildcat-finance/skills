# ADR-076: Govern real-data demonstrations separately

## Status

Accepted, 2026-09-04.

## Context

The Shoggoth's public front door needs to show what a governed skill can do
with real data without turning an example into a claim the repository cannot
check. Today, examples are scattered across skill prose, fixtures and command
snippets. A reader can run some of them, but there is no common answer to four
basic questions: whether the example uses real inputs, which preserved inputs
it is bound to, what command reproduces it offline, and what public claim that
evidence supports.

The existing `EVOLUTION.md` files cannot absorb that role without changing the
behaviour frontier they already expose to Kronos, Fiat and the marketplace
checks. A root registry would avoid that change, but it would create a second
inventory that every new skill has to remember to update. Editorial prose alone
has neither complete coverage nor a refusal when an example or its source
drifts.

The checked design record at
`docs/shoggoth-public-front-door-design-evidence.json` compares those three
constructions with an adjacent per-skill ledger. Its selection is
`per-skill-demo-ledger`.

## Decision

Every governed skill has one `DEMONSTRATION.md` beside its `EVOLUTION.md`.
Discovery of governed skill directories is the registry: no central list owns
membership, and landing a skill without its demonstration record is a checked
failure.

Each file has two joined parts. Human-readable history records its own
demonstration version, frontier, current result and next job. One closed
`shoggoth-demonstration/v1` object supplies the fields a checker and runner may
trust: skill identity, status, source class and identity, source digests or
chain anchor, network policy, argv arrays, expected observations, public claim
id, non-claim and timeout.

Status has five meanings:

- `real-data`: every material input is a preserved real-world source and the
  registered offline path reproduces the named result;
- `mixed`: a real-world source is present, but the result requires a
  constructed or target-mismatched component;
- `constructed`: the executable example is built wholly from fixtures or model
  records created for it;
- `absent`: no complete executable demonstration exists; and
- `not-applicable`: the owner gives a checked reason that a real-world input
  would not make sense for the skill.

The demonstration frontier is independent of the behaviour frontier. A
behaviour change may satisfy both records in one delivery, but advancing one
does not imply advancement of the other. An explicit `{skill}-demo` queue and
Kronos lane select demonstration work without relabelling a behaviour job.

A public real-data claim binds the exact demonstration-record digest. It passes
only while the current record is `real-data`, its source and command verify, and
the expected observation is reproduced. A downgrade, missing record, changed
digest or failed run removes the claim rather than leaving stale prose green.

## Alternatives

- **Editorial-only.** Keep examples and commands in prose. Rejected because it
  cannot establish complete coverage or refuse a stale real-data claim.
- **One central registry.** Put every skill's state in a root file. Rejected
  because discovery would no longer be the inventory: every new skill would
  need a second owner edit, and the shared file would be a merge hotspot.
- **Embed the fields in `EVOLUTION.md`.** Keep all skill state in one file.
  Rejected because it would change the established evolution grammar and every
  behaviour-frontier digest.

## Consequences

Adding or removing a governed skill changes the discovered demonstration set
without editing a count or registry. Each skill owner has one local place to
advance demonstration evidence, while public prose consumes checked records
instead of becoming an authority of its own.

The repository takes on one new file per governed skill, a strict parser and a
bounded runner. Those files must be kept distinct from `EVOLUTION.md`, and the
status vocabulary becomes a public compatibility boundary. Existing behaviour
frontiers and their digests remain unchanged.

This decision establishes the ownership and evidence model. It does not assert
that any particular skill currently has a real-data demonstration, authorise
network access, or make a public claim before the records and runner pass their
own checks.
