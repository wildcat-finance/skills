# Wildcat V2 wrapper subjects runbook

This runbook implements issue 2092's receipted study, SHA-256 `35ee6b0f2816d49d4cf2fd775c413ba47d0f76054c169e423ee5d4d1056c5e88`, from Skills `50d71a2e8c1777f8eb26db32dd8adeadb34063bd`. The selected `declared-wrapper-subjects` design lets a Wildcat V2 interval plan declare wrapper instances in `wildcat_v2_wrappers` under rule `wrapper-deployed/v1`, admits each one only against a preserved `WrapperDeployed` log from the registry's wrapper factory naming a registry market, opens its `immutable-code` epoch at that log's block, journals its native logs in the existing `logs` journal and binds the derived set as the `wrapper-subjects` component. Python `3.14.6`, stdlib production code, signed commits and the repository's checked runner remain required. Tabularium's wrapper contexts stay with the issue's `tabularium-wrapper-context` carryover.

Always: keep every plan without `wildcat_v2_wrappers` byte-identical in release bytes, gap sentences, receipts and check results; keep the V2, pre-#1880 and V1 registry documents and their three digest constants byte-identical; refuse an unknown market, a declared wrapper with no `WrapperDeployed`, a wrapper with no code and a wrapper log outside its epoch by name; run the declared checks and sign commits as `Dr Laurence E. Day <laurence@wildcat.finance>`, author and committer, with no trailer. Ask first: a registry change, a receipt format change, a change to a preserved example or the demonstration ledger, raising the portable tripwire, a new dependency, any live RPC call. Never: edit a file under `plugins/tabularium/`; collect real wrapper data; infer an event's cause from events sharing its transaction; publish a path, count or other number derived from the retained staging trees; skip or delete a failing test; claim an unrun check.

```design-lock
schema | protasis-design-evidence/v1
sha256 | fef4c019110a7146d94eff005b4d20cac8a39caa1d31d3fa3b036e60fe6a8f25
candidate | declared-wrapper-subjects
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/alexandria/tests/emit_wrapper_report.py | build_parser | step:1
```

```version-relations
alexandria | plugins/alexandria/skills/alexandria/EVOLUTION.md | next-generation-after-integration-base
```

Step 1 supplies the one registered runner interface, and its complete bytes stay fixed after its push binding. Its parser has exactly `--step` (required, integer, choices 1 to 4), `--report` (required) and `--retained` (store true), built in `build_parser` as one literal `ArgumentParser` and three literal `add_argument` calls, on the pattern of `plugins/tabularium/tests/emit_wildcat_batch_report.py` from the issue 2087 run. Behaviour lives in the imported module `plugins/alexandria/tests/wrapper_reports.py`, which later Steps extend. Without `--retained` it runs only the named Step's constructed test classes in process, launches no subprocess and writes one fresh `unittest-json-v1` report with the actual tests, failures, errors and skips; a report path that exists, or has a symlinked parent, refuses. With `--retained` it runs `test_wildcat_v2_interval_demo`, `test_wildcat_v1_interval_demo` and `test_wildcat_estates_interval_demo`, refuses with exit 2 and no report when `ALEXANDRIA_WILDCAT_V1_STAGING` or `ALEXANDRIA_WILDCAT_V2_STAGING` is unset, and exits non-zero when any test skips, so a staged rebuild cannot pass by skipping.

The design record's four conformance cells block `integration`. Their resolver is `python3 .hexaemeron/design/conformance.py <criterion> --candidate declared-wrapper-subjects`, which runs the named `plugins/alexandria/tests/test_wildcat_wrappers.py` assertions and writes only `.hexaemeron/design/reports/conformance/`, never replacing an existing report. The driver runs it once for each criterion at Step 4's clean committed head and keeps the reports for the final `done merge-step`; no worker reruns it into that path. Step 1 publishes byte-identical copies of the resolver, builder, model and selection reports under `docs/kickoff/2092/design/`, so the committed record resolves its relative report paths.

The study carries no known-failure inventory, so each Step opens on the controller's implementation-first path. A real failure found mid-step follows Elenchus and, where it changes a receipted requirement, the append-only amendment path.

The generation relation keeps Alexandria's held transaction-index reconciliation frontier. Step 3 adds one evidenced generation row to `plugins/alexandria/skills/alexandria/EVOLUTION.md` with the matching `metadata.version` in its `SKILL.md`; integration rechecks the exact current base and resolves any generation drift through the controller's signed sync and revalidation path. Do not advance the evolution counter, change the frontier digest or change the held job.

Every Step bumps the Alexandria package once, above its pull request base and above every version any local or remote ref claims, re-checked before its push; the planned sequence is 0.7.55, 0.7.56, 0.7.57 and 0.7.58. The version surfaces are `plugins/alexandria/.claude-plugin/plugin.json`, `plugins/alexandria/.codex-plugin/plugin.json`, Alexandria's entry in `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` and `tests/test_version_propagation.py`; prove each bump with `python3 scripts/plugin_release.py --base <PR base> --head HEAD` before the push. Before every commit, finish the written-record sequence on new prose, stage, then regenerate `.horos/boundary.json` and `.horos/census.json` and stage them.

## Step 1: Scaffold the run records and freeze legacy identities

**Goal.** Supply the registered runner, the public run record and the decision draft, and pin the constructed V1 and V2 release identifiers and the three registry digests as they stand at the base, without claiming that wrapper subjects exist.

**Entry.** The run branch at the starting commit, with the study and runbook receipts.

**Exit.** The Step 1 focused tests pass and the checked runner is green:

```sh
python3 plugins/alexandria/tests/emit_wrapper_report.py --step 1 --report .hexaemeron/steps/1/focused.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope alexandria --scope lazarus --scope repo-lints --format json
```

**Files.** Add `plugins/alexandria/tests/emit_wrapper_report.py`, `plugins/alexandria/tests/wrapper_reports.py`, `plugins/alexandria/tests/test_wrapper_report_runner.py` and `plugins/alexandria/tests/test_wildcat_wrappers.py` holding `LegacyIdentityTests`. Add `docs/kickoff/2092/` with byte-exact copies of the receipted `study.md`, `runbook.md` and `design-evidence.json`, the `design/` directory holding `model.json`, `build_design_evidence.py`, `conformance.py` and every `reports/selection/` report, and a README stating what is and is not yet implemented. Add `docs/decisions/drafts/admit-wildcat-v2-wrappers-as-declared-subjects.md`. Bump the five version surfaces to 0.7.55. Update `tests/check-map-v1.json` only where ownership is missing, and regenerate `.horos/boundary.json` and `.horos/census.json`.

**Tests.** `LegacyIdentityTests` builds the constructed V2 and V1 releases through the existing fake transport and asserts the release identifiers computed at the base, in `test_constructed_v2_release_identifier_is_frozen` and `test_constructed_v1_release_identifier_is_frozen`, and asserts the three registry digest constants and the generated registry bytes in `test_registry_digest_constants_are_unchanged`. Runner cases accept Steps 1 to 4 and refuse any other; Step selection runs only the named classes and keeps errors apart from failures; the report path refuses an existing file and a symlinked parent; `--retained` without both staging variables exits 2 and writes no report, and a skipped test makes it exit non-zero; the bundle copies equal the receipted artefacts byte for byte. Expect at least 10 tests. Elenchus command: `python3 plugins/alexandria/tests/emit_wrapper_report.py --step 1 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2092-step-1.json`.

**Disciplines.** phylax: the runner writes only a fresh report file, reads two operator-named variables and launches no subprocess. ephoros: reports carry actual counters so a missing or skipped test is visible. metron: none, no performance change. elenchus: preserve a failing guard for any runner defect found. hypomnema: the decision draft records the declared-subject choice, the unknown-market refusal, the component format and the plan field.

## Step 2: Derive wrapper subjects from WrapperDeployed logs

**Goal.** Add the `wildcat_v2_wrappers` plan field and the pure functions that derive and check the wrapper subject set and its `wrapper-subjects` component from preserved logs and the registry, with no collector wiring.

**Entry.** Step 1's verified push head, with the runner interface bound.

**Exit.** The Step 2 focused tests pass, the frozen legacy identities still hold, and the checked runner is green:

```sh
python3 plugins/alexandria/tests/emit_wrapper_report.py --step 2 --report .hexaemeron/steps/2/focused.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope alexandria --scope lazarus --scope repo-lints --format json
```

**Files.** `plugins/alexandria/scripts/alexandria_lib/interval.py` for the plan field's closed shape; `plugins/alexandria/schemas/interval-plan-v2.schema.json`; `plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v2.py`, or one new module beside it, for discovery, the component and bounded gaps; a new schema `plugins/alexandria/schemas/wildcat-v2-wrapper-subjects-v1.schema.json`; `plugins/alexandria/tests/test_wildcat_wrappers.py` and `plugins/alexandria/tests/wrapper_reports.py` for the Step 2 classes; the decision draft where the build changes it; the five version surfaces at 0.7.56; `.horos/boundary.json` and `.horos/census.json`.

**Tests.** The plan field accepts one closed shape with rule `wrapper-deployed/v1` and a non-empty sorted, lowercase, unique address list disjoint from `subjects` and every registry entry, only for venue `wildcat-v2` with the `logs` class and the wrapper factory declared, within `MAX_SUBJECTS`; every other shape refuses before any request. Discovery reads only logs whose emitter is the registry's wrapper factory and whose first topic is `WrapperDeployed`, requires three topics with zero-padded addresses, and refuses a market the registry does not list, a wrapper equal to a registry entry, a wrapper named by two logs and a declared wrapper no log names, each by name. Undeclared discovered wrappers become bounded gap sentences, 16 named plus one counted. The component lists the factory, topic, discovery window and each wrapper's market, deployment log identity and declared flag, and its bytes are canonical. A plan without the field reaches none of this code and the frozen identifiers hold. Expect at least 16 tests. Elenchus command: `python3 plugins/alexandria/tests/emit_wrapper_report.py --step 2 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2092-step-2.json`.

**Disciplines.** phylax: `WrapperDeployed` records are provider-returned JSON and the plan field is operator input, both checked field by field before use. ephoros: refusals name the wrapper and the market or block at fault. metron: none, no performance claim. elenchus: guard any wrong admission or lost refusal before fixing it. hypomnema: the decision draft records the component format and the gap wording.

## Step 3: Collect, build and check wrapper subjects

**Goal.** Wire declared wrappers through collection, opening reads, epochs, attribution, build and offline `check`, so a wrapper release lists each wrapper with its epoch and journal and every acceptance refusal fires through the CLI.

**Entry.** Step 2's verified push head.

**Exit.** The Step 3 focused tests pass, the frozen legacy identities still hold, Tabularium's suite passes with no Tabularium file changed, and the checked runner is green:

```sh
python3 plugins/alexandria/tests/emit_wrapper_report.py --step 3 --report .hexaemeron/steps/3/focused.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope alexandria --scope lazarus --scope repo-lints --format json
```

**Files.** `plugins/alexandria/scripts/usdc_interval.py` for the address filter, build and check; `plugins/alexandria/scripts/alexandria_lib/venues/wildcat_v2.py` and `plugins/alexandria/scripts/alexandria_lib/interval.py` for opening reads, epochs and attribution; `plugins/alexandria/tests/test_wildcat_wrappers.py` and `plugins/alexandria/tests/wrapper_reports.py` for `WrapperReleaseTests` and `WrapperRefusalTests`; existing Alexandria tests whose closed expectations enumerate plan fields, components or check-result keys; `plugins/alexandria/skills/alexandria/SKILL.md`, `plugins/alexandria/docs/usdc-interval-collector.md` and `plugins/alexandria/README.md` where they describe V2 subjects; the generation row in `plugins/alexandria/skills/alexandria/EVOLUTION.md` with the matching `metadata.version` in `SKILL.md`; any tracked file whose `git grep` of a changed file's entry SHA-256 finds a live pin; the decision draft where the build changes it; the five version surfaces at 0.7.57; `.horos/boundary.json` and `.horos/census.json`.

**Tests.** `WrapperReleaseTests`: over a constructed staging tree whose plan declares two wrappers deployed by two preserved `WrapperDeployed` logs, `build` and `check` exit 0 (`test_wrapper_release_builds_and_checks`); the check result lists each wrapper with its market, deployment block and log position, epoch start, end and runtime-code SHA-256, and its attributed log count in the `logs` journal (`test_check_lists_each_wrapper_with_epoch_and_journal`); `check` re-derives the `wrapper-subjects` component byte for byte and refuses an edited one (`test_check_rederives_the_wrapper_subjects_component`). `WrapperRefusalTests`: build refuses, and `check` refuses a release edited to carry the case, for an unknown market (`test_unknown_market_refuses`), a wrapper with no runtime code at its first block (`test_wrapper_without_code_refuses`), a wrapper log before its epoch's first block (`test_wrapper_log_outside_its_epoch_refuses`) and a declared wrapper with no `WrapperDeployed` (`test_declared_wrapper_without_deployment_refuses`), each naming the wrapper and the block or market. A wrapper's epoch names the wrapper as proxy and implementation, and no other subject's epoch owns its logs. A legacy plan builds the same bytes and check-result keys, and the frozen identifiers hold. Expect at least 14 tests. Elenchus command: `python3 plugins/alexandria/tests/emit_wrapper_report.py --step 3 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2092-step-3.json`.

**Disciplines.** phylax: the request filter grows only by declared addresses inside the existing request and response caps, and opening reads stay in the never-split `epoch-evidence` journal. ephoros: gap sentences state wrapper immutability and single-factory provenance as not established, and undeclared wrappers stay listed. metron: none, at most one code read and one header read per declared wrapper, no speed claim. elenchus: a wrong owner or an escaped log is reproduced and guarded before repair. hypomnema: `SKILL.md`, the collector guide and the generation row state the plan field, the refusals and what stays unestablished.

## Step 4: Demonstrate the constructed wrapper release and rebuild the preserved identities

**Goal.** Run a constructed wrapper specimen and the four refusals through the CLI, hold the portable payload budget, and rebuild the preserved V2 and V1 releases from the retained staging trees with no test skipped, publishing identifiers and pass or fail only.

**Entry.** Step 3's verified push head, with the driver-exported staging variables naming the V1 and V2 staging trees restored from internal custody, the route ADR-110 records, into a private 0700 directory outside every repository.

**Exit.** The Step 4 focused tests pass, the retained rebuild passes with zero skips, and the checked runner is green:

```sh
python3 plugins/alexandria/tests/emit_wrapper_report.py --step 4 --report .hexaemeron/steps/4/focused.json
python3 plugins/alexandria/tests/emit_wrapper_report.py --step 4 --retained --report .hexaemeron/steps/4/retained.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope alexandria --scope lazarus --scope repo-lints --format json
```

**Files.** A constructed specimen helper under `plugins/alexandria/tests/` with `WrapperDemonstrationTests` and `PortableBudgetTests` in `plugins/alexandria/tests/test_wildcat_wrappers.py`; `plugins/alexandria/tests/wrapper_reports.py` for the Step 4 classes; `docs/kickoff/2092/demonstration.md` recording the CLI commands, the constructed release identifier and listing, the four refusal messages, the portable measurement, and the two retained release identifiers with pass or fail; byte-exact copies of the four conformance reports under `docs/kickoff/2092/design/reports/conformance/`; the README in `docs/kickoff/2092/`; the five version surfaces at 0.7.58; `.horos/boundary.json` and `.horos/census.json`.

**Tests.** `WrapperDemonstrationTests` runs collect over the fake transport, reconcile, build and check on the constructed specimen through the CLI, prints the wrapper listing and runs the four refusals through the same CLI. `PortableBudgetTests.test_run_adds_at_most_five_payload_files_and_100000_bytes` measures the portable payload against the base and requires at most five added files and 100,000 added bytes, and `python3 scripts/portable_promise_machine.py sync` followed by `check` exits 0 inside the root suite. The retained run passes `test_wildcat_v2_interval_demo`, `test_wildcat_v1_interval_demo` and `test_wildcat_estates_interval_demo` with zero skips; its report holds counters only, and no path, count or other value read from the staging trees enters a committed file. Expect at least 6 constructed tests. Elenchus command: `python3 plugins/alexandria/tests/emit_wrapper_report.py --step 4 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2092-step-4.json`.

**Disciplines.** phylax: the retained run reads two operator-named directories, writes no path or payload, and the driver purges the restored trees after the run no longer needs them. ephoros: the demonstration record states which identifier rebuilt and which refusal fired. metron: record the retained rebuild's wall-clock duration as an observation with no claim. elenchus: a retained rebuild that fails is reproduced on a constructed case and guarded before any repair. hypomnema: the demonstration record names what the constructed specimen and the retained rebuild establish and what stays unestablished, including wrapper immutability and single-factory provenance.
