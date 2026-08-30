# Grade the router corpus from a driver rather than by hand

## 1. Problem statement

`tests/test_router_selection.py` binds a recorded grading run to
`corpus_sha256`. Adding a case moves that digest, so the recorded run stops
describing the corpus and the suite goes red. The documented repair is a
regrade. Nothing in the repository performs one.

This run builds the driver. It is for whoever adds the next plugin, who today
inherits a red suite and a manual procedure nobody has written down.

A working prototype is: a committed tool that emits one prompt file per corpus
case, ingests one answer per case, tallies them against `expect`, and writes a
`runs` block the existing checker accepts. Proved by taking the corpus on disk,
emitting its packet, feeding back the 38 answers this run already recorded, and
watching `python3 -m unittest tests.test_router_selection` stay green with a
block the driver wrote rather than a hand-edited one.

## 2. Prior art

The whole-set synopsis currency check exits 0 from the target root, so a
committed `AUDIT_SYNOPSIS.md` is the normal reading view here. Sources read:
`audit/rounds/fiat-499-grade-router-selection-not-just-resolution.synopsis.md`
(synopsis, current) and the live modules named below (source).

The two merged pull requests that last changed this surface:

**[#851](https://github.com/wildcat-finance/skills/pull/851)**, merged
`d1ca7ba5`, added `RS-38` for the Homologia router row and recorded a regrade
by hand. Its carried-forward items, each answered here:

- The regrade was performed by dispatching 38 fresh contexts by hand. That is
  the procedure this run automates. Carried forward as this run's content.
- `RS-34` changed answer between the 2026-08-28 and 2026-08-30 runs, and the
  recorded evidence cannot say whether that is model variance or an effect of
  the added router row, because the run block records nothing about the tree it
  graded. Stated non-goal here, with its reason in item 3.
- `RS-33` reproduced its earlier failure exactly. No action owed.

**[#697](https://github.com/wildcat-finance/skills/pull/697)**, the issue 499
delivery that built this surface. Its carried-forward items that bear on this
run:

- "The study's re-run recipe names a `--requests` flag on
  `tests/emit_router_selection_report.py` that no committed tool provides and
  that must stay unbuilt, since it would make the reporter echo request text."
  Carried forward as content, and item 4 turns it into the design constraint
  that separates the reporter from the driver.
- "The corpus binds its cases to prose the wider repository owns and edits
  freely, and integrating this run proved the cost." Carried forward as the
  reason this run exists.
- "The schema has no field for a case a grading run could not answer, so
  `passed` plus `failed` equalling `cases` is forced by the schema rather than
  by the guard." Named as a boundary in item 3; the driver must therefore
  refuse a missing answer rather than invent one.
- "`load_corpus`'s `OSError` branch is the one refusal site with no guard
  driving it." Untouched: this run adds a module and does not widen that one.

The audit record carries the decisive precedent. The first recorded grading,
commit `da2c2312`, scored 36 of 36 under template `3f6904e6` and was refused:
that template's response-format example "named the real labels `Q01` and `Q02`
and gave the outcome class of both", and the run "presented all 36 requests to
one batched context rather than one per request as the study's recipe and the
receipted exit both specify". Round 1 recorded those as `S3-R1-02` and
`S3-R1-03` and the controller ruled a regrade. The replacement, under template
`af3cb4c8`, removed both aids and scored 35 of 36.

Two rules follow from that, and they are the reason this is a driver and not a
convenience script. One context per request, never a batch. No aid in the
prompt that narrows the answer, including a worked example naming real labels.

Outside this repository: nothing. The corpus, the template and the checker are
local, and no packaged evaluation harness is in the dependency set.

## 3. Constraints and non-goals

Starting ref `48b063c597ebf6aa1978c3c7048ba928d27e7fb5` on `main`. Python at
the pin in `.python-version`, standard library only; the repository adds no
dependency for this. No network call from any committed module or test.

Ruled out by the prior art rather than by preference: batching requests into
one context, and any prompt aid that names outcome classes or real case labels.

Deferred past the prototype:

- **Adding a tree or commit digest to the run block.** It would make an
  `RS-34`-shaped change attributable, and it is the right answer to a real gap.
  It is also a schema change that invalidates every recorded block at once, and
  the issue that raised it says it is not decided there. Doing both in one run
  couples a tool nobody has used yet to a migration of the only evidence the
  surface has. A stated non-goal, not an oversight.
- **Calling a model.** The driver stops at the boundary in both directions. The
  contexts are supplied by whoever runs it.
- **Grading anything but router selection.** The corpus format is local to this
  surface.

## 4. Design options

**A. A flag on `emit_router_selection_report.py`.** Rejected, and the rejection
is inherited rather than reasoned afresh: #697 established that a reporter flag
carrying request text is a route from the report into a graded context. The
reporter's own docstring says the same. Adding `--requests` would undo a
decision the audit already made.

**B. A driver that calls a model directly.** Rejected. It puts a network client
and a provider credential into a repository that has neither, makes the tests
unrunnable offline, and makes the grading unreproducible by anyone without that
provider. It also buys nothing the operator cannot already do: the contexts
exist wherever the driver runs.

**C. A driver that emits a packet and ingests answers.** Chosen. `emit` writes
one prompt file per case, each the pinned template with one request
substituted, plus a manifest naming the corpus digest and the case ids.
`tally` reads an answers file, checks it against the manifest, scores it
against `expect`, and writes the `runs` block. The model step happens between
the two, wherever there are fresh contexts, and the driver never sees a model.

The trade: the operator still supplies the contexts, so this does not make a
regrade free. What it removes is the part that was error-prone rather than the
part that was slow. It also keeps the whole thing offline and testable, which B
does not, and it never puts request text into a report, which A does.

**D. A driver that also spawns contexts through a pluggable adapter.** Rejected
as premature. One adapter would be written, it would be the one this operator
uses, and the interface would be shaped by that single case. C's answers file
is already the interface, and it is a file rather than an API.

## 5. Risk register seed

The dangerous direction is outward: a field that must not reach a graded
context reaching one through the emitted packet. `expect`, `deciding_sentence`
and `not_established` all sit in the same case object as `request`, so the
emitter is one careless serialisation away from leaking the answer it is about
to grade. The guard is a positive allowlist rather than a denylist, and a test
that reads every emitted byte back.

The second direction is the tally accepting an answers file that does not
correspond to the packet it claims to answer, which would record a score about
nothing.

```risk-register
prompt-leak | the emitted prompt files | no emitted byte contains any field of a case other than its request, checked over every case
answer-binding | the answers file the tally reads | a tally refuses unless the manifest digest matches the corpus on disk and the answer id set equals the case id set exactly
missing-answer | a case the operator could not answer | the tally refuses rather than scoring it, because the schema has no field for an unanswered case
answer-shape | one answer line | only a canonical name the repository declares or one of the two refusal forms is accepted, and anything else refuses by name
packet-write | the output directory during emit | a refused emit leaves no partially written packet a later tally would read as complete
corpus-drift | the corpus between emit and tally | the manifest pins the corpus digest and the tally recomputes it, so a corpus edited in between refuses
```

## 6. Glossary seeds

- **Packet.** The directory `emit` writes: one prompt file per case and one
  manifest.
- **Answers file.** What the operator returns: one case id and one answer line
  each.
- **Run block.** The `runs` entry the checker already validates.
- **Graded context.** A context that receives one prompt and returns one line,
  having seen no expected answer.

## 7. Sources

- `tests/test_router_selection.py`, the checker and its guards.
- `tests/emit_router_selection_report.py`, the reporter, and its docstring on
  what must not reach a graded context.
- `tests/fixtures/router-selection/cases.json` and `prompt-template.txt`.
- `docs/promise-machine/router-selection-v1.md`, `## Recovery` and
  `## Digest scope`.
- `audit/rounds/fiat-499-grade-router-selection-not-just-resolution.synopsis.md`.
- Pull requests [#697](https://github.com/wildcat-finance/skills/pull/697) and
  [#851](https://github.com/wildcat-finance/skills/pull/851).

## 8. Signals, and the questions behind them

The driver is a command someone runs from a terminal and watches. It has no
unattended mode and no on-call question, so ephoros's contract is answered with
none, and the reason is that nothing here runs without a person waiting for it.

What it does owe is a legible refusal, since every risk in item 5 is a refusal
path. Each refusal names the case or the field and what was expected, in the
style the corpus checker already uses.

## 9. Boundaries, per capability

- **Reads the corpus.** A committed fixture at a fixed constant path, as
  `load_corpus` already does. No caller-supplied path, so no traversal surface.
- **Writes a packet directory.** Operator-supplied path. Worth taking because
  the packet is transient and belongs outside the repository. Closed by
  refusing an existing non-empty directory and by writing each file once,
  so a refused emit leaves nothing a tally would misread.
- **Reads an answers file.** Operator-supplied path and the only untrusted
  input in the run. Closed by the shape and binding rules in item 5: bounded
  read, closed answer vocabulary, exact id-set equality, manifest digest match.
- **Writes the corpus back.** The tally rewrites `runs` in place. Closed by
  rewriting only that key and by leaving `cases` and `pairs` byte-identical,
  checked by a test.

No subprocess, no network, no credential, no long-running process to kill
halfway. phylax's contract is answered by that list.

## 10. The budget, or its absence

None. The driver reads one fixture and writes 38 small files; the cost is
dominated by the model contexts, which are outside it. metron's contract is
answered with none, and the reason is that no step here is speed-motivated and
no number would change a decision.

## 11. The fail-closed posture

Every check in item 5 stops the run rather than degrading. A tally that cannot
bind its answers to its packet writes nothing, because a score recorded against
the wrong corpus is worse than no score.

A fix follows elenchus's guard rule: the guard fails without the fix. For this
surface that means a hostile fixture per refusal path, the way
`GUARD_CORPORA` already holds one per fault in the checker.

## 12. Decisions and their homes

One decision is expensive to reverse: that the driver stops at the model
boundary in both directions rather than calling a provider. It settles what
this repository will and will not automate about grading, and reversing it
later means taking on a credential and a network path. It earns a record at
`docs/decisions/ADR-<next>-grade-the-router-corpus-from-a-driver.md`, naming
option B and option D as the rejected alternatives.

The rejection of a reporter flag is not a new decision; it was made in #697 and
is cited here rather than restated.
