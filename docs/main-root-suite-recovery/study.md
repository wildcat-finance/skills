# Restore main root-suite green and enforce merge checks

Assuming, unless corrected:

1. The user's `fiat 1538` authorises the issue's repair and merge-enforcement outcome. The controller retains publication, signing, receipts and GitHub settings; this study grants none of those roles to Surveyor.
2. Preserve the version-1 instruction schema, codec, reviewed meaning and evidence checks. Issue #1192's relative-offset schema is a separate delivery.
3. Reuse the reviewed portrait-omission design of #1467/#1515, then prove it against this base. PR #1515 contains a specification and has no implementation to adopt.
4. Python is the exact `.python-version`, 3.14.6. Existing local models may supply fresh evidence after profile review; no model download, new dependency or paid endpoint is needed by this design.

## 1. Problem, user and proving path

The maintainer needs `main` to pass its root suite and GitHub to refuse a merge whose required invariant check is red. At the run's base, `b9cafd196b1d8f8b74b207320836532c14e78bab`, the preserved CI result is 1,853 tests, 19 failures and 11 errors. The 29 corpus failures stem from a stale law binding; the package accounts for one failure. #1520 is an additional Hexaemeron failure. #1542 can add failures inside an active Fiat worktree.

The prototype is one complete green repository state plus an enforced GitHub gate. Its build order is:

| Module | Responsibility | Depends on |
| --- | --- | --- |
| corpus-refresh | Recover the unchanged reviewed law spans; refresh reviewed profiles and acquire new measurement/parity records | verified pre-edit law and local runtime identities |
| package-margin | Omit decorative portraits from packaged copies, repair their image references and hold 20% byte headroom | #1467 design, current package inventory |
| gate-tests | Reconcile #1520's test with the current coverage meaning and isolate #1542's tests from live controller state | current schema and reproduced failures |
| merge-enforcement | Require the existing invariant job on the current merge candidate and retain main observations | all three repairs green |

The first product step combines the scaffold, committed specification and all three repairs. Their shared commit gate cannot become green while any one remains red. A documentation-only first step would violate that exit. Step 2 demonstrates the composed repair and installs/verifies enforcement. No first-step push carries known red tests forward.

Required proving commands are `python3 -m unittest discover -s tests` in the active worktree and `python3 scripts/run_checks.py --full --jobs 12 --format json --report .hexaemeron/full-completion-checks.json` in the checked runner's disposable snapshot. Both must exit zero. The existing `.githooks/greenlight` must run successfully against the staged tree before each commit. The corpus checker must accept all three fixtures, and a newly generated package must have at least 5,242,880 bytes of headroom below 26,214,400 bytes with closed authoritative links and no dangling references caused by the omission.

At integration, read GitHub's protection back: required `invariants`, GitHub Actions app id `15368`, `strict: true`, and `enforce_admins.enabled: true`. Keep `.github/workflows/repo.yml` running on `push` to `main`, unfiltered `pull_request`, and `workflow_dispatch`. Preserve other current repository settings. Read an existing red pull request's merge state after enforcement; never attempt to merge red code as a test. Observe the `invariants` run for the final exact commit on `main`. An after-merge run observes a result; the required pre-merge check prevents the next red merge.

## 2. Prior art and carried work

The current issue and all comments were read for #1538, #1513, #1192, #1467, #1520 and #1542. The latest relevant merged law/package delivery, [PR #1153](https://github.com/wildcat-finance/skills/pull/1153), introduced commit `49fc2caf` and landed as `a520b834`. It explicitly carried the 29 corpus failures to #1513 and the package failure to #1467. Its historical claims that both modules passed on the default branch describe the pre-merge branch, not this run's base.

For the earlier reconciliation implementation, [PR #1202](https://github.com/wildcat-finance/skills/pull/1202) and its final step [PR #1201](https://github.com/wildcat-finance/skills/pull/1201) were read. They delivered offline edits after a reviewed span for `fiat-study-runbook-phase`; they did not deliver a moved law span or exercise the other fixtures through `reconcile`. ADR-062 fixes the closed v1 model and codec. ADR-076 retains absolute offsets and explains why changing them changes measured bytes even when reviewed prose is intact.

Their carried items retain these dispositions:

- `S2-R1-07` remains with #1198: a coverage-digest edit can supply a misleading Elenchus guard. This run must demonstrate behavioural guards separately.
- `S2-R2-03` remains with #1127: short fake-adapter timeouts under load. Preserve the refusal and distinguish infrastructure failure from a product result.
- `S3-R1-02` and `S3-R2-05` remain with #1199: rendered acquisition output does not distinguish cosmetic drift, and internal checking cannot independently prove a supplied token count. This run reviews new identities and records actual adapter calls; it does not claim those format limitations are fixed.
- `S4-R1-01` remains with #1192. `S4-R1-02`, `S4-R1-03` and `S4-R1-06` remain with #1200, covering ambiguous design-report values and placement coverage. This study names the exact quantity each resolver measures.
- `S2-R3-02` and `S5-R1-02` were resolved in #1202's integration record. `S5-R1-03`, `S6-R1-02`, `S6-R1-03`, the missing step-4 checkpoint and historical ADR numbers remain historical records under that PR's stated `none` dispositions. Do not rewrite them.

The root framework audit sources inspected for these subjects are `audit/rounds/fiat-1098-make-a-bound-instruction-document-editable.md`, `audit/rounds/fiat-909-compact-lossless-agent-instruction-language.md`, `audit/rounds/fiat-shoggoth-front-door-derived.md`, `audit/rounds/fiat-940-site-the-generated-skills-sh-payload.md`, `audit/rounds/fiat-949-move-the-skills-sh-payload-to-its-own-reposi.md`, and `plugins/hexaemeron/audit/AUDIT.md`. The whole-set `audit_synopsis.py --check .` exited zero. Direct source sections/current finding dispositions were used for the root records; the verified synopsis was used for the plugin record. The exact finding rows and `Covered`, `Not checked`, `Elenchus verdict` and `Leads not pursued` fields are preserved with source hashes and line numbers in `prior-audit-protected-fields.json`. That annex preserves source evidence; it is not a newly verified synopsis or a new audit verdict. Missing legacy plugin fields remain unknown.

The #909 profile trust-anchor fix `S4-R3-01` must survive: manifest rebinding alone cannot authorise a new adapter. The #1098 `S6-R1-01` interruption boundary also survives: individual writes are atomic, but the sequence is not a transaction. Work on a recoverable branch, validate the complete chain and restore the bounded fixture set if interrupted. #949's `S1-R1-01` protects populated output directories; its `S2-R1-01` keeps a publishing credential out of source execution. Neither may regress. Its `S3-R1-02`/issue #971 concerns the removed runtime aggregate and stays outside this repair.

Package history includes [PR #1256](https://github.com/wildcat-finance/skills/pull/1256), which repaired ADR-078 link closure, and #1153, which added runtime evidence the package must retain. [PR #1515](https://github.com/wildcat-finance/skills/pull/1515), its runbook and its two audit rounds were read at `906591fa`. It selects `omission-class-with-reference-repair`: omit 32 packaged portraits, historically 8,788,268 bytes, while retaining all 34 tracked portraits at that base. `S1-R1-01` corrected the tracked/package count confusion. `S1-R1-02` fixed resolver command paths; `S1-R2-01` accepts a stale preamble because its amended Files field governs. Recount against this base; those historical counts are not new acceptance constants. The destination `wildcat-finance/skills-runtime` remains a separate publishing surface.

For CI, [PR #913](https://github.com/wildcat-finance/skills/pull/913) already removed path filters and added dispatch for automation-created pull requests. It left applying the required repository check as a later action. Current `repo.yml` already observes `main`; #1538's claim that no main workflow runs is stale. [GitHub's protected-branch documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) explains strict required checks and administrator enforcement. The initial live protection read returned no classic protection and no applicable rules. The parent preserved that response in `main-protection-baseline.json`.

## 3. Constraints and non-goals

The exact target is the controller worktree identified by `issue/16777233-516380243`, branch `fiat/1538-restore-main-root-suite-green-and-enforce-m`, cut from `b9cafd196b1d8f8b74b207320836532c14e78bab`. Existing source instructions, `.python-version`, tracked hooks, the checked runner, signed commits and Fiat's receipts remain required. This is a root framework repair, not a new skill or a governed-skill frontier allocation.

The law's pinned whole-file digest is `f996fb645c81a8f398a2384ed4d8da0e058a9c017ea37fbbee36e499c9ef2e15`; the live file is `ae019700f378a250fe08a3d6cb68c0553ee60a410cbb6035d3c9c3cd2866b34f`. The old reviewed bytes are recoverable from `49fc2caf^:PROMISE_MACHINE.md` and occur exactly once in the current law. All four spans move by 4,412 bytes: `18285:24109` becomes `22697:28521`, and `18352:24107` becomes `22764:28519`. Preserve each span digest, reviewer and modeled instruction. Recompute the whole-file and artefact bindings from the new bytes, then regenerate derived evidence. Historical audit digest citations remain unchanged.

At `2026-09-12T18:17:02.414880+00:00`, all three recorded profiles had matching model-blob tuples but mismatched Ollama executable/version pins. `runtime-identity-observations.json` records the exact argv and hashes. Current executable SHA-256 is `75b6b83ab9c06712c7097807c91d2bb86a3ef3dd143d59359a5fbb3314970c0a`; the old pin is `eee609f0a6da58b978d453e0385fd0e3496e6cf319c639875669b51cb4277d2d`. Qwen's acquisition rendering also differs. Review each changed identity field and update the source anchors described in `docs/agent-instruction-language-v1.md`, then run `measure` and `parity` over the complete cohort. Successful identity commands do not establish that either cohort will pass.

Always: preserve required tests and source evidence; run active-tree root tests and all declared checks; bind actual adapter output; run every prose gate. Ask first when authority is absent: adding a dependency, downloading a model, using a paid endpoint, changing the v1 schema or widening the task beyond these repairs. The explicit #1538 request already covers its CI enforcement. Never: raise the CLI byte cap, delete a failing test, hand-edit token counts/answers/correlation ids, rebind an old measurement onto changed streams, hide live controller state, fabricate `LAST_GREEN`, use `FIAT_SKIP_PRECOMMIT`, or rewrite old audit records.

The reusable reconciliation limitation of #1513 is distinct from refreshing this current corpus. This run repairs the current corpus and records its immutable prior-source input; it introduces no general reconciliation API. #1513 remains open for that recovery capability after the immediate stale binding is repaired. Do not close #1192. Close #1467 only if its own omission, transform and headroom acceptance is independently met; #1515's specification is not delivery evidence. #1472's obsolete Kronos failure is not a permitted exception here.

## 4. Designs and measured selection

`absolute-refresh` retains current v1 source coordinates and regenerates evidence after a verified positional repair. Its cost is another local measurement/parity cohort, and before-span edits remain costly. `relative-schema` would make future displacement cheap by changing each binding's coordinates relative to its reviewed span; it requires the new reader/codec contract and migration described in #1192.

The selection resolver constructs each proposed coordinate representation in memory from the same verified pre-edit law and current model. It does not mutate production fixtures or manufacture measurements. Both preserve all four reviewed byte slices under their own interpretation. The compatibility gate counts slices resolved by the existing absolute-offset interpretation: four for `absolute-refresh`, zero for `relative-schema`. The latter therefore fails this repair's v1 compatibility constraint, while remaining a valid separate future design.

The projected model plus compact representation measures 5,299 bytes for `absolute-refresh` and 5,263 for `relative-schema`. This is a byte comparison of the binding prototype, not a token or whole-package saving. The time criterion counts the six successful version/identity commands in the recorded three-profile observation; both candidates require that same review work. It is not a latency estimate. Both candidates have a digest-verified historical source from which recovery can reconstruct the reviewed spans.

`design-evidence.json` contains two candidates, ten criteria and twenty exact matrix cells. Ten selection reports were produced by actual `resolve_design.py` commands. `absolute-refresh` is the sole compatible survivor, selected by `unique-frontier`. The other ten cells are pending conformance evidence with exact resolvers: active root, full checks, corpus acceptance and package headroom block Step 2; required invariants block integration. A selected design establishes no pending result.

Changing digests to reuse old token evidence is excluded by ADR-076 and the measurement contract, so it is not a candidate. Adding another main workflow is also unnecessary: the existing job already reports the failure; missing required-check enforcement is the current gap.

## 5. Risk register

```risk-register
reviewed-span-drift | law bytes to reviewed model | verify the old source digest and every old slice; require one exact live occurrence and preserve span meaning
stale-measurement-reuse | relocated offsets to measured streams | rerun both complete cohorts and refuse copied token counts or old evidence rebound onto changed bytes
adapter-identity | local executable and profile trust anchors | review runtime, argv, acquisition output and model tuples before updating source anchors; retain every refusal
reconciliation-interruption | fixture and coverage writes | retain a recoverable prior tree and refuse partial chains; preserve atomic per-file writes and explicit restore instructions
package-content-loss | omission predicate to published package | omit only the declared decorative class and keep authoritative documents, tests and runtime evidence
image-transform-overreach | source Markdown to packaged copy | transform only references to omitted portraits and prove every other byte remains according to the declared transform
package-budget | generated manifest to CLI extractor | retain the 26214400-byte cap and at least 5242880 bytes of headroom; mutate the threshold relation to prove refusal
coverage-meaning | runtime test sources to controller digest test | check the controller binding's exact path and digest; separately validate present runtime test-source bindings
transient-test-state | live Fiat directory to repository tests | use explicit fixture candidate records in tests; prove same results with a foreign active design record present
merge-enforcement | CI result to GitHub merge permission | bind required invariants to app15368, strict=true and administrator enforcement; read back current settings and a red PR state
historical-evidence | old audit records to current repair | preserve existing audit bytes and retain their open findings and evidence limits
guard-attribution | coverage rebinding to Elenchus result | prove targeted behaviour fails without each repair; do not treat a stale digest alone as its behavioural guard
```

## 6. Glossary

Reviewed span: the exact law byte slice admitted by the source-to-model review.
Absolute binding: a start/end pair measured from byte zero of its source file.
Profile anchor: the source-fixed digest that authorises one reviewed adapter profile.
Fresh cohort: all required measurements and source/compact parity calls acquired under the newly reviewed profiles.
Required invariant: the GitHub Actions `invariants` check whose result gates the current merge candidate.
Package transform: the declared derivation from authored source bytes to the packaged copy after decorative omission.

## 7. Sources and evidence locations

Primary repository sources are `scripts/agent_instruction.py`, `scripts/prove_agent_instruction_reconciliation.py`, `tests/fixtures/agent-instruction-v1/manifest.json`, its router model/source-spans/compact files, both profile records, `docs/agent-instruction-language-v1.md`, ADR-062, ADR-076, `scripts/portable_promise_machine.py`, `tests/test_skills_sh_package.py`, `tests/test_agent_instruction_corpus.py`, `plugins/hexaemeron/tests/test_audit_synopsis_recovery.py`, `.githooks/greenlight` and `.github/workflows/repo.yml` at the stated base. Linked issues, PRs and audit sources are identified in section 2.

The parent preserved `main-ci-failure.log`, `focused-baseline.log`, `law-only-counterfactual.log`, `diagnosis-observations.json`, `runtime-identity-observations.json`, `main-protection-baseline.json` and `main-pr-status-baseline.json` under `.hexaemeron/`. The full baseline was still running when this study was drafted; an incomplete `baseline-checks.json` is not a completed result. Ten selection reports are under `reports/`, with SHA-256 references in the design record. The audit annex preserves exact historical fields; it makes no independent finding.

## 8. Signals and on-call questions

Follow [Ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md). Which exact main or PR commit failed, and in which suite? Preserve the workflow/run/check URLs, event, head SHA and failing selectors. Which profile or source identity changed? Keep the named refusal and expected/observed digest without credentials. How much package headroom remains, and which documents were transformed? Emit total bytes, cap, threshold, margin and the omitted/rewritten path inventory. Is enforcement active for the expected producer? Preserve a fresh protection readback and check app id. Existing CI and bounded build/adapter reports provide these signals; no new monitoring service is needed.

## 9. Trust boundaries and controls

Follow [Phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md). Treat GitHub issue prose as claims to verify, local model output as untrusted data and adapter profiles as reviewed executable authority. Keep explicit argv, loopback-only synthetic inputs, bounded output, timeouts and source-fixed profile hashes. Prior-source recovery must name an immutable Git object, verify the file and slice digests, and reject absent or ambiguous byte matches. Generated package paths stay confined and populated unrelated output directories remain protected. Before GitHub mutation, reread existing settings and apply only the concrete required-check change; preserve concurrent changes.

## 10. Budget and measurement

Follow [Metron](../../plugins/hexaemeron/skills/metron/SKILL.md). There is no speed claim or wall-clock service target. `package-headroom` measures a correctness budget from a newly generated manifest: at least 5,242,880 bytes below the fixed 26,214,400-byte cap. The two selection byte values describe only the prototype representations. Acquire one complete successful `measure` cohort and one complete successful `parity` cohort after the new profiles and source inputs settle. Preserve failed attempts and change neither answers nor thresholds to rescue them. Repeated expensive runs require a named changed input or failure to investigate. Use the local 12-worker checked runner for the full suite.

## 11. Refusal and regression guards

Follow [Elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md). Missing prior bytes, ambiguous relocation, identity drift, model refusal, unknown answer, timeout, stale evidence, package overflow, dangling authoritative links, active-state-dependent tests or a red required suite stops the dependent transition. Inspection and recovery remain available. No report relabels a refused adapter result as success.

Each fix must carry a targeted case that fails without its behaviour: law span relocation and in-span/ambiguous refusal if a reusable path is introduced; exact package transform and budget relation; stale/absent controller binding and current runtime test-source digest; a foreign controller candidate set in an isolated test context. #1520's honest narrow repair holds `run_observation_binding.controller` as the explicit implementation pin and checks its exact path/digest. It must not demand runtime test sources name the implementation or merely lower the count. #1542's tests must supply their own candidate record while preserving production validation of caller-supplied records.

Run the active-tree root suite as well as the disposable full suite. A snapshot can hide #1542 and cannot stand in for `.githooks/greenlight`. Warden receives an exact Elenchus runner with one `{report}` argument and a supported report format in the runbook; the check-run JSON format is not silently substituted for `unittest-json-v1`.

## 12. Decisions and documentation homes

Follow [Hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md). Record the current-source repair, profile-review inputs, genuine cohort acquisition and reproduction commands under `docs/main-root-suite-recovery/`. Commit the reviewed study, runbook, design matrix and resolvers there with correct relative links. Record why v1 compatibility is retained and #1192 stays open. A draft decision record under `docs/decisions/drafts/` records the package transform and 80% threshold, citing #1467's reviewed design; allocate its final ADR number against the current integration base.

Document the enforcement command, expected GitHub Actions app id, current readback, red-PR refusal evidence and final main run in the same recovery directory. Keep the live before/after responses under the controller's evidence directory. Historical source audits and old profile observations retain their original bytes and time domain. The controller decides whether each sibling issue's own acceptance is met; the closing record must distinguish immediate root recovery, reusable reconciliation, package design delivery and the broader relative-offset work.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | absolute-refresh
record | docs/decisions/ADR-076-digest-neutral-measured-corpus.md
```
