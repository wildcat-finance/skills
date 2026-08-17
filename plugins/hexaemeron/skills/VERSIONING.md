# Skill evolution contract

First-party Hexaemeron skills use labels of the form
`{skill}-v{evolution}.{generation}.{epoch}`. These labels are not SemVer and
do not rename the skill: invocations remain `fiat`, `imprimatur`, `vulgate`,
and `kronos`.

The adoption baseline for Fiat, Imprimatur, and Vulgate is `v1.1.0`. History
begins at adoption; do not invent or reconstruct versions for work that
predated this contract. Kronos was introduced after the reset and deliberately
starts at `v0.0.0`.

- **Evolution** is the first number. Increment it exactly once after a
  completed frontier Fiat job changes that skill's `Next Fiat job`, including
  a frontier-closing job that records `None -- mature`.
- **Generation** is the second number. Increment it for a meaningful change
  to scripts, checks, ordering, decisions, or other behaviour that is not a
  completed frontier advance. Prose-only edits do not count.
- **Epoch** is the third number. Increment it only when a skill crosses a
  compatibility or provenance boundary that makes its earlier lineage an
  unsafe guide: a replacement is absorbed, the execution contract is
  deliberately broken, ownership moves, or the history must be rebuilt from
  incomplete evidence. Do not use it as a patch number. The other counters do
  not reset.

Each first-party skill keeps `EVOLUTION.md` beside its `SKILL.md`. That ledger
is the authority for the current label, frontier status, frontier revision,
next job, and history. The numeric version in `SKILL.md` frontmatter must
match it. Each history row also stores the SHA-256 of this exact UTF-8 line,
including its final newline:

```text
{status}|{frontier revision}|{current frontier}|{next Fiat job}
```

## Frontier discipline

`Next Fiat job` is a held target, not a rolling writing prompt.

- A generation entry must retain the prior frontier revision and frontier
  digest byte for byte.
- A generation may clarify surrounding explanation to reflect earlier
  changes, but it must not change the target or its acceptance condition.
- Outside an evidenced epoch reopening, only a completed frontier Fiat job
  may replace the target and increment the evolution counter.
- At the end of a frontier job, judge whether another pass has a concrete,
  evidenced chance of material improvement. Style alternatives, speculative
  extensions, another rewrite, or a different implementation of already met
  acceptance conditions do not qualify.
- If no material improvement remains, set the status to `mature`, set the
  next job to `None -- mature`, record the evidence, and stop. Do not suggest,
  start, or resume another Fiat frontier run for that skill.

A mature frontier can reopen only when a maintainer supplies a new external
failure, requirement, dependency change, or other evidence that invalidates
the closure. Record that compatibility boundary as an epoch entry, with the
new frontier revision and digest, before a new frontier job is allowed.
Enthusiasm, a reworded prompt, or a request to try once more is not reopening
evidence.
