# Runbook: repair receipted commits before push

Issue: https://github.com/wildcat-finance/skills/issues/2014
Study: `.hexaemeron/study.md`, receipted in this run.
The starting commit is `685158cdc5407ca5559bf9ef4a021d664e764ece`.
The selected construction preserves original receipts and appends a bounded
supersession record. No step edits an earlier state or ledger event. Every step
starts from the green signed head of the preceding step and ends with the
repository's root and Hexaemeron suites green.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 2bd4fdff5e9d3d7da194a5a81d61fa97515d882f1548dffe53450fa469c7fcdd
candidate | append-only-map
```

## Step 1: Guard committer email readiness at local receipts

**Goal.** Add a bounded GitHub-readiness check for the committer email and the
signing key's user IDs while retaining signature-only cryptographic admission.

**Entry.** The run branch starts at
`685158cdc5407ca5559bf9ef4a021d664e764ece`, with no Step branch or
product edit. The exact receipted study and design record are available.

**Exit.** The implement, audit-round and audit-close receipts refuse a locally
valid GPG commit when its committer email is absent from the verified signing
key's user IDs. The diagnostic names the commit, key identity and committer
email without signature material. A matching committer passes this local
readiness gate, with GitHub verification still required at push. `done prose`
checks only the current receipted head because its future prose commit does not
exist yet. `done push` still checks every newly added commit. The guard does not
use author, co-author, byline, host or publisher as admission classes. Commit
the checked study and runbook copies in `docs/fiat-commit-supersession/` and
the first guard proof reporter. The reporter resolves `uid-admission` with a
zero-exit report under `.hexaemeron/reports/design/` before Step 2 opens.
Prove this Step on its signed head with `python3 -m unittest
plugins.hexaemeron.tests.test_fiat_commit_supersession -v`, `python3
plugins/hexaemeron/tests/run_tests.py`, `python3 -m unittest discover -s
tests`, `python3 scripts/run_checks.py`, and `git diff --check`, all exit zero.

**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, tests in
`plugins/hexaemeron/tests/`, and the applicable policy wording in `AGENTS.md`,
`SHOGGOTH.md` and the Fiat `SKILL.md`. Create
`plugins/hexaemeron/tests/fiat_commit_supersession_proof.py` and the tracked
study and runbook copies. Regenerate the portable Promise Machine copy and the
Horos census for every tracked change; update the boundary if Horos classifies
a changed path.

**Tests.** A real signed fixture whose key lacks the committer email is red
against the entry tree and refused on the Step head at first receipt. A
matching signed fixture passes. Bound malformed or unavailable GPG output,
subkey identity, duplicate UID, author/committer difference and the empty
prose-commit boundary. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-2014-step-1.json`.

**Disciplines.** phylax: Git and GPG metadata are bounded, untrusted child
output. ephoros: a refusal identifies the key and committer mismatch without
secrets. metron: none, no speed claim. elenchus: the signed mismatch specimen
is red on the parent and green on the fix. hypomnema: the separate
cryptographic-admission and platform-readiness rule is stated in the root and
Fiat contracts.

## Step 2: Add append-only supersession and effective commit projection

**Goal.** Permit a pre-push Step to replace already receipted implementation
or audit-fixes commits with tree-identical GitHub-verified commits.

**Entry.** Step 1's guard and proof reporter are receipted, signed, and green.
The `uid-admission` report and the design checker at `step:2` exit zero.

**Exit.** One bounded supersession command takes the recorded old SHA and the
replacement SHA, verifies the old receipt, exact Git tree equality, ordered
rewritten ancestry, local signature and GitHub exact-SHA verification before
an append-only ledger write. It rejects duplicate, cyclic, wrong-step,
changed-tree, unverified, unavailable, or old-SHA-still-in-range candidates
without a ledger mutation. Existing receipts stay byte-identical. A single
effective projection governs `last_local_commit`, audit closure, `verify`,
checkpoint coverage, push and checkpoint export/restore; all raw historical
ledger comparisons remain intact. The implementation and audit-fixes paths
both work. The proof reporter resolves `effective-ancestry` before Step 3
opens. Prove the signed Step head with the focused tests, complete Hexaemeron
and root suites, `python3 scripts/run_checks.py`, and `git diff --check`, all
exit zero.

**Files.** Change Fiat `hexctl.py`, its `checkpoint_authority/coverage.py`
consumer, the checkpoint and controller tests, and the proof reporter. Update
the Fiat `SKILL.md` and any owned reference needed to state the command and
recovery. Regenerate owned portable copies and Horos artifacts after the
tracked changes.

**Tests.** Build a disposable legacy run whose signed old commit was accepted
before the readiness guard and whose replacement has the same tree. Cover one
implementation commit and multiple audit rounds, exact original ledger
retention, effective ancestry in checkpoint coverage, and all refusal cases
from the risk register. Include an interrupted append/retry case. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-2014-step-2.json`.

**Disciplines.** phylax: the command reads Git objects and an external GitHub
answer before durable mutation. ephoros: refusals identify the old and new
SHA and the failed relation. metron: no speed claim; caps bound the map.
elenchus: each repaired failure has a parent-red guard. hypomnema: the
append-only schema and recovery rule belong in Fiat's operator contract and
version ledger.

## Step 3: Demonstrate repaired push and release the operator contract

**Goal.** Prove the guard and supersession compose across a complete Step
boundary, then publish consistent versioned instructions and generated copies.

**Entry.** Step 2's supersession and proof reporter are receipted, signed, and
green. The `effective-ancestry` report and design checker at `step:3` exit
zero.

**Exit.** A fresh signed disposable run refuses the mismatched committer at
its first commit receipt. A legacy run with three receipted bad commits
replaces each with a tree-identical commit, keeps the original ledger entries,
and completes `verify`, checkpoint coverage and `done push` on an effective
range that excludes all old SHAs. An unequal tree, a wrong parent/order and a
GitHub-unverified replacement each refuse without a new receipt. The demo
distinguishes a local UID match from GitHub's actual verified-email/account
gate. Record `platform-readback` for the integration transition from exact
replacement SHA checks. Bump the Fiat generation and Hexaemeron package
versions in all owned surfaces, update checkpoint-compatible versions, and
regenerate the portable Promise Machine runtime, coverage projections and
Horos boundary/census. Verify every changed prose record through Sapheneia,
Imprimatur, Vulgate and Imprimatur. Run the focused demonstration, complete
Hexaemeron and root suites, `python3 scripts/run_checks.py`, the three
discipline lints and `git diff --check`, all exit zero.

**Files.** Complete tests and demonstration under `plugins/hexaemeron/tests/`
and `docs/fiat-commit-supersession/`. Update Fiat's `EVOLUTION.md` and
`SKILL.md`, Hexaemeron package manifests, root and plugin policy documents,
generated portable runtime and its digests, version fixtures, coverage
projections, and Horos artifacts as required by the source ownership graph.

**Tests.** The demonstration exercises the exact three-commit chain and
rechecks the negative fixtures after the final edits. Record the complete
command, exit and report path. Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-2014-step-3.json`.

**Disciplines.** phylax: bind the final live platform response to its exact
repository and SHA. ephoros: the demo records each accepted or refused
boundary. metron: none, no speed claim. elenchus: final negative cases
reproduce the prior fault. hypomnema: the version row and repository prose
explain the changed receipt rule and its recovery.
