# Fiat installed-path and maturity proof runbook

This run has one step. The controller already exists and its installed copy
has passed 61 of 61 tests, so adding another controller feature would not
serve the held frontier job.

## Step 1: Publish the installed controller proof and close Fiat

**Goal.** Preserve the installed-path delivery evidence in the repository,
advance Fiat's evolution once, and close its exhausted frontier.

**Entry.** Clean `main` at
`60a01d4c6918e6d30b45da7677dcf6d63a936a3e`, with the active controller at
`/Users/c0rtexzer0/.codex/plugins/cache/wildcat-labs/hexaemeron/1.0.0+codex.20260816145806/skills/fiat/scripts/hexctl.py`
and live target state under this checkout's `.hexaemeron/` directory.

**Exit.** One merged PR contains prose-checked copies of the study and
runbook, a proof document recording the installed controller path and
receipt evidence, Fiat metadata version `2.2.0`, and a `fiat-v2.2.0`
evolution history row. The ledger status is `mature`, its next job is
`None -- mature`, the history digest matches the exact frontier line, all
required tests pass, and the installed controller reaches `done` with an
intact hash chain.

**Files.** Create
`plugins/hexaemeron/docs/fiat-installed-path-and-maturity-proof/study.md`,
`plugins/hexaemeron/docs/fiat-installed-path-and-maturity-proof/runbook.md`,
and
`plugins/hexaemeron/docs/fiat-installed-path-and-maturity-proof/proof.md`.
Update `plugins/hexaemeron/skills/fiat/EVOLUTION.md` and the version metadata
in `plugins/hexaemeron/skills/fiat/SKILL.md`. Change no controller code,
vendored skill, or other frontier ledger.

**Tests.** Run the installed Hexaemeron suite and expect 61 of 61 tests. Run
`python3 plugins/hexaemeron/tests/run_tests.py`,
`python3 plugins/hexaemeron/skills/imprimatur/tests/run_tests.py`, and
`python3 -m unittest discover -s tests`. Validate the changed Fiat skill
frontmatter and evolution digest. Run Imprimatur over every shipped Markdown
file and clear all hard findings. Before the phase receipt, run controller
`status` and `verify` through the installed path and copy the non-secret
receipt facts into `proof.md`.

The implementation branch is `step-1-publish-fiat-installed-proof`, based on
`main`. The audit examines provenance claims, the distinction between the
installed cache and target checkout, version-axis arithmetic, the frontier
digest, receipt accuracy, and whether maturity is supported by the observed
run. The prose phase covers the three shipped documents, changed Fiat prose,
and the PR title and body.
