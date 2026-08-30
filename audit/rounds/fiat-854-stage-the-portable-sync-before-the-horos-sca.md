## Step 1, round 1 -- 2026-08-30T05:51:15Z

Audit schema: fiat-audit-round/v2

Covered: index-write-scope=not-applicable; index-write-environment=not-applicable; non-repository-root=not-applicable; import-target-traversal=not-applicable; partial-write=not-applicable; boundary-counts-churn=reviewed; closure-check-cost=not-applicable

Not checked: x-ray, solidity-auditor and fizz did not run; the `security_suite` receipt waives them because the run ships no Solidity and no Foundry or Hardhat project, and this step ships two Markdown documents and one regenerated JSON artefact. Six of the seven register concerns sit at boundaries steps 2 and 3 open and no code implementing them exists at this commit, so they were read as not-applicable rather than reviewed. The step's own content was not re-audited for correctness: both documents are byte-identical copies of artefacts already receipted and lint-checked in the study and runbook phases, established here by `cmp -s` against `.hexaemeron/study.md` and `.hexaemeron/runbook.md` rather than by re-reading them. The five failures in `plugins/hexaemeron/tests/run_tests.py` were confirmed to reproduce on pristine `origin/main` at `4fe374dd` and `7e97b519` and are filed as wildcat-finance/skills#932; that suite is omitted by `scripts/run_checks.py` for this diff and no claim is made here about whether those five are repaired.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: boundary-counts-churn was the one concern this step could actually move, and it moved exactly as issue #842 predicts and no further: `.horos/boundary.json` changed by the single line `files_walked` 2077 to 2079, with all 135 entries and every byte tally (`bytes_binary`, `bytes_content_addressed`, `bytes_generated`, `bytes_lockfile`, `bytes_vendored`) byte-identical before and after. The delta is the two added documents, and it confirms they classify as readable source earning no boundary entry rather than as a sink. Whether that counts field should move at all belongs to #842 and is a stated non-goal of this run. Not pursued: re-reading the two documents for content, since the receipted artefacts are the authority and a divergent reading here would contradict a gate that already passed; and the `plugins/horos/examples/fixture-sol/Market.sol` pair of source-level dangling imports, which the study records and step 3 is specified to leave failing in neither tree.

## Step 2, round 1 -- 2026-08-30T06:14:22Z

Audit schema: fiat-audit-round/v2

Covered: index-write-scope=reviewed; index-write-environment=reviewed; non-repository-root=reviewed; partial-write=reviewed; boundary-counts-churn=reviewed; import-target-traversal=not-applicable; closure-check-cost=not-applicable

Not checked: x-ray, solidity-auditor and fizz did not run, under the recorded `security_suite` waiver; this step ships Python and no Solidity. The three bundled lints each exited 0 over `scripts` and `tests`. Concurrency was not examined: two syncs racing the same index would contend on `.git/index.lock`, which is git's problem rather than this script's, and no caller runs them in parallel. The behaviour of `git add` under a pathspec containing a submodule boundary was not exercised, because the mirror contains no submodule. The finding below was reached by executing `git add` against constructed trees rather than by reading the code, and the exit codes quoted are measured, not inferred.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | scripts/portable_promise_machine.py | staging was unconditional, and `git add --all -- <path>` treats an ignored pathspec as an error: measured exit 1 against a constructed repository whose `.gitignore` covered the path, and exit 128 against a path that does not exist. `stage_runtime` raised `PackageError` on that exit, so `sync` began failing in any repository that ignores its generated mirror, which is a working configuration and precisely the copy-mode install the skip path was written to protect. The step turned a silent wrong answer into a loud wrong one for that consumer. Fixed by asking `git check-ignore -q` before staging and returning a named skip status; a genuine staging failure still raises. Guarded by `test_a_repository_that_ignores_the_mirror_skips_staging`, which cannot pass without the check because the status string it asserts does not otherwise exist and the unfixed path raises instead | fixed in b52d01879b6eff1b6117b9e128f2adf0d7004858 |

Leads not pursued: the pathspec scope and the stripped environment were the two concerns the register named for this step and both hold under test rather than under reading. `test_staging_leaves_an_unrelated_working_tree_edit_alone` fails if the pathspec widens, and `test_staging_puts_the_written_mirror_in_the_scan_universe` fails when `stage_runtime` is replaced by a no-op that still reports success, which was run as a mutation and produced `'.agents/skills/promise-machine/runtime/AGENTS.md' not found in {'PROMISE_MACHINE.md'}`. That mutation is the evidence the guard can fail; it is not committed, because a permanently neutralised helper is not a test. Not pursued: whether `sync` should stage the boundary as well. It should not, because the boundary does not exist until the scan that follows has run, and staging it here would mean staging a stale one. Not pursued: whether `git add` should use `--force` for an ignored mirror, which would stage a file the repository asked not to track and is a decision for that repository rather than for this script.

## Step 2, round 2 -- 2026-08-30T06:15:21Z

Audit schema: fiat-audit-round/v2

Covered: index-write-scope=reviewed; index-write-environment=reviewed; non-repository-root=reviewed; partial-write=reviewed; boundary-counts-churn=reviewed; import-target-traversal=not-applicable; closure-check-cost=not-applicable

Not checked: the same suite waiver holds and the Pashov pair did not run. This round audits the tree with S2-R1-01's fix applied, which is what it exists to do; the fix added one branch and one test and changed nothing else, so the reader, the pathspec and the environment were re-read rather than re-derived. `sync` was run again against the real tree and reported `(staged)` with the mirror unchanged, so the fix did not disturb the path it was not about. No regression was introduced by the fix: the module's suite goes from 10 to 11 cases and all pass, and the root suite is 532 at 0 failures.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the one lead this round could still have taken is whether `_git_ignores` should distinguish an ignored mirror from an ignored ancestor, since `check-ignore` answers yes in both cases. It is not pursued because the two want the same behaviour: in either case the repository has asked not to track the mirror, and staging it anyway would override that. Carried unchanged from round 1: whether `git add --force` would be right for an ignored mirror, which remains a decision for the consuming repository.

## Step 3, round 1 -- 2026-08-30T06:30:28Z

Audit schema: fiat-audit-round/v2

Covered: import-target-traversal=reviewed; closure-check-cost=reviewed; index-write-scope=not-applicable; index-write-environment=not-applicable; non-repository-root=not-applicable; partial-write=not-applicable; boundary-counts-churn=reviewed

Not checked: x-ray, solidity-auditor and fizz did not run, under the recorded `security_suite` waiver; the step ships Python and reads Solidity as text without compiling it. The check does not parse Solidity, so an import inside a block comment or a string literal would be read as an import; the mirror carries none today, measured by grepping for comment-led and quoted import lines and finding zero, and the consequence of a false positive is a refusal a human reads rather than a silent pass. Non-relative imports are out of scope by the study's own non-goal, so a remapped or bare-scope target is skipped and nothing here claims otherwise. Python and Markdown closure were not examined; the observed defect was Solidity and the study scoped the check to it. The check reads only files already loaded into the payload plus one `is_file` probe per candidate under the source root, so no traversal outside the tree occurs even before the resolver's refusal.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | low | scripts/portable_promise_machine.py | the import pattern missed `import "./A.sol" as N;`, a legal Solidity form, because it required the semicolon to follow the closing quote directly. The consequence is the worst kind for this check: a lost import written that way would have been skipped in silence and the check would have exited 0, which is the exact failure the step exists to end. Reached by enumerating the legal import grammars against the compiled pattern rather than by reading the mirror, since the mirror happens to contain none of that form and reading it would have shown nothing. Fixed by admitting an optional trailing alias, and guarded by `test_every_legal_import_form_naming_a_path_is_seen`, which asserts all six forms resolve to the same path and fails on the unfixed pattern | fixed in ee5d67044d76b19d48192629ba3927f0d8f4c5ab |

Leads not pursued: the differential rule was checked in both directions rather than assumed. Against the real tree the check reports nothing across 88 mirrored Solidity files and 265 relative imports, including the two in `plugins/horos/examples/fixture-sol/Market.sol` that resolve in neither tree and must stay accepted. Dropping `plugins/janus/harness/src/wildcat/IRoleProvider.sol` from the payload reproduces skills#329 exactly and reports `HonestAccessHook.sol imports ./IRoleProvider.sol: plugins/janus/harness/src/wildcat/IRoleProvider.sol is in the source and absent from the mirror`, so the check catches the case it was written for. Not pursued: making the check compile or parse Solidity, which would buy comment and string awareness at the cost of a toolchain dependency this repository does not otherwise need for a packaging script. Not pursued: extending closure to Python or Markdown, which is a larger surface with no observed defect behind it. Not pursued: whether a bare-scope import such as `@openzeppelin/...` should be resolved through a remapping file, which belongs to whoever owns the Solidity build rather than to the mirror check.

## Step 3, round 2 -- 2026-08-30T06:31:01Z

Audit schema: fiat-audit-round/v2

Covered: import-target-traversal=reviewed; closure-check-cost=reviewed; index-write-scope=not-applicable; index-write-environment=not-applicable; non-repository-root=not-applicable; partial-write=not-applicable; boundary-counts-churn=reviewed

Not checked: the suite waiver holds and the Pashov pair did not run. This round audits the tree with S3-R1-01's fix applied. The fix widened one regular expression and added one test; the resolver, the differential rule and the caller were re-read and not re-derived. The parser limits stated in round 1 are unchanged and are limits rather than findings: the check still reads Solidity as text, so a commented or quoted import would be read as one, and non-relative targets remain out of scope by the study's own non-goal.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the widened pattern was checked for over-reach as well as reach, because a looser regex is the obvious way to break this fix. The optional alias clause admits only `as` followed by one identifier before the semicolon, so it does not begin matching statements that are not imports, and the real tree still reports zero failures across 88 mirrored Solidity files with the mirror byte-identical before and after. All 18 cases in the module pass and the root suite is 539 at zero failures. Carried unchanged from round 1: Solidity is not parsed, closure is not extended to Python or Markdown, and bare-scope imports are not resolved through a remapping file.

## Step 4, round 1 -- 2026-08-30T06:36:56Z

Audit schema: fiat-audit-round/v2

Covered: index-write-scope=reviewed; index-write-environment=reviewed; non-repository-root=reviewed; import-target-traversal=reviewed; closure-check-cost=reviewed; partial-write=reviewed; boundary-counts-churn=reviewed

Not checked: x-ray, solidity-auditor and fizz did not run, under the recorded `security_suite` waiver; this step ships one Markdown record and changes no code. The register's seven concerns were re-read against the demonstration rather than against fresh code, because the demonstration is what exercises them from outside: the demo path runs `sync` and `check` over the real tree and the record states each control in prose that was compared against the implementation it describes. The record's claims about rejected alternatives were checked against the measurements they cite rather than accepted as written; the 218-of-265 count and the two `Market.sol` targets were recounted from the tree at this commit and both match. No claim is made that ADR-055 keeps its number: the collision check passes against `origin/main` at this commit and the number is re-read immediately before the integration merge, which the runbook now requires.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the demonstration was run in the documented order with no manual stage between `sync` and `scan`, which is the claim the run exists to make, and `test_boundary_currency` passed over the result at 7 cases. One thing worth stating rather than leaving implicit: the record's own file was staged before the demo path ran, because it is a hand-written file and the fix is about the sync's own output rather than about an author forgetting to add their work. Running the demo without that stage would fail, and would fail correctly. Not pursued: whether the demo path belongs in CI as a test rather than as a documented sequence, which would turn the ordering claim into a standing guard; `tests/test_boundary_currency.py` already fails when the committed boundary drifts, so the marginal gain is small and the change is larger than this step. Not pursued: renumbering ADR-055 now, since `main` moves several times an hour here and the correct moment is immediately before the merge.
