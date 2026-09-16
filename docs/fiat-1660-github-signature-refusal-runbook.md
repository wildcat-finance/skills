# Runbook: refuse GitHub signatures before keyring verification

Derived from `.hexaemeron/study.md`. The selected design is locked below; the
step does not reopen the design choice.

```design-lock
schema | protasis-design-evidence/v1
sha256 | ff6f32c5616e1d8c9c7a19655bab7c40191ddffe0dc2b8b2acacb9dc75c25692
candidate | precheck-signing-key
```

Known-failure assignment: `kf-1660-github-keyring-bypass` -> Step 1
Known-failure assignment: `kf-1660-prover-keyring-precondition` -> Step 1

## Step 1: Scaffold the guard and demonstrate the refusal

**Goal.** Commit this study and runbook with their current source copies, move
the known GitHub-key classification before both verifier paths, extend the
focused regression, and make the signature prover pass under a keyring that
trusts GitHub's web-flow key.

**Entry.** The run branch
`fiat/1660-retry2-1660-github-signature-guard` at the exact source
commit `7d9c9844c3ee0242b4b54f37cfb84025582282dd`, with the study receipted at
`c12f1a3367bab7a45d8f3b21031e143d862e7e19392ce259c407bc11de92304e` and the
selected design record at
`ff6f32c5616e1d8c9c7a19655bab7c40191ddffe0dc2b8b2acacb9dc75c25692`.

**Exit.** The tracked study and runbook copies are byte-identical to the
receipted `.hexaemeron` artefacts. `verify_local_commit` reads `%GK` through
its bounded exact-object reader before either ordinary or native signature
verification and refuses `4AEE18F83AFDEB23` and `B5690EEEBB952194` with the
existing GitHub-rewrite message. The existing unknown-key and bare refusals
remain unchanged. The focused test covers a GitHub key with verifier status
zero and the native-relation call. The prover accepts local signatures, refuses
unsigned and altered objects, and refuses web-flow commit
`77bf7f15e2f857fd8fd3c2db8ad50c3f738a6883` under the current keyring. Prove
these claims with the commands in **Tests**.

**Files.** Change
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl.py`, and
`tests/prove_signature_only_refusals.py`. Create
`docs/fiat-1660-github-signature-refusal-study.md`,
`docs/fiat-1660-github-signature-refusal-runbook.md`, and
`docs/fiat-1660-github-signature-refusal-demonstration.md` as the run's
operator-facing records. Keep `docs/decisions/ADR-099-accept-any-validly-signed-authorship.md`
as the standing decision record; do not edit it in this step. Permit only the
configured append-only audit record and deterministic Horos files if their
owning checks change them.

**Tests.** Extend `GitHubSignerDiagnosis` with the status-zero and
native-relation cases. Run:

```text
python3 -m unittest plugins.hexaemeron.tests.test_hexctl.GitHubSignerDiagnosis -v
python3 -m unittest plugins.hexaemeron.tests.test_hexctl -v
python3 tests/prove_signature_only_refusals.py --candidate precheck-signing-key --out .hexaemeron/step-1-signature-refusal-report.json
cmp -s .hexaemeron/study.md docs/fiat-1660-github-signature-refusal-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-1660-github-signature-refusal-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-1660-github-signature-refusal-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-1660-github-signature-refusal-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:1
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
git diff --check
```

The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`. Its report format is `unittest-json-v1`, its
expected schema is `elenchus.unittest.v1`, and its fresh report file is
`.hexaemeron/test-reports/step-1.json`. The known-failure reports are the
`protasis-design-report/v1` files named by the study inventory; the default
keyring run is part of this step and may not be skipped as an environment
precondition.

**Disciplines.** phylax: this step reads exact commit objects and starts bounded
Git verifiers, so fixed argv, `--no-replace-objects`, the native relation
environment, the existing timeout and output caps remain in force. ephoros: the
refusal text names the GitHub key and the rewrite cause, while the prover's
exit and no-report result distinguish a checked refusal from an unproven local
signer. metron: none, because the design records bounded process count and no
performance claim is made. elenchus: the two source-bound findings are assigned
here, the parent behavior is red under the trusting keyring, and every repair
uses the exact report contract above. hypomnema: the selected ordering is
bound to ADR-099, which already holds the local-signature and GitHub-rewrite
policy; no second decision home is created.

The last command of this step is the signature prover. Its closed report is
the demonstration from the problem statement and is the evidence handed to
the audit and prose phases.

### Amendment -- 2026-09-16

**What changed.** Complete replacement Files: Change `tests/promise_machine_coverage.json` and `docs/promise-machine/obligation-gates/evaluation-run.json` when the controller source or its fixture-only evaluation tree digest changes as part of this step. These are owner-produced deterministic evidence records; keep their historical answers and prompt/corpus results unchanged.

**Why.** The guard implementation changes `hexctl.py` and its current source binding in `tests/promise_machine_coverage.json`; the portable Promise Machine check then requires `evaluation-run.json` to be recomputed from the unchanged prompt and raw-answer identities. Without those owner-produced refreshes, the full suite refuses a stale tree binding.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds.

### Amendment -- 2026-09-16

**What changed.** Complete replacement Files: Change `tests/fixtures/promise-machine/composition/cases.json`, `tests/fixtures/promise-machine/runtime/fiat-final-integration.json`, `tests/fixtures/promise-machine/runtime/fiat-receipted-delivery.json`, and `tests/fixtures/promise-machine/runtime/fiat-study-amendment.json` to rebind their owner-produced evidence references to the changed `plugins/hexaemeron/tests/test_hexctl.py` source bytes. Preserve every fixture's recorded result, field map, and historical evidence apart from that source digest.

**Why.** The guard regression changes `test_hexctl.py`, whose whole-file digest is bound by the two composition relations and the three Fiat runtime fixtures. `scripts/promise_machine.py coverage --check` refuses those stale bindings, so the same source change cannot reach a green step exit until the owner-produced records are refreshed.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds.
