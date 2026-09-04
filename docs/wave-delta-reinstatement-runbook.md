# Runbook: reinstate the Wave Delta distributed checkpoint programme

Derived from `.hexaemeron/study.md`, receipted. The selected design is
`additive-successors`: reopen the distributed layer by addition above ADR-028,
one standing successor per retired decision, ADR-028 left Accepted with one
appended dated amendment.

This is a Tier 0 delivery. It writes decision records and documents. It
implements no checkpoint behaviour, creates no repository, touches no cloud
account, key, region or spend, and changes nothing under `plugins/`.

## The four programme checks

Every step is green at entry and green at exit, and green means all four of
these exit zero, run from the run worktree:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
```

`plugins/hexaemeron/tests/run_tests.py` is the parallel runner and is the one
that must be used over that tree. Plain `unittest discover` there swallows
ImportErrors and reads as a clean suite, so a green `discover` over
`plugins/hexaemeron/tests` proves nothing and is not a substitute. Do not
replace that first line with a `discover` invocation.

Three prose lints passing is not CI. A step that receipts green on imprimatur,
vulgate and hypomnema alone can still be a red branch, so every step's Exit
below names all four commands in full rather than deferring to this section.

## Where results go

Every step reports its result in the pull-request body. No step writes an issue
comment. The single exception is the closing pointer `done integrate` puts on
[#859](https://github.com/wildcat-finance/skills/issues/859) before it closes
that issue; it stays short and carries nothing that is not already in the run
pull-request body.

## Boundaries for this build

**Always.** All four programme checks at both ends of every step. Imprimatur
then vulgate on every changed prose file. `tests/test_decision_records.py` after
a base sync, because ADR numbers are only free against the fetched default
branch. A recorded readback before any published issue body is called done.

**Ask first.** Any ADR number outside 069 to 073. Any edit to a file under
`plugins/`. Any issue outside #859 to #867. Any change to
`tests/test_fiat_checkpoint_decision_record.py` or its pinned digests. Any new
dependency.

**Never.** Edit `docs/fiat-controller-checkpoint-study.md` or
`docs/fiat-controller-checkpoint-runbook.md`; both are digest-pinned run
artefacts. Edit a `wave-atlas-original` section. Edit #899 or #901. Rewrite the
Status line of any existing decision record. Delete a failing test to make a
suite pass. Claim a command ran when it did not.

## Carried forward at integration

This run does not re-file
[#899](https://github.com/wildcat-finance/skills/issues/899) and
[#901](https://github.com/wildcat-finance/skills/issues/901) against the Fiat
frontier. That work is named here so the integrate step does not discover it
late: `.hexaemeron/run-pr.md` carries it under `## Carried forward`, where
`done integrate` requires a non-empty section, and Step 7's exit checks that the
section names both issue numbers.

## The Elenchus runner contract

Every step below uses the same runner. The root suite is the one that holds
`tests/test_decision_records.py` and
`tests/test_fiat_checkpoint_decision_record.py`, which are the tests this
delivery can actually break.

Command: `python3 tests/run_tests.py {report}`. Format: `elenchus.unittest.v1`.
The runner refuses a report path that already exists, so a second round in the
same step writes the next unused path in the same directory.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 6a171b6f72d1a651ebd9b7dd32af331ba6a9aaff600f02100c328907d1b9d755
candidate | additive-successors
```

## Step 1: Land the study, the runbook and the reinstatement record

**Goal.** Commit the receipted study and this runbook, record the reinstatement
route as ADR-069, and append the dated amendment to ADR-028.

**Entry.** `main` at `ff47f3070c8dce05c767b6c0dad65234c56870de`, synced and
fast-forwarded, with `origin/main` fetched so ADR numbering can be compared
against it. All four programme checks green. ADR-068 is the highest record on
disk; 069 through 073 are free on the fetched default branch.

**Exit.** ADR-069 exists and states the reinstatement route: the distributed
layer reopens above the local checkpoint store, ADR-028 stays Accepted, and the
four retired decisions gain successors rather than edits. ADR-028 carries a new
`## Amendment: distributed layer reinstated (2026-09-02)` section placed after
`## Consequences`, with its Status line and every literal the pinned test names
untouched. All of these exit zero:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest tests.test_decision_records tests.test_fiat_checkpoint_decision_record
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/wave-delta-reinstatement-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/wave-delta-reinstatement-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/wave-delta-reinstatement-study.md --design-evidence .hexaemeron/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/wave-delta-reinstatement-study.md docs/wave-delta-reinstatement-runbook.md docs/decisions/ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md
! git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD | grep -q '^plugins/'
```

The hypomnema call is the one that first becomes satisfiable here: the study's
`design-bridge` block names ADR-069, so it reports H008 until this step's commit
and exits zero from this step's exit onward. The result goes in the
pull-request body.

**Files.** Created: `docs/wave-delta-reinstatement-study.md`,
`docs/wave-delta-reinstatement-runbook.md`,
`docs/decisions/ADR-069-reinstate-the-distributed-checkpoint-layer-above-the-local-store.md`.
Changed: `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`,
appended only.

**Tests.** No new test module. `tests/test_decision_records.py` and
`tests/test_fiat_checkpoint_decision_record.py` are extended by nothing and must
pass unmodified; the second is the guard that proves the ADR-028 amendment did
not disturb a pinned literal or a pinned digest. Expected count: the root suite
was 768 tests at PR #997 and this step adds none, so the count moves only if
another delivery landed meanwhile. Elenchus runner:
`python3 tests/run_tests.py {report}`, format `elenchus.unittest.v1`, report
file `.hexaemeron/elenchus/step-1.json`.

**Disciplines.** phylax: none, this step reads and writes only files inside the
worktree and starts no subprocess of its own. ephoros: none, nothing this step
lands runs unattended. metron: none, no performance claim and no measurable
change. elenchus: applies, because the ADR-028 amendment is the one edit in this
delivery that can break a pinned assertion, and a break here is a failure in
hand rather than a hunt. hypomnema: applies, this step writes the standing
record the study's design bridge binds and appends to an accepted record.

## Step 2: Carry ADR-029 and ADR-030 forward

**Goal.** Give the protocol-and-authority separation and the storage-authority
substrate one standing successor each, rebased on `fiat-v5.49.1`.

**Entry.** Step 1's exit state. All four programme checks green. ADR-069 on
disk. ADR-070 and ADR-071 free on the fetched default branch.

**Exit.** ADR-070 carries ADR-029's decision forward and names it; ADR-071
carries ADR-030's forward and names it. Each states which clauses it carries
verbatim, which it rebases on `fiat-v5.49.1`, and which it drops, so a reader
can diff successor against source. Neither describes as absent anything
`plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md` already
specifies. ADR-029 and ADR-030 keep their Retired status and their bodies. All
of these exit zero:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest tests.test_decision_records tests.test_fiat_checkpoint_decision_record
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-070-separate-the-checkpoint-protocol-from-its-authority-service.md docs/decisions/ADR-071-hold-checkpoint-authority-in-locked-storage-behind-replaceable-compute.md
git diff --name-only HEAD~1..HEAD -- docs/decisions/ADR-029-separate-the-checkpoint-protocol-from-its-authority-service.md docs/decisions/ADR-030-use-s3-object-lock-behind-replaceable-digitalocean-compute.md | wc -l | grep -qx '0'
! git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD | grep -q '^plugins/'
```

The `git diff --name-only … | wc -l` check is the exit that proves the two
retired records were not edited while their successors were written. The result
goes in the pull-request body.

**Files.** Created:
`docs/decisions/ADR-070-separate-the-checkpoint-protocol-from-its-authority-service.md`,
`docs/decisions/ADR-071-hold-checkpoint-authority-in-locked-storage-behind-replaceable-compute.md`.
Changed: none.

**Tests.** No new test module. `tests/test_decision_records.py` gains two more
records to check and must pass unmodified: the filename convention, the H1
matching the filename number, and no collision against the fetched default
branch. Expected count unchanged from Step 1. Elenchus runner:
`python3 tests/run_tests.py {report}`, format `elenchus.unittest.v1`, report
file `.hexaemeron/elenchus/step-2.json`.

**Disciplines.** phylax: none, files only, no boundary opens. ephoros: none,
nothing runs unattended. metron: none, no performance claim. elenchus: applies,
because a number collision against a concurrently landing delivery is the
failure this step is most likely to produce and its guard already exists in
`tests/test_decision_records.py`. hypomnema: applies, two standing records are
written and two retired ones gain named successors.

## Step 3: Carry ADR-031 and ADR-032 forward

**Goal.** Give the signed publication fence and the lineage DAG one standing
successor each, rebased on `fiat-v5.49.1`.

**Entry.** Step 2's exit state. All four programme checks green. ADR-072 and
ADR-073 free on the fetched default branch.

**Exit.** ADR-072 carries ADR-031's decision forward and names it; ADR-073
carries ADR-032's forward and names it, on the same carry-rebase-drop contract
as Step 2. ADR-031 and ADR-032 keep their Retired status and their bodies. Each
of ADR-029 through ADR-032 now has exactly one standing successor, which is the
condition `retired-decision-successors` scored 4 on. All of these exit zero:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest tests.test_decision_records tests.test_fiat_checkpoint_decision_record
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-072-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md docs/decisions/ADR-073-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md
git diff --name-only HEAD~1..HEAD -- docs/decisions/ADR-031-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md docs/decisions/ADR-032-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md | wc -l | grep -qx '0'
! git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD | grep -q '^plugins/'
```

The result goes in the pull-request body.

**Files.** Created:
`docs/decisions/ADR-072-fence-external-fiat-transitions-on-signed-checkpoint-acceptance.md`,
`docs/decisions/ADR-073-model-checkpoint-lineage-as-an-explicitly-resolved-dag.md`.
Changed: none.

**Tests.** No new test module. Same two record tests as Step 2, extended by two
more records and passing unmodified. Expected count unchanged. Elenchus runner:
`python3 tests/run_tests.py {report}`, format `elenchus.unittest.v1`, report
file `.hexaemeron/elenchus/step-3.json`.

**Disciplines.** phylax: none, files only. ephoros: none, nothing runs
unattended. metron: none, no performance claim. elenchus: applies, same
numbering-collision guard as Step 2. hypomnema: applies, the last two standing
records land and the successor set closes.

## Step 4: Write the fresh programme study

**Goal.** Replace the disclaimed programme study with one that governs, rebased
on what has actually shipped.

**Entry.** Step 3's exit state. All four programme checks green. ADR-069 through
ADR-073 on disk.

**Exit.** `docs/wave-delta-checkpoint-programme-study.md` exists, carries no
"no longer governs" banner, answers all twelve Protasis items, and states four
things the old study could not: that `hexctl checkpoint export` and `hexctl
checkpoint restore` already supply controller-state capture, ref binding, ledger
prefix verification and relocation; what the distributed layer still owes on top
of that capsule; that #508 no longer gates #860 by maintainer decision recorded
2026-09-02, and that #508 stays open in its own lane inside milestone 64; and
that #899 and #901 are `hexctl` controller defects leaving milestone 64 for the
Fiat frontier. `docs/hexaemeron-checkpoint-programme-study.md` keeps its
historical banner and gains a dated forward pointer to the new study. All of
these exit zero:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest tests.test_decision_records tests.test_fiat_checkpoint_decision_record
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/wave-delta-checkpoint-programme-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/wave-delta-checkpoint-programme-study.md docs/hexaemeron-checkpoint-programme-study.md
git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD -- docs/fiat-controller-checkpoint-study.md docs/fiat-controller-checkpoint-runbook.md | wc -l | grep -qx '0'
! git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD | grep -q '^plugins/'
```

The digest-pinned pair check is an exit here because this is the step working
closest to them. The result goes in the pull-request body.

**Files.** Created: `docs/wave-delta-checkpoint-programme-study.md`. Changed:
`docs/hexaemeron-checkpoint-programme-study.md`, appended only.

**Tests.** No new test module. `tests/test_fiat_checkpoint_decision_record.py`
carries the guard that matters here, because it holds the two digest pins this
step must not disturb, and it passes unmodified. Expected count unchanged.
Elenchus runner: `python3 tests/run_tests.py {report}`, format
`elenchus.unittest.v1`, report file `.hexaemeron/elenchus/step-4.json`.

**Disciplines.** phylax: none, files only. ephoros: none, the document describes
a system that does not exist yet and emits nothing. metron: none, no performance
claim. elenchus: applies, a stray edit to either digest-pinned file fails
immediately and the exit above names the check that catches it. hypomnema:
applies, this decides that the fresh documents supersede the historical pair by
addition rather than replacing them in place.

## Step 5: Write the fresh programme runbook

**Goal.** Derive the programme's step sequence from Step 4's study, with each
packet's target repository and authority gate stated.

**Entry.** Step 4's exit state. All four programme checks green.
`docs/wave-delta-checkpoint-programme-study.md` on disk and passing
`protasis.py --study`.

**Exit.** `docs/wave-delta-checkpoint-programme-runbook.md` exists, carries no
"no longer governs" banner, passes the Protasis step schema, and names for every
packet its target repository and its entry gate. It states that #860 is
startable once the reinstatement records land, that creating
`wildcat-finance/fiat-checkpoints` remains a separate authorisation, and that no
packet below it authorises one agent to write Skills, the service and Atlas
together. `docs/hexaemeron-checkpoint-programme-runbook.md` keeps its historical
banner and gains a dated forward pointer. All of these exit zero:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest tests.test_decision_records tests.test_fiat_checkpoint_decision_record
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/wave-delta-checkpoint-programme-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/wave-delta-checkpoint-programme-runbook.md docs/hexaemeron-checkpoint-programme-runbook.md
git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD -- docs/fiat-controller-checkpoint-study.md docs/fiat-controller-checkpoint-runbook.md | wc -l | grep -qx '0'
! git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD | grep -q '^plugins/'
```

The result goes in the pull-request body.

**Files.** Created: `docs/wave-delta-checkpoint-programme-runbook.md`. Changed:
`docs/hexaemeron-checkpoint-programme-runbook.md`, appended only.

**Tests.** No new test module. Expected count unchanged. Elenchus runner:
`python3 tests/run_tests.py {report}`, format `elenchus.unittest.v1`, report
file `.hexaemeron/elenchus/step-5.json`.

**Disciplines.** phylax: none, files only. ephoros: none, nothing runs
unattended. metron: none, no performance claim. elenchus: applies, the
digest-pin guard from Step 4 still holds and its check is repeated in the exit.
hypomnema: applies, the runbook is where each later packet's authority gate is
recorded, and getting that wrong is expensive to reverse.

## Step 6: Rewrite the estate's operative verdict

**Goal.** Make the nine estate issues say what the repository now says, by
appending one new dated `wave-atlas-review` block to each.

**Entry.** Step 5's exit state. All four programme checks green. ADR-069 through
ADR-073 and both fresh programme documents on disk. The maintainer's 2026-09-02
grant, recorded in the study's assumption 8, is in force.

**Exit.** `docs/wave-delta-issue-estate-2026-09-02.md` exists and holds, per
issue, the exact block bytes published and the digest read back from GitHub
afterwards. The nine issues each carry the new block. The grant is bounded to
exactly these nine and nothing else:
[#859](https://github.com/wildcat-finance/skills/issues/859),
[#860](https://github.com/wildcat-finance/skills/issues/860),
[#861](https://github.com/wildcat-finance/skills/issues/861),
[#862](https://github.com/wildcat-finance/skills/issues/862),
[#863](https://github.com/wildcat-finance/skills/issues/863),
[#864](https://github.com/wildcat-finance/skills/issues/864),
[#865](https://github.com/wildcat-finance/skills/issues/865),
[#866](https://github.com/wildcat-finance/skills/issues/866) and
[#867](https://github.com/wildcat-finance/skills/issues/867). No other issue is
edited, and #899 and #901 are not edited. Every `wave-atlas-original` section is
left byte-identical. Each block is drafted on disk, passes the bounded Sapheneia
durable-record pass and then imprimatur and vulgate there, and is published
verbatim from those bytes; the readback compares the published body against the
drafted bytes and a mismatch stops the step. All of these exit zero:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 -m unittest tests.test_decision_records tests.test_fiat_checkpoint_decision_record
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/wave-delta-issue-estate-2026-09-02.md
for n in 859 860 861 862 863 864 865 866 867; do gh issue view "$n" --repo wildcat-finance/skills --json body --jq .body | grep -q 'wave-atlas-original:start' || exit 1; done
! git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD | grep -q '^plugins/'
```

The loop is the exit that proves the historical filing survived on every one of
the nine. The per-issue readback digests are the evidence recorded in the on-disk
record. The result goes in the pull-request body; this step writes no issue
comment.

**Files.** Created: `docs/wave-delta-issue-estate-2026-09-02.md`. Changed: none
in the repository. Nine issue bodies change on GitHub.

**Tests.** No new test module, because no repository test can reach a GitHub
issue body and adding one would claim a guard that does not exist. The on-disk
record plus the readback loop above is the evidence instead. Expected count
unchanged. Elenchus runner: `python3 tests/run_tests.py {report}`, format
`elenchus.unittest.v1`, report file `.hexaemeron/elenchus/step-6.json`.

**Disciplines.** phylax: applies, this is the delivery's only write to a surface
outside the worktree, and the controls are the bounded grant, the on-disk draft,
the verbatim publication and the readback. ephoros: none, an issue edit runs
once under an operator and emits no signal anyone waits on. metron: none, nine
API calls carry no budget. elenchus: applies, a readback mismatch stops the step
and its guard is the loop in the exit. hypomnema: applies, the on-disk record is
the durable home for what was published, so the change stays reviewable without
GitHub.

## Step 7: Demonstrate the reinstatement

**Goal.** Run the demo path from the study's problem statement and show the
contradiction is gone.

**Entry.** Step 6's exit state. All four programme checks green. Every record
and document from Steps 1 through 6 on disk.

**Exit.** `docs/wave-delta-reinstatement-demo.py` exists and
`python3 docs/wave-delta-reinstatement-demo.py --repo .` exits zero, having
checked all five conditions from the study's section 1: ADR-029 through ADR-032
each name exactly one standing successor; ADR-028 is still Accepted and still
carries its mandatory-local-hand-off amendment verbatim; no governing document
under `docs/` carries a "no longer governs" banner; the estate's current verdict
names the reinstatement; and
`python3 -m unittest tests.test_decision_records tests.test_fiat_checkpoint_decision_record`
exits zero.

Condition four is read from `docs/wave-delta-issue-estate-2026-09-02.md` rather
than from a live GitHub call. That is a deliberate reading of the study's
wording and the reason is on the page: a demo that needs the network is not
deterministic and cannot run in CI, so it proves the estate from the readback
evidence Step 6 recorded. The live check happened in Step 6's exit and is not
repeated here. All of these exit zero:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 docs/wave-delta-reinstatement-demo.py --repo .
python3 -m unittest tests.test_wave_delta_reinstatement
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/wave-delta-reinstatement-demo.py --include-code
grep -q '899' .hexaemeron/run-pr.md && grep -q '901' .hexaemeron/run-pr.md
! git diff --name-only ff47f3070c8dce05c767b6c0dad65234c56870de..HEAD | grep -q '^plugins/'
```

The `run-pr.md` check is the exit that proves the carryover this run owes was
written before integrate asks for it. The result goes in the pull-request body.

**Files.** Created: `docs/wave-delta-reinstatement-demo.py`,
`tests/test_wave_delta_reinstatement.py`. Changed: `.hexaemeron/run-pr.md` gains
its `## Carried forward` section naming the #899 and #901 re-filing against the
Fiat frontier.

**Tests.** New module `tests/test_wave_delta_reinstatement.py`, expected 6 tests:
one per demo condition, plus one that runs the demo against a deliberately broken
copy of the tree in a temporary directory and asserts it exits non-zero. That
last one is the guard convention: it fails without the demo script, so the demo
cannot silently become a script that passes on anything. The demo takes `--repo`
and nothing else, opens files read-only, writes nothing, and starts no subprocess
other than the two named `unittest` modules with fixed argv and no shell.
Elenchus runner: `python3 tests/run_tests.py {report}`, format
`elenchus.unittest.v1`, report file `.hexaemeron/elenchus/step-7.json`.

**Disciplines.** phylax: applies, this step adds executable Python to a documents
delivery, and the controls are the single `--repo` argument, read-only opens, no
writes, and fixed-argv subprocesses with no shell. ephoros: none, the demo runs
under an operator or in CI and its exit status is the whole signal. metron: none,
the demo reads a handful of files and holds no budget. elenchus: applies, the
broken-tree test is the guard that fails without the fix. hypomnema: none, this
step records no decision; every decision this delivery makes was recorded in
Steps 1 through 6.
