# Joined demonstration

This is the acceptance evidence for [skills#1944](https://github.com/wildcat-finance/skills/issues/1944), conformance cell `joined-demonstration`. From the repository root:

```bash
python3 docs/deferred-runner-binding/proof.py --candidate creating-step-binding --criterion joined-demonstration --report .hexaemeron/reports/creating-step-binding-joined-demonstration.json
```

The resolver drives the checked-in controller once through a disposable Git fixture, using the fake delivery tools in `plugins/hexaemeron/tests/hexctl_harness.py`. The fixture target holds `src/core.py` and `tests/test_core.py` and has no Python test runner. Its runbook names `tests/run_tests.py` in a `step:1` row of its `command-interfaces` fence, and Step 1's Exit and Elenchus commands name that runner.

## What ran

The run on 2026-09-27, during Step 4, drove these bytes:

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, SHA-256 `eadce105f8c371ea2fda18fb8cdfb0ce45824791ebf09d7e5a27d52b7f43e502`, 1,292,780 bytes.
- `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py`, SHA-256 `6c1789b0d59d3df96a62efdafefe014dd50ef5cf553eafdf789b560c409f8932`, 41,443 bytes.

The resolver hashes both files before and after the run. It checks that the harness runs that controller and that each gate record the controller wrote names that adapter digest. The init-pinned 1.6.82 controller that drives the live run, SHA-256 `ae9ab31da97327b68e164209e1e116041831dd7949d2ad81d06a055bf112dc56`, did not run.

The run wrote two files:

- `.hexaemeron/reports/creating-step-binding-joined-demonstration.evidence.json`, SHA-256 `eca7194405883bf3cc6f9e3bd2712096fb561ce82e4a851facf90e165c927358`. It holds every raw observation, the checks derived from them, the fixture's commit ids, the digests of `proof.py`, the harness and the Elenchus parser, and the report's SHA-256.
- `.hexaemeron/reports/creating-step-binding-joined-demonstration.json`, SHA-256 `53aba529374497f88a86817b0b1e85763216b206577d1a7437efbbc73b3a7175`. It is the closed `protasis-design-report/v1` report, with value `true`.

The report's value is true only when all twelve checks hold. `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration` exited 0 with this report in place.

## Observations

The criteria are the study's section 1.

Criterion 1, no file before Step 1:

- `runbook-refuses-present-runner`, a refusal. With an untracked `tests/run_tests.py` present, `git status --porcelain --untracked-files=all` listed it, and `done runbook` exited 1 with `deferred-source-present`. State and ledger bytes did not change.
- `runbook-receipted-without-product-files`. With that file removed, the same status listed no product file outside `.hexaemeron/`, before or after `done runbook`.
- `step-one-commands-deferred`. The receipted runbook holds the row `tests/run_tests.py | build_parser | step:1`. Step 1's Exit and Elenchus commands each recorded `interface-deferred` for that path.
- `status-awaiting-binding`. `hexctl status --field gate_command_status` reported `awaiting-binding` for `tests/run_tests.py`.

Criterion 2, Step 1 adds the runner:

- `runner-created-by-step-one`. The starting commit has no entry at the path. The only commit that adds it is Step 1's receipted implementation commit.
- `push-binds-runner`. Status read `awaiting-binding` until `done push` and `current` after it. The binding names Step 1, the starting commit, the push head and a `100644` blob; the resolver read that blob's id and SHA-256 back from Git and they match. Every gate record in the binding reads `interface-valid` against that digest. The `done:push` ledger event carries the same binding as state, and `verify` passed.

Criterion 3, committed bytes must match:

- `push-refuses-worktree-mismatch`, a refusal. An uncommitted edit to the runner at the push made `done push` exit 1 with `deferred-worktree-mismatch`. State and ledger bytes did not change.
- `later-edit-refuses-drift`, a refusal. On Step 2's branch, a committed edit to the bound runner made `verify` and `done implement` each exit 1 with `registered-source-drift`. State and ledger bytes did not change, and status read `stale-or-invalid`.

Criterion 4, a fix inside Step 1 needs no amendment:

- `in-step-fix-without-amendment`. After an audit round recording one finding, a Step 1 commit added `socket.getnameinfo` to the runner's denied network events, with a guard test. This is the analogue of miskatonic#14 finding S1-R1-01. `verify` passed and status stayed `awaiting-binding`. The ledger holds no `amend:runbook` event, the runbook digest did not move, and the push bound the fixed runner's bytes.
- `fix-changes-runner-behaviour`. Under the runner as created, the guard ran 1 test with 1 assertion failure. The fixed runner, run as Step 1's Elenchus command names it, ran 2 tests and both passed. The checked-in Elenchus parser accepted both reports as `unittest-json-v1`. The runner runs its tests in its own process and imports only `argparse`, `json`, `pathlib`, `sys` and `unittest`.

Identity:

- `controller-bytes` and `adapter-bytes`, as described under "What ran".

## Exclusions

- GitHub, the remote and commit signatures are the harness's fake delivery tools. No remote state or signature was checked.
- The audit rounds are harness stand-in records, not Warden rounds. No Elenchus verdict was recorded.
- The runner's network denial is an audit hook inside one test process, not host isolation.
- Only the checked-in controller named above ran.

## What this does not establish

The evidence covers one disposable fixture. It does not show that these observations are sufficient for the issue's acceptance. It does not show that the fixture runner or its tests are correct beyond the counts recorded, or that the fixture was isolated from the host, the process table or the network. It says nothing about remote GitHub state, or about any other target, runbook or controller version.
