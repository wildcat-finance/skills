# Demonstration: the literal base controller and the checked-in controller on one run

Resolver, run from the run worktree on the committed Step 4 head of the skills#2042 run:

```bash
python3 docs/starting-commit-gate-bindings/demonstrate.py --candidate base-commit-bindings --criterion base-commit-controller-demonstration --report .hexaemeron/reports/design/base-commit-bindings-base-commit-controller-demonstration.json
```

It writes one closed `protasis-design-report/v1` object at the named path and every other observation in a sidecar created beside it, `<report>.evidence.json`. Both are created once; an existing file or link at either path refuses `report-already-exists`, a candidate or criterion outside the one cell refuses by name, and a refusal writes nothing. The disposable workspace is removed on exit, including after a refusal. The facts below are the same on every run; the sidecar retains what varies: the fixture's commit ids, each command's wall time and the bounded stdout and stderr of every boundary.

## Controllers

| label | source | package | ledger | `hexctl.py` SHA-256 | adapter SHA-256 |
| --- | --- | --- | --- | --- | --- |
| base | `git archive d162d0952782f09659370b6a554c9cd4511b8db9 plugins/hexaemeron` | 1.6.77 | `fiat-v6.74.1` | `fa2cfc3dda1e3cef1a8a1829dbebee7e17cdd1887e0ee54e38e1c38fa2ea35f3` | `ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119` |
| unfixed | `git archive dd2e6939ed460dcd987457a398a2765822349588 plugins/hexaemeron` | 1.6.92 | `fiat-v6.78.1` | `e07e2c0065f6f2b18c01a29a312a5034889c417b8702ef25b3bdf028ee6d89ce` | `90ad7967e44a583fa5be15f15b804cccdfbd74750e1da19adaae00959dc055f7` |
| fixed | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` of the Step 4 branch | 1.6.96 | (the branch's own) | recorded in the sidecar | recorded in the sidecar |

The base and unfixed digests are asserted before either rebuilt tree runs anything; a mismatch refuses `base-controller-digest-mismatch` or `unfixed-controller-digest-mismatch` and writes nothing. The unfixed `hexctl.py` is also compared with the blob read through `git --no-replace-objects cat-file blob dd2e6939…:plugins/hexaemeron/skills/fiat/scripts/hexctl.py`. The base commit is the starting commit run #1872 recorded; the unfixed commit is this run's own starting commit, whose controller refused #1872.

Between the base adapter and the branch's adapter three `MODULE_BINDINGS` pins moved: `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, `plugins/hexaemeron/skills/protasis/scripts/protasis.py` and `plugins/hexaemeron/tests/run_tests.py`. The branch's adapter already admits the base digest of `run_tests.py`, `a806ec152583f7101efd11117b5a102153fb0786396e393a10a6cb2aeb0bbcd6`, through its reviewed prior runner pair, so the starting commit is consulted for two modules, `ephoros.py` and `protasis.py`. The unfixed adapter's pins equal the branch's.

## Fixture

A disposable Git repository whose one signed base commit holds `plugins/hexaemeron`, `plugins/brevitas/skills/brevitas/scripts/brevitas.py` and `scripts/run_checks.py` exactly as `d162d095` ships them, so every pin of the base adapter has its module in the tree. The signing key is an ed25519 key the demonstration generates under its own `GNUPGHOME` with the `gpg` that `plugins/hexaemeron/tests/fixture_tools.native_signing_tools` selects. The remote `origin` is `https://github.com/wildcat-finance/example.git` and the harness's fake `gh` from `plugins/hexaemeron/tests/hexctl_harness.py` answers the two platform reads a receipted run makes, `repos/wildcat-finance/example` and `repos/wildcat-finance/example/commits/<sha>`. A `git` shim ahead of the real `git` on `PATH` records each argv and executes the real binary, which is how the starting-commit reads below were counted. Nothing reads the plugin cache or the network.

Three runs, each in its own origin. The runbook of every run names the module #1872's runbook names, through one Exit command, `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py study.md`, and declares one step, `Gate`. Each run is driven through `init`, `done study`, `done runbook` and, for the first two, a signed `done implement` on the step branch `<run branch>-step-1-gate`. The run's state directory is snapshotted before and after every command, so a command that wrote under `.hexaemeron/` is visible as such.

## Boundaries

`state` says whether the run's `.hexaemeron/` was byte-identical after the command; `reads` counts `git cat-file` calls the controller made, each of the form `--no-replace-objects cat-file -p <starting commit>:<path>` during a replay, or `cat-file -p <starting commit>:<path>` during the since-base diagnosis.

| run | command | controller | exit | state | reads | outcome |
| --- | --- | --- | --- | --- | --- | --- |
| base | `init`, `done study`, `done runbook`, `done implement` | base | 0 | written | 0 | the receipts carry the base adapter digest and the base pins |
| base | `verify` | base | 0 | unchanged | 0 | `ok:` |
| base | `verify` | unfixed | 1 | unchanged | 3 | `gate source stale or invalid: unregistered-cli-module-bindings; registered module …ephoros.py, …protasis.py, …run_tests.py is unchanged since the run's starting commit … yet fails this controller's MODULE_BINDINGS pin, so this controller (fiat-v6.78.1 …) and the run's tree were pinned at different commits; drive the run with the controller it recorded, fiat-v6.74.1 at init …` |
| base | `status --field gate_command_status` | unfixed | 0 | unchanged | 6 | `status` `stale-or-invalid`, `cause` `controller-pin-skew`, three modules `unchanged` |
| base | `verify` | fixed | 0 | unchanged | 3 | `ok:` |
| base | `status --field gate_command_status` | fixed | 0 | unchanged | 3 | `{"provenance": {"adapter_sha256": "ac527913…", "modules": ["…ephoros.py", "…protasis.py"], "starting_commit": <fixture base>}, "status": "current", "validation": "interface-only"}` |
| base | `supersede-commit --old <receipted> --new <amended>` after a tree-identical `git commit --amend -S` | fixed | 0 | written | 7 | `receipted; original receipt retained`; the ledger's last event is `commit:supersede` |
| base | `verify`, then `status` | fixed | 0 | unchanged | 3 | `ok:`; the same `current` view with the same provenance |
| base | `verify` with one assignment appended to `protasis.py` | fixed | 1 | unchanged | 7 | `gate source stale or invalid: unregistered-cli-module-bindings; registered module …protasis.py changed inside the run since its starting commit …; submit a freshly validated runbook amendment` |
| base | `status --field gate_command_status` with the edit in place | fixed | 0 | unchanged | 11 | `cause` `module-edited-in-run`; `modules` `[{"module": "…protasis.py", "since_base": "changed", "named_by_runbook": true}]` |
| base | `verify` with the module restored | fixed | 0 | unchanged | 3 | `ok:` |
| forged | `init` … `done implement`, `verify` | base tree with one comment line appended to its adapter | 0 | written, then unchanged | 0 | the runbook receipt's `adapter_sha256` is the forged digest, neither reviewed nor the base's |
| forged | `verify` | fixed | 1 | unchanged | 3 | `gate source stale or invalid: gate-receipt-drift; submit a freshly validated runbook amendment` |
| forged | `status --field gate_command_status` | fixed | 0 | unchanged | 6 | `status` `stale-or-invalid`, no `cause`, no `modules`, recovery names the runbook amendment |
| legacy | `init` with the `gate_commands` marker withheld, `done study`, `done runbook`, `verify` | base | 0 | written, then unchanged | 0 | `contracts` holds `design_evidence` and `success_criteria` only; the runbook receipt has no `gate_commands` |
| legacy | `verify`, `status --field gate_command_status`, `status --json` | fixed | 0 | unchanged | 0 | `ok:`; `{"status": "legacy", "validation": "not-recorded"}`; no `cat-file` at all |

The legacy run is constructed the way the harness's historical construction builds one: the base controller's `commit` is wrapped for the `init` event only so the marker is withheld from the first ledger entry, and nothing else in that controller changes.

Every read-only command under the unfixed and fixed controllers, fourteen in all, left the state directory byte-identical. `supersede-commit` is the one fixed-controller command that wrote, and writing is its job. The three starting-commit reads of a fixed replay are the adapter blob and the two refused modules; the unfixed controller makes the same three reads for its diagnosis and then refuses, because its replay admits nothing from them.

## What the fixture does not prove

- It is not run #1872. The fixture base is a fresh signed commit holding the tree of `d162d095`, with one step, one runbook command and no amendment; #1872 carries 68 ledger entries, 25 bound commands and 17 runbook amendments. The replica of #1872 was measured at design selection, not here.
- No plugin-cache controller ran. The fixed controller is the branch's checked-in file; the run that wrote it is driven by Hexaemeron 1.6.92 from the plugin cache and validated by that controller, not by this one.
- The reviewed-list doctrine for an adapter that is not a run's own base is unchanged: the forged run shows the fixed controller refusing `gate-receipt-drift` for a digest that is neither reviewed nor the base's.
- The platform reads were answered by the fake `gh`; no GitHub verification happened and no network was used. The signing key is the fixture's own; nothing here concerns the repository's signing key.
- The `git` shim observes argv for the commands it wrapped. "No `cat-file`" on the legacy run is an observation of the recorded argv, not a proof about every read a process could make.
- The unfixed controller's diagnosis names three skewed modules where the fixed controller names two. Its `registered_module_skew` calls `parser_bindings` without the source digest, so the reviewed prior runner pair cannot match there; the replay in both adapters admits `run_tests.py` through that pair. This is an observation about the 1.6.92 diagnosis, not a defect this step changes.
- Timing is retained per command in the sidecar and is not a benchmark. The design record's `verify-wall-ms` gate, at most 5,000 ms, was measured on the #1872 replica at selection.

## Tests

`tests/test_starting_commit_gate_bindings_scaffold.py` `DemonstrationTests` pins the constants above, the resolver string the design record names, the closed arguments (an empty, short, extra or positional argument exits 2 with usage), the named refusals for another candidate or criterion (exit 1, nothing written), the `report-already-exists` refusal for an existing or linked report or sidecar, the closed report shape with the demonstration short-circuited, and that a refused demonstration writes nothing. The demonstration itself needs Git history and signing tools, so it is recorded here and not run by the suite.
