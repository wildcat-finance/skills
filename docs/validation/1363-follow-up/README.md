# Validation follow-up to #1363

The source maps landed in [PR #1921](https://github.com/wildcat-finance/skills/pull/1921)
at `df56bfeec3f67bf689d0b083c4994fc329477905`. These observations supplement
that delivery. The original report inventory and audit receipts remain intact.

## Unittest parent replay

Native unittest counts subtests in its failure list but counts methods in
`testsRun`. Two failing subtests therefore produce one method and two failures.
The old adapter rejected this twice in the
[minimal reproduction](evidence/subtest-counter-reproducer.json).

The new `unittest-json-v3` format retains those native counters and reconciles
one outcome per method invocation. Any error still makes the result inconclusive.
V1, v2 and the caller-bound parent-guard contract retain their rules.

The [supplemental parent result](evidence/focused-parent-v3-result.json) overlays
the changed tests from `ee0552755296050e25d6aed0494ddc6bf2c6dc1e` on its parent:
51 methods execute, 10 fail through 95 subtest assertions, and none errors.
Its verdict is `guarded`. The [fixed report](evidence/focused-fixed-v3-report.json)
records 51 passing methods. The [earlier focused refusal](evidence/focused-parent-result.json)
remains evidence; this new declaration does not replace the frozen runbook command
or its inconclusive receipt.

The repair has 13 passing regression tests, including real contained parent
replays. Ten of the 11 parser/reporter cases fail on the old source; the legacy
format case passes. All 179 Elenchus tests pass.

## Pinned protocol tests

Each full run used `forge test --threads 4 --fuzz-seed 0x1363`, Solidity 0.8.25,
and the snapshot's unchanged production configuration.

| Snapshot | Commit | Foundry | Result |
| --- | --- | --- | --- |
| Candidate | `bea503c2736d47de7fd34130c64f10783dc35b39` | 1.7.1 | 706 passed, 0 failed, 0 skipped |
| Deployed | `f5a26146987926f4811b72a795d662813dedfe85` | 1.7.1 | 795 passed; two `testFail*` names rejected before execution |
| Deployed | Same pinned commit | 0.3.0 | 821 passed, 0 failed, 0 skipped |

Foundry 1.7.1 reports only the two rejected names for the inherited wrapper suite.
Foundry 0.3.0 runs all 26 methods there, explaining the different totals.
The older binary came from the official release; its API supplied no digest.
The [asset record](evidence/foundry-0.3.0-asset.json) preserves local hashes.
Both source worktrees retain their prior Git status, including deployed's existing
untracked `x-ray/` directory. These passes do not establish protocol safety.

## Coverage and CI limits

The candidate's supported command,
`FOUNDRY_TEST=test/sanctions bash scripts/coverage.sh --match-contract SanctionsTest`,
passes 11 tests. Its [record](evidence/candidate/focused-coverage-result.json)
confirms identical source hashes before and after the wrapper's temporary SphereX
patch. This uses a focused non-via-IR build and reduced fuzz/invariant settings;
it is not production-bytecode coverage. Both sanctions contracts show 100% line,
statement, branch and function coverage. Test-library source-anchor warnings
remain in stderr. Whole-suite accurate coverage remains compiler-blocked.

The original [CI failure](https://github.com/wildcat-finance/skills/actions/runs/36239898649/job/108398319318)
was `ENOTEMPTY` during a temporary Git directory's cleanup. The same head passed
on retry. Fifty targeted attempts with Git 2.50.1 and 100 with Git 2.55.0 passed
on macOS. The compressed Git trace contains 100 automatic maintenance starts;
it does not establish the failure's cause. Linux reproduction was not run.
The cleanup failure is unresolved, and no speculative fixture change ships.

[The inventory](manifest.json) binds the retained reports and logs by SHA-256.
