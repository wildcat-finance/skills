# Runbook: preserve checkpoint identity across verified restore

Assuming, unless corrected:

1. The accepted design is `transparent-relocation` from the receipted study.
2. This run changes no version-1 public schema and opens no checkpoint boundary.
3. The exact starting commit is `66f43a0e07865daf526036ad1efbf98e3e27deac`.

```design-lock
schema | protasis-design-evidence/v1
sha256 | ec5fe366ad26dfc7cbb6f0eef3db6f3808fa024868e0cae1fb7880227dd3c477
candidate | transparent-relocation
```

## Step 1: Preserve semantic identity through verified relocation

**Goal.** Make one valid `checkpoint:restore` tail transparent to semantic checkpoint identity while retaining every existing restore, anchor, prefix, source, observation, ref, ancestry, and checkpoint-boundary refusal.

**Entry.** Start from `fiat/860-restore-identity-continuation-r2` at `66f43a0e07865daf526036ad1efbf98e3e27deac`, with the receipted study and design record selecting `transparent-relocation`; the `roundtrip-and-refusals` conformance result remains pending until integration.

**Exit.** The controller reconstructs the exact accepted producer prefix only through one immediate, verified `checkpoint:restore` receipt; producer and fresh-checkout receiver print byte-identical `fiat-checkpoint-identity-result/v1` output and `snapshot_id`; malformed joins, path-delta smuggling, prefix drift, extra suffixes, legacy anchors, non-exhausted audit rounds, and every other non-boundary state refuse before stdout without writes. The checkpoint identity and controller checkpoint references state the restore join and the unchanged intra-step refusal. Tracked copies of this study and runbook are present. Prove the exit with `mise exec node@26.6.0 python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_identity -v`, then `mise exec node@26.6.0 python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py`, `mise exec python@3.14.6 -- python3 -m unittest discover -s tests`, `mise exec node@26.6.0 python@3.14.6 -- python3 scripts/run_checks.py --base 66f43a0e07865daf526036ad1efbf98e3e27deac`, the three discipline lints, Imprimatur over changed prose, Horos check, and `git diff --check`, all at exit zero.

**Files.** Amend `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md`, `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md`, and `plugins/hexaemeron/tests/test_hexctl_checkpoint_identity.py`; extend `plugins/hexaemeron/tests/test_hexctl_checkpoint.py` only if the round-trip belongs there. Create `docs/fiat-checkpoint-restore-identity-study.md` and `docs/fiat-checkpoint-restore-identity-runbook.md`. Deterministically update `.agents/skills/promise-machine/runtime/` and exact digest or coverage bindings only when their checked generators require it. Regenerate `.horos/boundary.json` and `.horos/candidates.json` only when Horos reports them stale. Warden may append this run's exact audit record and synopsis.

**Tests.** Add a parent-red, branch-green fresh-checkout restore test that re-reads identity and compares exact producer and receiver output bytes. Add hostile cases for every risk-register id, with explicit coverage of a second suffix entry, altered restore join, prefix truncation, illegal path delta, anchor/ref substitution, and non-exhausted audit state. For any audit repair, run `mise exec node@26.6.0 python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; report file `.elenchus/fiat-860-step-1.json`. A missing, stale, empty, malformed, zero-test, or infrastructure-failed report is `inconclusive`. Before integration, run `python3 .hexaemeron/design/prove_restore_identity.py --candidate transparent-relocation --out .hexaemeron/reports/transparent-relocation-roundtrip-and-refusals.json` and require the design-evidence integration transition to pass.

**Disciplines.** phylax: hostile relocated controller bytes cross into semantic identity and require closed receipt, exact-prefix, stable-read, bounded-path, and fixed-argument Git joins. ephoros: the command's bounded result and fixed refusal classes answer the study's operator questions; no persistent telemetry is added. metron: no performance claim or extra identity pass is permitted. elenchus: the existing post-restore refusal is the parent-red guard and every repair must retain a structured branch-green report. hypomnema: ADR-028 remains the decision home; the two Fiat references own only the callable mechanics and may not reopen checkpoint boundaries.
### Amendment -- 2026-09-06

**What changed.** Complete replacement Exit: The controller reconstructs the exact accepted producer prefix only through one immediate, verified `checkpoint:restore` receipt; producer and fresh-checkout receiver print byte-identical `fiat-checkpoint-identity-result/v1` output and `snapshot_id`; malformed joins, path-delta smuggling, prefix drift, extra suffixes, legacy anchors, non-exhausted audit rounds, and every other non-boundary state refuse before stdout without writes. The checkpoint identity and controller checkpoint references state the restore join and the unchanged intra-step refusal. Tracked copies of this study and runbook are present. Prove the exit with `python3 -m unittest plugins.hexaemeron.tests.test_hexctl_checkpoint_identity -v`, then `python3 plugins/hexaemeron/tests/run_tests.py`, `python3 -m unittest discover -s tests`, `python3 scripts/run_checks.py --base 66f43a0e07865daf526036ad1efbf98e3e27deac`, the three discipline lints, Imprimatur over changed prose, Horos check, and `git diff --check`, all at exit zero. Complete replacement Tests: Add a parent-red, branch-green fresh-checkout restore test that re-reads identity and compares exact producer and receiver output bytes. Add hostile cases for every risk-register id, with explicit coverage of a second suffix entry, altered restore join, prefix truncation, illegal path delta, anchor/ref substitution, and non-exhausted audit state. For any audit repair, run `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; expected schema `elenchus.unittest.v1`; report file `.elenchus/fiat-860-step-1.json`. A missing, stale, empty, malformed, zero-test, or infrastructure-failed report is `inconclusive`. Before integration, run `python3 .hexaemeron/design/prove_restore_identity.py --candidate transparent-relocation --out .hexaemeron/reports/transparent-relocation-roundtrip-and-refusals.json` and require the design-evidence integration transition to pass.

**Why.** `mise` is unavailable in this checkout; the directly invoked `python3` is exactly Python 3.14.6, so this preserves the specified interpreter while making every required command runnable.

**Steps touched.** Step 1 Exit and Tests runner.

**Still holding.** Step 1: entry holds; exit holds.
