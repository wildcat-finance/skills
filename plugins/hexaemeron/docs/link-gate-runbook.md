# Runbook: check that a study or runbook resolves its links before its digest is pinned

Derived from [the study](https://github.com/wildcat-finance/skills/blob/79072bef97360eff130410e2a767d47b936d414d/plugins/hexaemeron/docs/link-gate-study.md). The
selected design is `require-location-independent`: refuse any link that is
neither an absolute URL nor repository-relative, then resolve, so the verdict
reads the link rather than the artefact's path.

Three steps. Step 1 commits the design records and changes no behaviour. Step 2
adds the rule, wires it into both receipts, records the decision, and pays the
derived-digest chain in the same commit, because the controller's bytes are
pinned by `INTEGRATED_CONTROLLER_SHA256` and the suite goes red the moment they
move. Step 3 advances the ledger, reconciles the prose and demonstrates.

Every step runs the repository suite at its exit. That is not decoration: the run
that produced this change was receipted green on plugin suites alone and was red
on hosted CI, which is [#1067](https://github.com/wildcat-finance/skills/issues/1067).

```design-lock
schema | protasis-design-evidence/v1
sha256 | 52c842bbd391004007c60e41eb75c98bc9c3330ede60d3ee0a72fdd33e35df94
candidate | require-location-independent
```

## Step 1: Commit the design records

**Goal.** Land the study, runbook, design record and its eighteen resolved
reports under `plugins/hexaemeron/docs/`, with no behaviour changed.

**Entry.** Exact commit `79072bef97360eff130410e2a767d47b936d414d` on the run
branch, with the receipted `.hexaemeron/` artefacts in place;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:1`
exits zero.

**Exit.** `plugins/hexaemeron/docs/link-gate-study.md` and
`plugins/hexaemeron/docs/link-gate-runbook.md` are byte-identical to the
receipted `.hexaemeron/` copies; the design record and its reports are committed
under `plugins/hexaemeron/docs/link-gate/`; both committed documents pass the
bundled link check at their committed depth and at one deeper depth with the same
verdict; `python3 -m unittest discover -t . -s tests` is green; the Horos
boundary is rescanned after staging; and
`design_evidence.py --transition step:2` exits zero.

**Files.** Create `plugins/hexaemeron/docs/link-gate-study.md`,
`plugins/hexaemeron/docs/link-gate-runbook.md`,
`plugins/hexaemeron/docs/link-gate/design-evidence.json`,
`plugins/hexaemeron/docs/link-gate/reports/` (eighteen report objects) and
`plugins/hexaemeron/tests/test_link_gate_records.py`. Change
`.horos/boundary.json`.

**Tests.** Add `plugins/hexaemeron/tests/test_link_gate_records.py`: the committed
design record declares `protasis-design-evidence/v1`, names three candidates and
six criteria covering all five concerns, selects `require-location-independent`
under `unique-frontier`, every result cell names a report whose recorded SHA-256
matches the committed bytes, and neither committed document carries a link that
is relative to its own file. The audit runner contract is
`cd plugins/hexaemeron && python3 tests/run_tests.py --elenchus-report {report} --jobs 8`,
its format is the runner's Elenchus-compatible report, and Warden writes
`.hexaemeron/elenchus/hexaemeron-step-1.json`. Also run the root suite and
`git diff --check`. Expected new focused tests: 5.

**Disciplines.** phylax: none, the step adds documents and a test and opens no
boundary. ephoros: none, nothing here runs unattended. metron: none, no
performance claim. elenchus: none, no failure in hand at entry. hypomnema: the
committed location of the design records is settled here rather than left
implicit.

## Step 2: Add the link rule, wire it into both receipts, and pay the digest chain

**Goal.** Refuse a study or runbook whose links are not location-independent, or
do not resolve, before its digest is pinned; record the decision; and re-pin every
artefact bound to the controller's bytes.

**Entry.** Step 1's exit state; `design_evidence.py --transition step:2` exits
zero.

**Exit.** `hexctl done study` and `hexctl done runbook` refuse an artefact
carrying a link relative to its own file, and refuse one whose repository-relative
or absolute-path link does not resolve, each with a named refusal, before any
digest is pinned or state is written. A conforming artefact is still accepted and
its receipt still records the skills that ran. No byte of
`plugins/hexaemeron/skills/fiat/SKILL.md` at or below offset 22771 changes, and
`python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json`
exits zero. `plugins/hexaemeron/docs/decisions/` carries the new ADR, and it
passes the link check at two depths. The six derived artefacts are re-pinned:
the fixture manifest and source digest, the nine `fiat` runtime entries in
`tests/promise_machine_coverage.json`, `INTEGRATED_CONTROLLER_SHA256`,
`CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS`, and the portable-runtime and Horos
regeneration pair. `python3 -m unittest discover -t . -s tests` and
`cd plugins/hexaemeron && python3 tests/run_tests.py --jobs 8` are both green,
`python3 scripts/portable_promise_machine.py check` is clean, and
`design_evidence.py --transition step:3` exits zero.

**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (the link
rule, the `config.skills` seed, and the `done study` and `done runbook`
receipts), `plugins/hexaemeron/skills/fiat/SKILL.md` (phase-notes prose at or
after byte 22789 only), `tests/promise_machine_coverage.json`,
`plugins/hexaemeron/tests/test_issue_429_recovery.py`,
`tests/fixtures/agent-instruction-v1/` and `.horos/boundary.json`. Create
`plugins/hexaemeron/docs/decisions/ADR-link-gate.md` and
`plugins/hexaemeron/tests/test_link_gate.py`.

**Tests.** Add `plugins/hexaemeron/tests/test_link_gate.py`: the exact five
`../<skill>/SKILL.md` citations the previous run froze are refused; a link
relative to its own file is refused even when it happens to resolve from the
artefact's current directory; an absolute URL and a repository-relative path are
accepted; an unresolvable repository-relative path is refused; the same bytes earn
the same verdict at two depths; a refusal writes no receipt and leaves the ledger
unchanged; and a conforming artefact still receipts with its skills recorded. The
audit runner contract is
`cd plugins/hexaemeron && python3 tests/run_tests.py --elenchus-report {report} --jobs 8`,
its format is the runner's Elenchus-compatible report, and Warden writes
`.hexaemeron/elenchus/hexaemeron-step-2.json`. Every new guard runs against the
parent commit, where the receipt-level ones fail. Expected new focused tests: 8.

**Disciplines.** phylax: this step makes the controller run a bundled script on a
caller-named artefact, so the path bound and the subprocess boundary are its to
answer. ephoros: the refusal names the file and the link, which is the only signal
this change owes. metron: none, no budget and no speed-motivated change.
elenchus: each refusal carries its exact specimen and fails against the parent.
hypomnema: the rule departs from the `done_prose` declaration precedent in the
same file, so the reason lands in an ADR beside it.

## Step 3: Advance the ledger, reconcile the prose, and demonstrate

**Goal.** Record the behaviour change as a generation row, correct the documents
that describe the receipts, and demonstrate the gate end to end.

**Entry.** Step 2's exit state; `design_evidence.py --transition step:3` exits
zero.

**Exit.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries exactly one new
row valid under the versioning contract: the generation counter incremented once,
evolution and epoch retained, and the frontier revision, frontier text, frontier
digest and held `Next Fiat job` byte-identical to their current values. The
`SKILL.md` frontmatter version matches the ledger. The demonstration runs in a
throwaway run directory: a study carrying the frozen specimen is refused by
`done study` with its digest unpinned, the same study with commit-pinned links is
accepted, and the transcript of both is recorded in the step's pull request. Both
suites and the root suite are green, the Horos boundary is current, and
`design_evidence.py --transition integration` exits zero.

**Files.** Change `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md` (frontmatter version only),
`tests/test_evolution_contract.py` and `.horos/boundary.json`. Create
`plugins/hexaemeron/tests/test_link_gate_ledger.py`.

**Tests.** Add `plugins/hexaemeron/tests/test_link_gate_ledger.py`: the ledger's
header version matches its newest row, the row's axis is `generation`, the
frontier revision and digest are unchanged from the prior row, the frontier digest
recomputes over the exact
`{status}|{frontier revision}|{current frontier}|{next Fiat job}` line including
its final newline, and the `SKILL.md` frontmatter version matches the header. The
audit runner contract is
`cd plugins/hexaemeron && python3 tests/run_tests.py --elenchus-report {report} --jobs 8`,
its format is the runner's Elenchus-compatible report, and Warden writes
`.hexaemeron/elenchus/hexaemeron-step-3.json`. Also run the demonstration above,
the root suite and `git diff --check`. Expected new focused tests: 5.

**Disciplines.** phylax: none, the step edits documents and runs the controller in
a throwaway directory. ephoros: none. metron: none. elenchus: the demonstration is
the guard, and it reproduces the original defect before showing the refusal.
hypomnema: the generation row is the durable record and the versioning contract
fixes its home.
