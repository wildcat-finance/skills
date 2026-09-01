# Check that a study or runbook resolves its links before its digest is pinned

Assuming, unless corrected:

1. The starting ref is `main` at `79072bef97360eff130410e2a767d47b936d414d`.
2. Python 3 with the standard library, matching the interpreter the repository
   already pins. No new dependency.
3. The bundled Hypomnema script is the link checker. This run does not write a
   new one.
4. Fiat's held frontier job is [skills#363](https://github.com/wildcat-finance/skills/issues/363),
   about delegation task identities, and is unrelated to this change. This run is
   an ordinary delivery that owes a generation row and must leave the frontier
   revision, digest and held job byte-identical.
5. The reviewed spans in the agent-instruction fixture are the binding
   constraint on where `fiat/SKILL.md` may be edited.

## 1. Problem statement

`done study` and `done runbook` pin an artefact's digest without ever checking
that its links resolve. The controller already runs sibling Protasis checkers
itself, so the omission is not a missing capability; it is a missing call.

What is being built is a refusal: a study or runbook whose links cannot be
resolved does not get a receipt. A working prototype is that the exact citation
specimen the previous run froze into its study is refused before the digest is
pinned, and that the refusal does not depend on where the artefact happens to sit.

Done is checked by: the specimen is refused; a conforming artefact is accepted;
the receipt still records what ran; the whole repository suite stays green; and
Fiat's ledger carries exactly one new generation row.

## 2. Prior art

**The call sites that already exist.** `hexctl.py:5768` runs
`protasis/scripts/design_evidence.py`; `:9401` and `:9428` run
`protasis/scripts/protasis.py`. The controller shelling out to a bundled sibling
checker at receipt time is established behaviour.

**The mechanism to mirror, and its limit.** `hexctl.py:118-120` seeds
`config.skills` with `prose_lint` and `voice`. `done_prose` at `:6688-6694`
takes the set difference of those two ids against the declared `--skills` list
and refuses what is missing. That is a check on a *declaration*, not on a result:
it establishes that an id was named, never that the lint passed. `done study`
records `skills` at `:5989` and `:5994` and enforces nothing.

**Where the defect was found.** The run that landed
[#1070](https://github.com/wildcat-finance/skills/pull/1070) cited the five
discipline skills as `../<skill>/SKILL.md`. Those paths resolve from the Protasis
skill directory the style was copied out of, and from neither location the study
occupies. Hypomnema exits 1 with five `H001` findings. It was caught in step 1
round 1, after the digest was pinned, and `amend study` preserves the receipted
bytes as an exact prefix and appends, so the body could not be corrected. That
run's repair gave the committed copy corrected links and amended the runbook's
step 1 exit to record that the committed study is a corrected rendering rather
than a byte copy. The two differ by design and nothing recomputes one from the
other. Its `## Carried forward` block records this as `study-copy-is-a-rendering`.

**The house convention already in use.** The Anamnesis study committed before
that run cites the same five skills as absolute GitHub URLs pinned to its own
starting commit, and Hypomnema reports it clean. The repository already writes
location-independent citations; nothing required it.

**The last run over this target.** Pull request
[#1040](https://github.com/wildcat-finance/skills/pull/1040) produced `fiat-v5.47.1`
and gated a run on what its issue filed. Its carried-forward records that
`carried_forward_fault` had accepted prose under the heading, and that an item
named in prose and filed nowhere is indistinguishable from one filed twice. The
same shape recurs here: a receipt that accepts a declaration cannot tell a lint
that ran from one that did not.

**Audit records.** The whole-set synopsis currency check exits zero, so the
verified synopses are the reading view. Fiat's own records are the many
`audit/rounds/fiat-*.md` files rather than one log.

## 3. Constraints and non-goals

- Starting ref `79072bef97360eff130410e2a767d47b936d414d`.
- **The reviewed spans bound the edit.** `tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`
  pins `fiat/SKILL.md` at `3bf9cf49` with seven spans whose highest end is byte
  22771. `**Study and runbook.**` sits at 22789 and the imprimatur instruction at
  23183, both outside every span, so no offset shifts and no token count needs
  re-measuring. The `done study --artifact <path> --skills <csv>` row at byte
  18811 is inside `study-phase` (18699-18857) and must stay byte-identical.
- Changing the controller re-pins six digest-bound artefacts in a fixed order.
- Non-goal: a factual claim that no lint reads. The previous run's other prose
  defect was Anamnesis's ADR-004 asserting that Synkrisis admits a producer
  contract it never has. A link checker does not catch that and this run does not
  pretend to.
- Non-goal: widening the audit round's mechanical part to the repository's own
  check graph. That is [#1067](https://github.com/wildcat-finance/skills/issues/1067)
  and a separate change.
- Non-goal: advancing Fiat's frontier. The held job stays byte-identical.

## 4. Design options

Three candidates, scored in `.hexaemeron/design-evidence.json` against the exact
citation specimen the previous run froze, the bundled checker, and the fixture
offsets.

**`declare-only`.** Require the configured link-lint id in `--skills`, exactly as
`done_prose` requires its two. The cheapest change and the one that mirrors an
existing mechanism. It fails three gates because it resolves nothing: it records
that an id was named. The defect this run exists to repair was not a missing
declaration, it was a lint nobody ran.

**`lint-in-place`.** Run the checker on the candidate where it sits. It refuses
the specimen. It fails `verdict-location-independent`: the same bytes earn
different verdicts at different depths, measured with a link that resolves from
one directory and not another. A study is receipted at `.hexaemeron/` and
committed under `plugins/<skill>/docs/`, so a verdict taken at one depth is not a
verdict about the other.

**`require-location-independent`.** Refuse any link that is neither an absolute
URL nor repository-relative, then resolve. The verdict reads the link rather than
the artefact's path, so it holds at both depths. It is the largest of the three
and it is the only one whose answer means the same thing wherever the file ends
up. It also matches what the repository already writes by hand.

**Selection.** `declare-only` fails `catches-observed-defect`,
`verdict-location-independent` and `enforces-result-not-declaration`.
`lint-in-place` fails `verdict-location-independent`.
`require-location-independent` passes every gate and is the sole survivor, so the
rule is `unique-frontier`. The checker exits zero at `design-lock`.

One consequence worth stating: this study is written under the rule it proposes,
and cites its own sources as commit-pinned URLs.

## 5. Risk register seed

```risk-register
frozen-artefact | the study and runbook digests at receipt time | a refusal arrives before the pin, never after, so the artefact is still repairable
reviewed-span-drift | plugins/hexaemeron/skills/fiat/SKILL.md bytes below 22771 | no byte at or below the highest reviewed span end changes, and the fixture's sub-span digests still match
derived-digest-chain | the six artefacts bound to the controller's bytes | every one is re-pinned in the fixed order and the whole repository suite is green afterwards
frontier-drift | plugins/hexaemeron/skills/fiat/EVOLUTION.md | the held job, frontier revision and frontier digest are byte-identical; only a generation row is added
false-refusal | a legal artefact the new rule rejects | a conforming study and runbook are accepted, and the rule's boundary is stated rather than assumed
self-application | this run's own study and runbook | both pass the gate this run adds, before it is receipted
```

## 6. Glossary seeds

- **Reviewed span.** A byte range of a source that the agent-instruction fixture
  binds by digest, with recorded token counts that cannot be regenerated offline.
- **Location-independent link.** A link whose target does not depend on the
  directory the file sits in: an absolute URL, or a path resolved from the
  repository root.
- **Declaration versus result.** A receipt field naming a skill that ran, against
  an exit code proving what it found.
- **Generation row.** A ledger entry for a behaviour change that is not a
  completed frontier advance; it retains the prior revision and digest.

## 7. Sources

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` lines 118-120, 5768, 5989, 6688-6694, 9401, 9428
- `plugins/hexaemeron/skills/fiat/SKILL.md` bytes 18811, 22771, 22789, 23183
- `tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json`
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`
- `plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py`
- Pull requests wildcat-finance/skills#1040 and #1070, and issue #1086
- [the versioning contract](https://github.com/wildcat-finance/skills/blob/79072bef97360eff130410e2a767d47b936d414d/plugins/hexaemeron/skills/VERSIONING.md)

## 8. Signals, and the questions behind them

This run adds a refusal to a command a person runs from a terminal and reads
immediately. There is no unattended process and no on-call question. The one
thing a reader will ask is why a receipt was refused, and the answer is the
checker's own output naming the file and the link.
[Ephoros](https://github.com/wildcat-finance/skills/blob/79072bef97360eff130410e2a767d47b936d414d/plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal must carry; none is owed here.

## 9. Boundaries, per capability

The change makes the controller read one more artefact and run one more bundled
script at receipt time. It opens no network boundary, reads no credential and
adds no dependency. The boundary worth naming is the subprocess: the checker is
resolved from the plugin root by path, as the existing Protasis calls already do,
and the artefact path is one the controller already resolves and bounds.
[Phylax](https://github.com/wildcat-finance/skills/blob/79072bef97360eff130410e2a767d47b936d414d/plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and its controls.

## 10. The budget, or its absence

No performance budget. The measured check latency in the design record is
selection evidence comparing candidates, not a budget this run must hold. The
check runs once per receipt, at tens of milliseconds against a suite already
measured in tens of seconds. [Metron](https://github.com/wildcat-finance/skills/blob/79072bef97360eff130410e2a767d47b936d414d/plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget
carries; none is declared, and nothing here is changed in the name of speed.

## 11. The fail-closed posture

What stops the run: the design checker refusing at a step boundary; the fixture's
sub-span digests failing to match after a re-pin; the ledger row failing the
versioning arithmetic; the frontier tuple changing; the repository suite going
red. A fix follows the guard convention, with the test failing against the parent
commit and passing against the fixed tree, naming its exact specimen.
[Elenchus](https://github.com/wildcat-finance/skills/blob/79072bef97360eff130410e2a767d47b936d414d/plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.

## 12. Decisions and their homes

Two decisions here are expensive to reverse.

- **A study's links must be location-independent.** It changes what the
  controller accepts, so a run that wrote a valid artefact yesterday may be
  refused today. Its home is a new ADR under `plugins/hexaemeron/docs/decisions/`,
  stating the rule, why the verdict must not depend on the artefact's path, and
  what it does not catch.
- **The gate checks a result rather than a declaration.** This departs from the
  `done_prose` precedent in the same file, so the reason belongs beside the rule
  rather than in a commit message.

[Hypomnema](https://github.com/wildcat-finance/skills/blob/79072bef97360eff130410e2a767d47b936d414d/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where
each lives.
