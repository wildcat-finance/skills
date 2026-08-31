# Fiat author and publisher separation runbook

## Step 1: Separate governed authorship from publication

### Scope and exit

**Goal.** Preserve Shoggoth authorship while an explicitly authorised human committer, signer and pull-request account restores GitHub-verifiable publication.

**Entry.** `main` at `d427e750de6b4b728cead9f7bdce1328e5eaa62d`, with issues #906 and #903 open and the study in this directory accepted by Protasis.

**Composition.** Before publication, `origin/main` advanced to `a8289d46f68b29b315ce39182abf206d03776da5` through pull request #922 and assigned ADR-051. Merge that exact tip, retain its ADR, move this decision to ADR-052, regenerate the portable runtime and Horos boundary, and rerun every affected gate before signing the composition commit.

**Exit.** Commit the study, runbook and ADR; update the identity and Fiat contracts; record author and committer separately from one GitHub commit response; reject runtime-host committers locally and remotely; keep legacy attribution readable; advance Fiat to `fiat-v5.38.1` without moving its frontier; advance the installable Hexaemeron package to `1.6.12`; review and recheck the version-bound beginner primer; regenerate portable runtime copies; and demonstrate a Shoggoth-authored, Laurence-committed commit that passes `git verify-commit`, pushes under `laurenceday`, and returns `verified: true`, `reason: valid`. Prove the changed surface with `python3 -m unittest plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_issue_429_recovery.Issue429RecoveryTests.test_integrated_controller_digest_reaches_every_promise_binding tests.test_shoggoth_identity`, `python3 -m unittest discover -s tests`, `python3 scripts/promise_machine.py check`, the repository prose lints over changed prose, and `git diff --check`. Also run `TMPDIR=/private/tmp python3 plugins/hexaemeron/tests/run_tests.py --jobs 12`; preserve any unchanged-base failures as evidence for issue #889 rather than broadening this emergency repair.

### Files and tests

**Files.** `SHOGGOTH.md`; `docs/decisions/{ADR-016-attribute-governed-agent-work-to-shoggoth.md,ADR-052-separate-governed-authorship-from-publication.md}`; `docs/a-child-or-a-golden-retriever-study.md`; `scripts/build_child_or_golden_retriever_primer.py`; `plugins/hexaemeron/docs/fiat-author-publisher-separation/{study,runbook}.md`; `plugins/hexaemeron/skills/fiat/{EVOLUTION.md,SKILL.md,references/push-discipline.md,scripts/hexctl.py}`; `plugins/hexaemeron/tests/{hexctl_harness.py,test_hexctl.py,test_fiat_skill.py,test_issue_429_recovery.py}`; `tests/{test_child_or_golden_retriever_primer.py,test_evolution_contract.py,test_shoggoth_identity.py,test_version_propagation.py}`; both Hexaemeron plugin manifests and both marketplace manifests; generated portable-runtime copies and their manifest; `.horos/boundary.json` if its deterministic scan changes.

**Tests.** Add focused positive and refusal cases to the existing unittest suites. The positive case has author Shoggoth and committer Laurence; negative cases cover a runtime-host committer and malformed GitHub committer shapes; the receipt test asserts separate author and committer accounts and no `@` address. Run the exact commands in Exit. This is a direct emergency delivery rather than a Fiat-created step, so no Warden `{report}` runner contract applies.

### Discipline routing

**Disciplines.** phylax: Git and GitHub identity fields are external inputs and must remain bounded and secret-safe. ephoros: none, no new unattended runtime. metron: none, no performance claim. elenchus: positive and negative identity guards must fail on the parent behaviour and pass with the repair. hypomnema: ADR-052 records the durable author/publisher split and its evidence boundary.
