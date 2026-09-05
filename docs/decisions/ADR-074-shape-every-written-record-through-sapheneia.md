# ADR-074: Shape every written record through Sapheneia

## Status

Accepted, 2026-09-03.

## Context

[ADR-017](ADR-017-gate-durable-agent-prose.md) gave Sapheneia one bounded
operation for three surfaces: an agent-authored audit record, a GitHub issue
title and body, and a GitHub issue comment. Everything else an agent writes
down was left to whichever workflow happened to own it.

The gap is visible in what those workflows produce. A pull request body, a
study, a runbook, a decision record, a README and a commit message all carry
the same failure the three named surfaces were gated against: process
narration that says nothing, restatement of what the reader already has, and
hedges that carry no information. A reader paying attention to twelve of these
per run pays for every unnecessary sentence in all of them.

Two things stopped the earlier decision going wider. Enumerating surfaces one
at a time meant each new kind of record waited for its own amendment. And some
bytes an agent writes are not prose it may shorten: a generated installation
copy, a receipt, a digest-bound document and a fixed-template report are fixed
by their own owner, and shortening one breaks the check that binds it.

## Decision

`sapheneia-durable-record-shape` governs every piece of prose an agent writes
to a file or publishes to a host, before it is written or published. The
subject is defined rather than enumerated: any agent-authored prose that
leaves the transcript. Audit prose, issue titles and bodies, issue and pull
request comments, pull request bodies, repository documents and commit
messages are named as instances, and the list does not close.

The operation carries a stated objective: the shortest candidate that still
carries the whole protected evidence inventory and the required host
structure. Cutting stops where one more removal would drop or weaken an
inventory item. Length is the only thing the pass trades.

Four subjects sit outside it. Bytes fixed by a generator, digest, manifest or
another skill's fixed template stay as their owner produced them. A record
already written stays as it was written, because the pass is prospective. Code,
data and configuration values are not its subject. A quotation keeps the
wording of whoever wrote it.

The repository sequence in `AGENTS.md` moves from issues and comments to every
written record under the heading `## Written-record publication`. Its steps are
unchanged: freeze the structure and inventory, apply the Sapheneia pass, run
Imprimatur, apply Vulgate, run Imprimatur again on the exact publishable bytes,
and for an issue body run `hexctl issue-check --body` on those bytes.

## Alternatives

- **Enumerate the new surfaces and stop there.** Adding pull requests and
  documents to a closed list of five leaves the sixth kind of record waiting
  for another decision. The failure ADR-017 left open is the enumeration, not
  the length of the list.
- **Fold the objective into Brevitas.** Brevitas already governs volume and
  structure for engineering prose, and it deliberately exempts code comments,
  commit messages and completeness-oriented specifications. Moving the parity
  obligation there would either break those exemptions or leave the surfaces
  Brevitas exempts ungoverned.
- **Make the pass rewrite existing records too.** Audit records are append-only
  and byte-pinned, and historical issues carry the context somebody replied to.
  A retrospective sweep would change evidence.
- **Add a second promise for the new surfaces.** Two promises with the same
  evidence, boundary and refusals would drift, and every receipt naming the
  first would need to say which one it meant.

## Consequences

One contract now covers what an agent says and what it writes down. The
receipts that already name `sapheneia:sapheneia` keep their meaning, because
the promise identifier and its five-step check are unchanged; what changed is
the range of subjects it accepts.

The pass stays model-checked. Imprimatur reads the exact bytes it is given,
`hexctl issue-check` reads an issue body's shape, and neither can tell whether
a candidate lost a qualification. No check establishes that a candidate is the
shortest form available, and the promise says so. An executable pre-send
checker remains open work under
[skills#421](https://github.com/wildcat-finance/skills/issues/421).
