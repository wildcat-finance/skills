# Wildcat V2 wrapper subjects specification

## Source bundle

This bundle preserves the receipted #2092 study, runbook and selected design record as exact byte copies. It also holds the design model, the builder that computed the 24 selection reports, those reports and the conformance resolver. `study.md` has SHA-256 `35ee6b0f2816d49d4cf2fd775c413ba47d0f76054c169e423ee5d4d1056c5e88`, `runbook.md` `406f7b923eb18806ad1bf277d4bcc84de220a3dfc303fd5aca1566eada54307a` and `design-evidence.json` `fef4c019110a7146d94eff005b4d20cac8a39caa1d31d3fa3b036e60fe6a8f25`. Each report under `design/reports/selection/` carries the digest the design record declares for it. Controller state stays local and isn't in this bundle.

## Selection and conformance

`design/build_design_evidence.py` computes every selection value from the declared facts in `design/model.json` and runs no product code. The reports keep their original command identities, which name `.hexaemeron/design/`. To reproduce them, stage `design/` under `.hexaemeron/` in a fresh worktree at Skills `50d71a2e8c1777f8eb26db32dd8adeadb34063bd` and run that command. The builder refuses rather than replace a report that differs.

`design/conformance.py` resolves the four conformance cells the design record leaves pending by running named assertions in `plugins/alexandria/tests/test_wildcat_wrappers.py`. At Step 1 only the three `legacy-identities-hold` assertions exist. The driver runs the resolver once per criterion at Step 4, which adds the four reports under `design/reports/conformance/`.

## Step 1

Run from the repository root with Python `3.14.6`:

```sh
python3 plugins/alexandria/tests/emit_wrapper_report.py --step 1 --report .hexaemeron/steps/1/focused.json
```

Step 1 adds the registered runner `plugins/alexandria/tests/emit_wrapper_report.py`, its implementation `plugins/alexandria/tests/wrapper_reports.py`, the runner and bundle tests in `plugins/alexandria/tests/test_wrapper_report_runner.py`, `LegacyIdentityTests` in `plugins/alexandria/tests/test_wildcat_wrappers.py` and this bundle. The runner runs the named Step's classes in process, launches no subprocess and writes `unittest-json-v1` with the actual test, failure, error and skip counts to a fresh path under `.elenchus/` or `.hexaemeron/`. With `--retained` it exits 2 and writes no report unless `ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING` are both set. Any skipped test makes it exit non-zero.

`LegacyIdentityTests` pins the constructed V2 release `sha256:f2b94e967c761a871129f5889fd372e992d62de87104fb5d5a4480338f9915a1` and V1 release `sha256:cbbacc59170bdf549c56347f8a962a869a6632868606a1ce3a0e1b37c0ae3def`, both built through the fake transport at the starting commit, plus the three registry digest constants and the generated registry bytes.

## Not yet implemented

No wrapper is a capture subject on this tree. The `wildcat_v2_wrappers` plan field, the `WrapperDeployed` derivation, the `wrapper-subjects` component, wrapper epochs and log attribution, `check`'s re-derivation, the four refusals, the constructed wrapper demonstration and the retained rebuild belong to Steps 2 to 4. A passing Step 1 establishes only the runner's report counters and refusal behaviour, and the frozen legacy identities.

The selected design and the three rejected candidates are recorded in `adr/admit-wildcat-v2-wrappers-as-declared-subjects`, numberless until integration assigns it.
