# ADR-035: Bind volunteer selection to an explicit intent handoff

## Status

Accepted, 2026-08-25.

## Context

A volunteer offer can refer to four different subjects: one named issue, the
Wave Atlas issue pool, a governed skill frontier, or one bounded maintenance
output. Natural-language verbs such as “help” and “evolve” do not identify one
of those subjects. Fiat starts after selection, so making Fiat interpret those
verbs would also make it duplicate Atlas and Kronos policy.

Existing GitHub state cannot carry the whole decision. Assignment requires
repository write access. An issue-number branch or linked pull request appears
only after work exists. Each is useful evidence that work has started, but none
records which candidate universe was searched.

This decision is design-only. It ships no selector, comment writer, controller
change, Wave metadata change, or frontier transition. The accepted
[study](../volunteer-intent-study.md) and
[runbook](../volunteer-intent-runbook.md) are its source and delivery records.

## Decision

Use `wildcat-volunteer-intent/v1`, a closed handoff with exactly four intent
kinds: `named-issue`, `wave`, `frontier`, and `maintenance`. The handoff has a
producer side and a consumer side.

Before reading candidates, the launcher stores an immutable request receipt in
producer-owned launch state. It contains the schema, intent kind, producer,
observation time, and SHA-256 digest of the exact request bytes. After selection
or refusal, the producer stores the exact sealed JSON handoff beside that
receipt. The sealed handoff binds the request digest, evidence source and
class, candidate evidence, selected subject or refusal, immutable claim
requirement, consumer, and `promise-machine/v1` boundary. A selected issue uses
`required`; issue-free maintenance uses `none`. This field never asserts that a
claim already exists. Raw prompts, issue bodies, comments, and model reasoning
are excluded.

Fiat accepts only a sealed handoff addressed to `hexaemeron:fiat`. Before
creating run state, it validates the packet and selected subject. An
issue-backed handoff remains insufficient until the separate claim evidence
below is present and current. Missing bytes, changed request digests, copy
mismatches, or later replacement refuse before state creation. Fiat binds the
selected subject; it never selects one.

The selector and evidence depend on the intent kind:

| Intent kind | Selection owner | Required evidence | Selected subject |
| --- | --- | --- | --- |
| `named-issue` | launcher | canonical issue URL plus a normalized singleton snapshot and digest | that issue |
| `wave` | Wave Atlas | source identity, same-read normalized candidate-set digest and count, generation/read metadata | one member of that exact set |
| `frontier` | Kronos | current scoreboard identity, complete candidate digest, held-job digest, maturity and park state | one eligible held job |
| `maintenance` | bounded caller | target repository, one output descriptor, and scope digest | that output |

A canonical named issue has precedence over every lane. Its producer emits
`named-issue`, performs no Wave or frontier search, and requires the selected
URL to equal Fiat's task-issue receipt. A direct Fiat invocation never infers a
lane. A contributor front door may choose `wave` for a bare volunteer offer
only when that policy is stated at that front door before the candidate read.

Every `wave` selection binds the normalized set from the same read that made
the selection. A later `all=true` read cannot supply that evidence. Milestone
titles, including `5b` and `9b`, remain opaque metadata and supply no ordering.
This record creates no periodic, age-based, or count-based census trigger;
Atlas freshness and exclusion evidence remain with issue #505.

An issue-backed handoff requires a public claim before Fiat starts. After the
intent handoff is sealed, the authorised contributor publishes the canonical
early claim: an issue comment whose body contains a
`wildcat-volunteer-claim/v1` marker, the intent-handoff SHA-256 digest, and
`state: active`. GitHub's authenticated comment author is the claimant. Exact
authority to publish the comment and the repository's publication gates are
preconditions; selection grants neither.

After exact comment readback, the producer seals a separate
`wildcat-volunteer-claim-evidence/v1` record. It binds the handoff digest,
comment URL and id, authenticated author, exact comment-body digest, observed
active state, and observation time. Fiat validates the handoff and claim
evidence together, rechecks the live comment, copies the records separately to
`.hexaemeron/volunteer-intent.json` and `.hexaemeron/volunteer-claim.json`, and
binds both SHA-256 digests before creating run state. Missing evidence, a
changed comment, an author or digest mismatch, or a live release refuses
without changing either retained input.

Claims do not expire on a timer. A release is a second structured comment by
the claimant or a maintainer. It carries a
`wildcat-volunteer-claim-release/v1` marker, the original comment URL, the same
intent digest, and `state: released`. The original claim remains active until
that release exists. The release is a later external record and never mutates
the retained intent or claim-evidence bytes. Edited, malformed, or conflicting
claim records require maintainer resolution. Assignment, issue-number branches,
and linked pull requests remain independent safety refusals and corroborate a
valid claim.

Issue-free maintenance is limited to a local, read-only report with one named
repository and output. It need not invoke Fiat or publish a claim. Maintenance
that mutates the repository or publishes externally first requires a named
issue, so `named-issue` precedence applies.

### Worked intent cases

These are design cases, not claims that an executable selector exists.

1. **`named-issue`.** The caller supplies
   `https://github.com/wildcat-finance/skills/issues/447`. The launcher records
   `named-issue` before reading the singleton snapshot, seals that snapshot's
   digest, the same URL and `claim requirement: required`, then obtains the
   structured claim comment and seals its separate readback evidence. Fiat
   accepts both records only when its task-issue receipt is #447.
2. **`wave`.** The documented contributor front door receives a bare volunteer
   offer and records `wave`. Atlas reads one dependency-clear set, stores that
   set's digest, selects one member of it, and seals the member and same-read
   evidence. The selected issue then follows the claim and evidence sequence
   above. Atlas neither chooses nor orders a milestone title.
3. **`frontier`.** The caller supplies `frontier` and one governed skill.
   Kronos records the intent, builds its current scoreboard, and may seal one
   held job only when the ledger says the frontier is neither mature nor
   parked. An issue-backed held job follows the same claim and evidence
   sequence. Fiat consumes that selected job without reranking the scoreboard.
4. **`maintenance`.** The caller names one repository, one read-only report
   path, and a scope digest. The bounded caller seals those values and writes
   only that local report. No issue, public claim, or Fiat run is implied. A
   request to publish the report instead changes the case to `named-issue`.

### Required refusals

| Condition | Decision point | Refusal |
| --- | --- | --- |
| Unknown or absent intent kind | request receipt | Stop before candidate search; never fall through to another lane. |
| Empty Wave set | Atlas selection | Return no selection and create no Fiat state. |
| Stale, mismatched, or split-read Wave evidence | handoff validation | Refuse until Atlas supplies current same-read evidence whose digest contains the selected issue. |
| Pre-existing active or conflicting claim | before claim publication | Refuse until a valid digest-bound release or maintainer resolution exists. |
| Missing, stale, or mismatched claim evidence | Fiat validation | Refuse until a current `wildcat-volunteer-claim-evidence/v1` record and live comment agree. |
| Mature or parked frontier | Kronos selection | Refuse dispatch; this ADR grants no reopening authority. |
| Unbounded maintenance request | request receipt | Refuse until one repository, output, and scope digest bound the work. |
| Missing publication authority | claim publication | Do not post a comment or start Fiat; selection confers no GitHub write authority. |
| Wave-suffix ordering | request receipt | Refuse the ordering request; suffixes are opaque and the Atlas pool owns Wave selection. |

## Alternatives

- Put volunteer parsing and every selector inside Fiat. This offers one command
  but duplicates Atlas and Kronos policy and makes the delivery controller own
  candidate discovery. Rejected because Fiat starts after selection.
- Treat assignment, branches, and pull requests as the handoff. Those surfaces
  expose useful work state, but external contributors cannot assign issues and
  branches appear too late to record preselection intent. Rejected.
- Infer a lane from conversational wording. This has no schema cost, but the
  same words can choose a different universe after routing prose changes and
  cannot be replayed. Rejected.

## Consequences

Selection remains with the component that already owns each candidate
universe, and Fiat receives replayable evidence without becoming a fourth
selector. Named issues have deterministic precedence. Candidate evidence,
selected subject, immutable claim requirement, observed claim evidence, and
controller binding remain separate facts.

The design adds two small record schemas and separate producer and Fiat copies
for intent and claim evidence. Atlas will need to emit a same-read digest,
Kronos will need an adapter, and Fiat will need validators before any command is
live. A contributor or maintainer must release abandoned claims explicitly.
That recovery is slower than automatic expiry, but it cannot silently authorize
duplicate work while a long Fiat run remains active.

Issue #505 remains the decision home for Atlas freshness and dropped-issue
evidence. Any executable selector, GitHub writer, or controller integration
requires its own authorised delivery and tests.
