# Runbook: preserve external contributor attribution through Fiat integration

Derived from `.hexaemeron/study.md`. Four steps, dependency order, one pull
request each, stacked. Every step ends green on both suites.

Two obligations recur, so they are stated once here and named in each step that
incurs them. Any step that edits
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` must refresh the three
`fiat-*` `sha256` values in `tests/promise_machine_coverage.json` in the same
commit and leave `python3 scripts/promise_machine.py check` at exit 0. Any step
that changes tracked prose must leave `python3
plugins/horos/skills/horos/scripts/horos.py scan . --write` producing no
further change to `.horos/boundary.json`.

## Step 1: Scaffold the run and record the attribution decision

**Goal.** Commit the receipted study and runbook and record ADR-017, so the
later steps build against a written decision rather than a conversation.

**Entry.** Run branch `fiat/466-preserve-external-contributor-attribution-th`
at `191f2ce1d60abb8068887095a8c39fb4341f0be6`, study receipt recorded, no
tracked changes in the run worktree.

**Exit.** `plugins/hexaemeron/docs/fiat-merged-attribution/study.md` and
`plugins/hexaemeron/docs/fiat-merged-attribution/runbook.md` are byte-identical
to the receipted artefacts, and `docs/decisions/ADR-017-bind-merged-authorship-
to-the-integration-receipt.md` records the two decisions from study item 12.
Prove it with:

```bash
cmp .hexaemeron/study.md plugins/hexaemeron/docs/fiat-merged-attribution/study.md
cmp .hexaemeron/runbook.md plugins/hexaemeron/docs/fiat-merged-attribution/runbook.md
python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" --study plugins/hexaemeron/docs/fiat-merged-attribution/study.md
python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" plugins/hexaemeron/docs/fiat-merged-attribution/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions plugins/hexaemeron/docs/fiat-merged-attribution
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

**Files.** Create `plugins/hexaemeron/docs/fiat-merged-attribution/study.md`,
`plugins/hexaemeron/docs/fiat-merged-attribution/runbook.md`,
`docs/decisions/ADR-017-bind-merged-authorship-to-the-integration-receipt.md`.
Update `.horos/boundary.json` only if the scan earns an entry.

**Tests.** No new test. The step adds documents, and the root suite already
guards the boundary, the ADR shape and the prose gates. Hypomnema H001 over
the committed copies is the check that matters here: a relative link written
for one directory resolves to nothing from another, and the committed copy is
the one a reader follows. Expected counts
unchanged from the recorded baseline: 192 root, 874 Hexaemeron. Elenchus runner
contract for any fix in this step's audit:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-1.json`.

**Disciplines.** phylax: none, the step opens no boundary and reads no
untrusted input. ephoros: none, nothing here runs unattended. metron: none, no
performance claim. elenchus: none, no failure in hand at entry. hypomnema: the
ADR is the whole point of the step, and the storage shape and gate placement it
fixes are expensive to reverse once later receipts read them.

## Step 2: Record who authored the pushed range

**Goal.** Make `done push` record, for the exact verified range, the GitHub
account each commit is linked to and a digest that identifies its author
without storing the address.

**Entry.** Step 1 merged into this branch's parent and green: the study,
runbook and ADR-017 are committed and both suites pass at step 1's head.

**Exit.** `verify_github_commits` returns a validated attribution record per
SHA and `done push` stores it under a new `attribution` container on the push
receipt, holding the pull-request author login, and per commit: the linked
login or explicit `null`, the author name, the SHA-256 digest of the lowercased
author email, and any co-author identities parsed from the message. Every field
is type-checked and length-capped, and a malformed, oversized or absent field
refuses before state or ledger mutation. No email appears in
`.hexaemeron/state.json` or `.hexaemeron/ledger.jsonl`. Prove it with:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`tests/promise_machine_coverage.json`.

**Tests.** Extend `plugins/hexaemeron/tests/test_hexctl.py`. The fake `gh`
commits payload gains `author`, `commit.author` and `commit.message`, driven by
`FAKE_GH_MODE`. New cases: an external human author recorded with its login and
digest; an unlinked author recorded as explicit `null`; a co-author trailer
recorded as a second identity; a host identity in a co-author trailer still
refused; a malformed login, a malformed email and an oversized field each
refusing; and an assertion that no `@` appears in the recorded attribution
bytes. Expect about 10 new tests, so roughly 884 Hexaemeron and 192 root.
Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-2.json`.

**Disciplines.** phylax: this step reads new fields out of a GitHub JSON
response and parses attacker-influenceable commit-message trailers, and it
decides what is persisted. ephoros: the push receipt is the record that answers
which identity a step published under, so its shape is the emission. metron:
none, the step adds no request and makes no speed claim. elenchus: none at
entry; any failure surfaced in the round is worked to its cause under the
runner contract above. hypomnema: none beyond ADR-017, which already fixes the
stored shape.

## Step 3: Bind the merged state at integrate

**Goal.** Make `done integrate` refuse unless every identity recorded across
the run is still attributable from the recorded merge commit, and record which
mechanism preserved it.

**Entry.** Step 2 merged into this branch's parent and green: push receipts
carry the attribution container and both suites pass at step 2's head.

**Exit.** `done integrate` gathers the identities recorded across every step's
push receipt and, for each, requires one of two mechanisms against the recorded
merge SHA: the commit that carried it is an ancestor of the merge, or the
identity appears as author or `Co-authored-by` of the merge commit. The
integration receipt records the mechanism per identity. A recorded identity
that satisfies neither refuses the receipt, naming the identity and the fault,
with no state or ledger mutation. The `integrate` directive from `next` names
the merge method that preserves attribution. Prove it with:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/hexaemeron/skills/fiat/scripts/hexctl.py
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`,
`tests/promise_machine_coverage.json`.

**Tests.** Extend `plugins/hexaemeron/tests/test_hexctl.py`. The fake `git`
gains an ancestry mode so `merge-base --is-ancestor` can answer no. New cases:
a preserved merge recording mechanism `ancestor`; a rewritten merge whose merge
commit carries the identity as author recording mechanism `merge-author`; the
same via a co-author trailer recording `merge-coauthor`; a rewritten merge that
dropped the identity refusing and naming it; a failed ancestry call
distinguished from a negative answer; and a legacy push receipt with no
attribution container still integrating. Expect about 8 new tests, so roughly
892 Hexaemeron and 192 root. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-3.json`.

**Disciplines.** phylax: the step adds a local git ancestry read and must not
confuse a failed call with a negative answer. ephoros: the refusal text and the
recorded mechanism are what answer "did the authorship reach the base" and "why
did integrate refuse". metron: none, the added work is bounded by the existing
range cap and no speed claim is made. elenchus: none at entry; a failure in the
round is worked under the runner contract above. hypomnema: none beyond
ADR-017.

## Step 4: Publish the claim, close the ledger, and demonstrate

**Goal.** Say in the repository's own prose exactly what the new evidence
establishes, record the generation on Fiat's ledger, and replay the demo path
from the study's problem statement.

**Entry.** Step 3 merged into this branch's parent and green: both gates are in
the controller and both suites pass at step 3's head.

**Exit.** The README contributor-list sentence and a new contributor-guide
paragraph state what the receipt establishes and name the GitHub-side
conditions the repository does not control: the commit author email has to be
one GitHub can match to the account, and the list itself is GitHub's to
compute. `push-discipline.md` states the recorded attribution and the merge
method that preserves it. Fiat's `SKILL.md` carries the phase note and a
`fiat-final-integration` promise whose Boundary says the receipt does not
establish that GitHub will list anyone. `EVOLUTION.md` carries exactly one new
generation row, `fiat-v5.14.1`, retaining `state-shape-validation`, its digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa` and the held
issue 363 target byte for byte. Hexaemeron moves to `1.5.7` in all three
manifests. `plugins/hexaemeron/docs/fiat-merged-attribution/proof.md` replays
the demo path from a clean checkout. Prove it with:

```bash
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" README.md docs/how-to-help-shoggoth.md plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/references/push-discipline.md plugins/hexaemeron/docs/fiat-merged-attribution/proof.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py README.md docs/how-to-help-shoggoth.md plugins/hexaemeron/docs/fiat-merged-attribution/proof.md
bash -c 'set -e; sed -n "/^```bash$/,/^```$/p" plugins/hexaemeron/docs/fiat-merged-attribution/proof.md > /dev/null'
```

The proof's own replay instruction is the demonstration: run its Bash blocks in
order in one shell from a clean checkout and require every block to exit 0.

Keep the edit off issue 515's text. That run appends a
`<!-- contributors:start -->` thanks block at the end of `README.md` and
touches neither the contributor-list sentence nor the guide, so this step
changes `README.md:57-61` and the guide and leaves the tail of the file alone.

**Files.** `README.md`, `docs/how-to-help-shoggoth.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `tests/test_version_propagation.py`,
`tests/test_evolution_contract.py`,
`plugins/hexaemeron/docs/fiat-merged-attribution/proof.md`,
`.horos/boundary.json`, and `.hexaemeron/run-pr.md` for the run-level body.

**Tests.** Update the two pinned tests rather than adding behaviour tests.
`tests/test_evolution_contract.py` moves its Fiat assertions to `fiat-v5.14.1`
and keeps the frontier revision, digest, status and held target unchanged;
`tests/test_version_propagation.py` moves Hexaemeron to `1.5.7`. Counts stay at
roughly 192 root and 892 Hexaemeron. Elenchus runner contract:
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `elenchus.unittest.v1`, report file `tmp/elenchus/step-4.json`.

**Disciplines.** phylax: none, the step ships prose, metadata and a replay
document and opens no boundary. ephoros: none, nothing new runs unattended;
the emissions were settled in steps 2 and 3. metron: none, no performance
claim. elenchus: none at entry; the proof's replay is the failure surface, and
a block that does not exit 0 is worked under the runner contract above.
hypomnema: the ledger row and the public statement are both records, and both
are named in study item 12 with their homes.
