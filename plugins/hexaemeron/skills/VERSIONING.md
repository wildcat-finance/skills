# Skill evolution contract

Governed first-party marketplace skills use labels of the form
`{skill}-v{evolution}.{generation}.{epoch}`. These labels are not SemVer and
do not rename the skill: a label is built from the skill's own name, not its
plugin's, so Lemma's skill is governed as `lemma`.

This contract governs a skill, not a plugin. A plugin whose skills each hold
their own frontier keeps one ledger per skill. Vendored or third-party skills
are not governed and keep no ledger; inside Hexaemeron that exempts the
bundled Pashov suite (`fizz`, `x-ray`, `solidity-auditor`), which remains
covered by Hexaemeron's own plugin frontier.

History begins at adoption; do not invent or reconstruct versions for work
that predated this contract. The adoption baseline for Fiat, Imprimatur, and
Vulgate is `v1.1.0`. Kronos was introduced after the reset and deliberately
starts at `v0.0.0` to mark it terminal and outside the frontier loop. The
nine top-level plugin skills adopted at whatever version their `SKILL.md`
already declared, so their baselines are not uniform and no baseline value
may be assumed.

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

Each governed skill keeps `EVOLUTION.md` beside its `SKILL.md`. That ledger
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

## What every frontier run owes

Before a frontier job is recorded as done, cold-read and reconcile all mutable
first-party marketplace prose. A frontier advance is the point at which a
skill's behaviour changes, and the documents that describe it to somebody else
are the ones that go stale silently. This holds for every governed skill in the
checkout, whichever plugin it sits in.

It is stated here rather than inside each `Next Fiat job` because a rule copied
into eighteen held targets goes stale in eighteen places, and because amending
a held target is exactly what the discipline above forbids. A ledger whose job
text still spells the obligation out is repeating this clause, not extending
it; the copy retires on its own when a completed frontier run next replaces
that text.

A completed frontier job on Alexandria, Tabularium, Lazarus or Probitas in
`wildcat-finance/skills` also owes the source-coverage refresh in
[wildcat-sources.md](fiat/references/wildcat-sources.md) after its ledger row
lands and before the run's integration merge: a fail-silent contributor check
decides whether the repository-root `SOURCES.md` and its ledger links are
regenerated, and a passing refresh records the non-identifying `labs_sources`
receipt. A failed or unavailable check changes nothing and is not mentioned.
This clause lives here for the same reason as the one above: the obligation
belongs to the frontier run, not to any one held job's text.

A frontier run reads controller state one field at a time and keeps the audit
brief out of its own transcript. Where it needs a single value, use
`hexctl status --field <path>` rather than `hexctl status --json`, which prints
every step, receipt and audit round recorded so far and grows for the whole
run: `--field phase` on resume, `--field observation_run_id` for a companion
observation receipt. Where it delegates an audit round, pass
`hexctl next --brief-out <path>` and hand the subagent that path, so the step
markdown, risk register and design evidence reach the Warden without being
printed into the controller's context first. An unknown field path is refused
rather than answered, so a wrong path fails visibly instead of reading as
absent.

This clause lived here for a different reason from the two above, and that
reason is gone. The instructions that would otherwise carry it are inside
[fiat/SKILL.md](fiat/SKILL.md), which
`tests/fixtures/agent-instruction-v1/manifest.json` binds by whole-file
SHA-256. Editing it used to invalidate a bound measurement record that only
`scripts/agent_instruction.py measure` could reissue, on one machine, so the
clause was written here instead.
[skills#1098](https://github.com/wildcat-finance/skills/issues/1098) closed
that for an edit outside the reviewed span, and `fiat/SKILL.md` now says both
things itself, so an ordinary run gets the saving rather than only a frontier
one. The clause stays because a frontier run owes it explicitly, not because
the controller cannot be told.

A mature frontier can reopen only when a maintainer supplies a new external
failure, requirement, dependency change, or other evidence that invalidates
the closure. Record that compatibility boundary as an epoch entry, with the
new frontier revision and digest, before a new frontier job is allowed.
Enthusiasm, a reworded prompt, or a request to try once more is not reopening
evidence.
