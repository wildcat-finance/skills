# Runbook: publish the ranked human contributor list

Study: [study.md](./study.md)
Task issue: https://github.com/wildcat-finance/skills/issues/515
Run branch: `fiat/515-publish-the-ranked-human-contributor-list`
Base: `main` at `dd23413ef6e9021bd80b930ad57e1766bf166f0b`

## Scope

Five steps. Step 1 scaffolds and commits the spec. Steps 2 and 3 build the
generator and its two rendered artefacts. Step 4 adds the daily trigger. Step 5
records the decisions and runs the demo path from the study's problem statement.

Every step's exit runs the root suite, the Promise Machine checks, and the
Phylax sweep, so no step hands the next a tree that fails a gate the repository
already enforces.

## 2026-08-28 amendment: Wave Atlas contributor evidence

The refresh now reads every closed pull-request page from
`wildcat-finance/shoggoth-wave-atlas`, counts only merged rows, and classifies
their author accounts through the existing exclusions. A human author of a
merged Atlas PR enters the ranking even with zero Skills commits. Skills commit
counts remain the first ordering key; merged PR counts from Skills and Wave
Atlas are summed for the second key. The public Atlas read uses the existing job
token and does not widen the workflow's permissions.

## Audit boundary

The run produces Python, Markdown, JSON and GitHub Actions YAML. It produces no
Solidity and no Foundry or Hardhat project, so the vendored security suite is
waived for this run and recorded as such. Audit rounds run Phylax, Ephoros and
Hypomnema exits rather than X-Ray and Solidity Auditor.

## Step 1: Scaffold the contributor surface and commit the spec

**Goal.** Land the committed spec, the shared host-identity constants, and the
parity test that keeps them honest, without yet computing a ranking.

**Entry.** The run branch `fiat/515-publish-the-ranked-human-contributor-list`
at `dd23413ef6e9021bd80b930ad57e1766bf166f0b`. Root suite green at 192 tests.

**Exit.** All of these hold:

- `docs/contributors/study.md` and `docs/contributors/runbook.md` are the
  receipted spec bytes, having passed the prose pass.
- `scripts/contributors.py` exists, exposes `HOST_IDENTITY_NAMES`,
  `HOST_IDENTITY_EMAILS`, `HOST_PR_LOGINS` and `is_host_identity`, and its
  `--help` exits 0. It computes no ranking yet.
- `tests/test_contributors.py` asserts the three frozensets are equal to the
  ones parsed out of `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, and
  fails when either side is edited alone.
- `tests/emit_contributors_report.py` writes one `elenchus.unittest.v1` report
  to a supplied path and only to that path.
- `python3 -m unittest discover -s tests` passes with at least 195 tests.
- `python3 scripts/promise_machine.py check`,
  `python3 scripts/promise_machine.py coverage --check` and
  `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins scripts tests schemas`
  each exit 0.

**Files.** Create `scripts/contributors.py`, `tests/test_contributors.py`,
`tests/emit_contributors_report.py`, `docs/contributors/study.md`,
`docs/contributors/runbook.md`.

**Tests.** Create `tests/test_contributors.py` with the host-set parity tests:
one per frozenset, plus one asserting `is_host_identity` agrees with
`hexctl.py`'s function on the fourteen names and two emails. Expected count 3
new tests, root total at least 195.

Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 tests/emit_contributors_report.py {report}
report format: unittest-json-v1
report file:   .elenchus/contributors.json
```

**Disciplines.** phylax: the step adds a root script that later reads the
network, so its argument surface is fixed now. ephoros: none, nothing in this
step runs unattended. metron: none, no performance claim. elenchus: none, no
failure in hand at entry. hypomnema: the committed spec location is the record,
and `docs/contributors/` is chosen here rather than argued about in step 5.

## Step 2: Classify and rank contributors from resolved identity

**Goal.** Compute the ranked contributor list from the GitHub contributors API
and the local git history, and stop rather than guess on an identity the host
set does not cover.

**Entry.** Step 1's exit state on branch
`fiat/515-publish-the-ranked-human-contributor-list-step-1-scaffold-the-contributor-surface`.

**Exit.** All of these hold:

- `python3 scripts/contributors.py --json` prints one JSON object carrying the
  ranked logins, each contributor's commit count and merged pull-request count,
  the excluded identities with a reason per identity, and the closed-issue
  coverage list of humans with issue activity and no ranked commits.
- Ranking is commits descending, merged pull requests descending as tie-break,
  then login ascending, so equal counts order identically on every run.
- The owner login is absent from the ranked list.
- Every identity in the reused host set is absent from the ranked list.
- Five guard tests pass, each failing when its guard is removed:
  `test_stops_on_unknown_identity`, `test_stops_on_bad_login_grammar`,
  `test_stops_on_api_failure`, `test_stops_on_host_set_drift`,
  `test_stops_on_owner_in_output`.
- No response field other than the login appears in any output structure.
- `python3 -m unittest discover -s tests`,
  `python3 scripts/promise_machine.py check`,
  `python3 scripts/promise_machine.py coverage --check` and the Phylax sweep
  over `plugins scripts tests schemas` each exit 0.

**Files.** Change `scripts/contributors.py`, `tests/test_contributors.py`.
Create `tests/fixtures/contributors/` holding recorded API responses so the
tests need no network.

**Tests.** Extend `tests/test_contributors.py` with the five guard tests, the
ranking-determinism test over a tie, the multi-email resolution test using the
recorded fixture that splits one human across two author emails, and a test
asserting the classification lines name every identity encountered. Expected
count at least 12 new tests, root total at least 207.

Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 tests/emit_contributors_report.py {report}
report format: unittest-json-v1
report file:   .elenchus/contributors.json
```

**Disciplines.** phylax: this step opens the GitHub API read and the git
subprocess, the two boundaries item 9 names. ephoros: the per-identity
classification line is the signal answering "why is this person not on the
list". metron: none, no performance claim; the study records the absence of a
budget. elenchus: the five fail-closed stops each get a guard test here.
hypomnema: the identity-over-trailer decision is recorded in step 5's ADR, not
here.

## Step 3: Render both artefacts from one computation

**Goal.** Write `CONTRIBUTORS.md` and the `README.md` thanks block from the
single ranking computed in step 2, so the two cannot disagree.

**Entry.** Step 2's exit state on branch
`fiat/515-publish-the-ranked-human-contributor-list-step-2-classify-and-rank-contributors`.

**Exit.** All of these hold:

- `python3 scripts/contributors.py --write` creates `CONTRIBUTORS.md` with a
  ranked table and a header comment stating the file is generated and must not
  be hand-edited, and replaces the region of `README.md` between two literal
  HTML-comment markers with handles only.
- The `README.md` block carries GitHub handles and no count, rank, date or
  other aggregate data. Asserted by a test that fails if a digit appears
  inside the block.
- `python3 scripts/contributors.py --check` exits 0 when both artefacts match
  the computation and non-zero naming the file when either does not.
- A second `--write` over an unchanged ranking leaves both files
  byte-identical.
- Neither file is ever left half-written: each is rendered whole in memory and
  replaced atomically. Asserted by a test that interrupts between the two
  writes and confirms the untouched file is intact.
- `README.md` outside the two markers is byte-identical to its entry state.
- The root suite, both Promise Machine checks and the Phylax sweep each exit 0.

**Files.** Change `scripts/contributors.py`, `tests/test_contributors.py`,
`README.md`. Create `CONTRIBUTORS.md`.

**Tests.** Extend `tests/test_contributors.py` with the idempotence test, the
digits-absent test over the README block, the owner-absent test over both
rendered files, the marker-boundary test asserting the rest of `README.md` is
untouched, and the interrupted-write test. Expected count at least 6 new tests,
root total at least 213.

Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 tests/emit_contributors_report.py {report}
report format: unittest-json-v1
report file:   .elenchus/contributors.json
```

**Disciplines.** phylax: this step opens the tracked-file write boundary, and
the marker-bounded edit is its control. ephoros: none, the rendering emits no
new unattended signal beyond step 2's. metron: none. elenchus: the
interrupted-write and marker-boundary guards land here. hypomnema: the
generated-file convention goes in the `CONTRIBUTORS.md` header comment and the
generator docstring, per the study's item 12.

## Step 4: Refresh daily and open a pull request only on change

**Goal.** Run the generator on a daily schedule and on manual dispatch,
opening a pull request only when the ranking actually changed.

**Entry.** Step 3's exit state on branch
`fiat/515-publish-the-ranked-human-contributor-list-step-3-render-both-artefacts`.

**Exit.** All of these hold:

- `.github/workflows/contributors.yml` runs on `schedule` with one daily cron
  and on `workflow_dispatch`.
- `permissions` is declared explicitly as `contents: write` and
  `pull-requests: write` and nothing else.
- The job is guarded to `github.repository == 'wildcat-finance/skills'` so a
  fork's schedule cannot open pull requests.
- `concurrency` groups the job so two runs cannot race the same branch.
- The workflow runs `--check` first and exits without opening anything when it
  passes, so an unchanged ranking produces no pull request and no commit.
- One job-summary line per run carries the ranking digest, the contributor
  count, and whether a pull request was opened, so a no-op run is
  distinguishable from a failed one.
- A test parses the workflow YAML and asserts the permission set, the
  repository guard, the concurrency group, the daily schedule and the presence
  of `workflow_dispatch`.
- The root suite, both Promise Machine checks and the Phylax sweep each exit 0.

**Files.** Create `.github/workflows/contributors.yml`. Change
`tests/test_contributors.py`.

**Tests.** Extend `tests/test_contributors.py` with the workflow-shape tests:
permissions exactly the two write scopes, repository guard present, concurrency
group present, schedule daily, `workflow_dispatch` present, and no `secrets.`
reference other than none at all. Expected count at least 6 new tests, root
total at least 219.

Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 tests/emit_contributors_report.py {report}
report format: unittest-json-v1
report file:   .elenchus/contributors.json
```

**Disciplines.** phylax: this step opens the unattended CI boundary, and the
minimum permission set, repository guard and concurrency group are its controls.
ephoros: the job-summary line is the signal answering "did the refresh actually
run". metron: none. elenchus: none, no failure in hand. hypomnema: the cadence
decision came from the Creator and is recorded in the study's item 3, so this
step adds no separate record.

## Step 5: Record the decisions, correct the claim, and demonstrate

**Goal.** Record the identity-over-trailer decision, make the README's
recognition sentence say what the implemented evidence establishes, bind the
generator into the Promise Machine, and run the demo path.

**Entry.** Step 4's exit state on branch
`fiat/515-publish-the-ranked-human-contributor-list-step-4-refresh-weekly-and-open-a-pull-request`.

**Exit.** All of these hold:

- `docs/decisions/ADR-019-rank-contributors-by-resolved-identity.md` records
  the decision, the rejected trailer option with the counts that disprove it,
  and the dependency on issue #466.
- `README.md:57`'s recognition sentence names `CONTRIBUTORS.md`, states that
  the list is regenerated daily, and names the GitHub-side condition the
  repository cannot control, which is that a merge discarding authorship
  reduces a contributor's count and this repository cannot detect it.
- `docs/how-to-help-shoggoth.md` states what the generated list establishes and
  what it does not.
- `docs/promise-machine/contributors-v2.md` states the generator's promise,
  evidence, boundary and refusals, and `tests/promise_machine_coverage.json`
  carries its row.
- `python3 scripts/promise_machine.py check` and
  `python3 scripts/promise_machine.py coverage --check` exit 0 with the new
  promise counted.
- The demo path from the study's problem statement runs clean, in order:

```bash
python3 scripts/contributors.py --check
python3 scripts/contributors.py --write
git diff --exit-code -- CONTRIBUTORS.md README.md
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins scripts tests schemas
```

- `git diff --exit-code` after `--write` proves the committed artefacts are
  exactly what the generator produces.

**Files.** Create
`docs/decisions/ADR-019-rank-contributors-by-resolved-identity.md`,
`docs/promise-machine/contributors-v2.md`. Change `README.md`,
`docs/how-to-help-shoggoth.md`, `tests/promise_machine_coverage.json`,
`tests/test_contributors.py`.

**Tests.** Extend `tests/test_contributors.py` with a test asserting the README
recognition sentence names `CONTRIBUTORS.md`, and one asserting the ADR file
exists and names both the chosen and the rejected option. The Promise Machine
coverage check is the test for the new promise row. Expected count at least 2
new tests, root total at least 221.

Elenchus runner contract for any fix claimed in this step's audit:

```text
test command: python3 tests/emit_contributors_report.py {report}
report format: unittest-json-v1
report file:   .elenchus/contributors.json
```

**Disciplines.** phylax: none, this step opens no new boundary. ephoros: none,
the signals landed in steps 2 and 4. metron: none. elenchus: none, no failure in
hand. hypomnema: this is the step hypomnema governs, carrying ADR-019, the
Promise Machine contract, and the two corrected prose claims.
