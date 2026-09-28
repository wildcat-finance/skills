# Gate commands for a repository with no runner

Assuming, unless corrected:

1. The run starts from `main` at `e992a54b4e3e4671bae98b448d57690de8dfa044` on branch `fiat/1944-gate-commands-for-a-repository-with-no-runn`, bound to [skills#1944](https://github.com/wildcat-finance/skills/issues/1944) at init. The controller is Hexaemeron 1.6.82 from the CLI plugin cache, byte-identical to this worktree's `plugins/hexaemeron` at the starting commit. Its ledgers read `fiat-v6.75.1` (frontier open) and `protasis-v6.18.1` (frontier mature).
2. The run's own runbook is validated by that init-pinned 1.6.82 controller, not by the code this run writes. Its Exit and Elenchus commands can name only the eight built-in registry scripts. The acceptance proof therefore comes from the checked-in successor controller driven in a disposable Git fixture, not from this run's own receipts.
3. The issue's phrase "binds its digest at Step 1's exit" is read as Step 1's `done push`, the last transition of the creating step, reading the pushed commit. Reason: the observed change to a new runner (miskatonic#14 finding S1-R1-01) came from Step 1's own audit loop, which ends before the push.
4. The new route covers a runner that a named step creates. This generation admits Step 1 only, because Protasis already fixes Step 1 as the scaffold step and the acceptance names Step 1. A runner that already exists, or that a later step changes, keeps today's amendment route.
5. The interpreter is Python 3.14.6, exactly as `.python-version` pins it. The change adds no dependency, network call, credential or model call.
6. No Solidity changes, so the security suite stays waived as recorded at init.

The study proceeds on these readings. No ambiguity remains that would change the selected design.

## 1. Problem statement

A Wildcat operator runs Fiat against a target repository that has no Python test runner of its own. Protasis admits a runbook gate command only as literal `python3` followed by a script that is in the built-in registry or in a `command-interfaces` row pinned by SHA-256, and the script must be readable when the runbook is receipted. At the starting commit:

- the built-in `REGISTRY` names only Skills paths ([gate_commands.py line 46](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py#L46));
- `validate` reads every declared registration from the target root at capture ([line 525](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py#L525)), and a missing file refuses `source-unavailable` ([line 102](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py#L102));
- an unregistered script refuses `unregistered-cli` ([line 187](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py#L187)), a non-`python3` command refuses `unregistered-executable` ([line 335](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py#L335)), and a runbook declaring no command refuses `command-count-bound` ([line 514](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py#L514));
- a changed registered source refuses `registered-source-drift` ([line 192](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py#L192)).

The miskatonic#14 run (Hexaemeron 1.6.82, 2026-09-26) met this. It wrote `tests/run_tests.py` into the run worktree as an untracked file before `done runbook`, registered its digest, and had Step 1 commit those bytes unchanged. When audit finding S1-R1-01 required a change to that runner, the fix needed a runbook amendment carrying a replacement `command-interfaces` fence, and the committed runbook copy and its pinned digest had to follow.

A working prototype is a successor Protasis adapter and Fiat controller that accept a registration naming a runner Step 1 creates, with no file in the run worktree before Step 1, and bind the runner's digest when Step 1 closes. From then on the ordinary pinned-source rules apply.

The acceptance text from the issue:

> A Fiat run against a repository with no Python runner receipts a runbook whose Exit and Elenchus commands name a runner that Step 1 adds, with no file in the run worktree before Step 1. A test proves the gate refuses when the committed runner bytes differ from the registration.

Restated as checkable criteria:

1. **No pre-Step-1 file.** In a disposable Git fixture of a target with no runner, the successor controller receipts a runbook whose Step 1 Exit and Elenchus commands name `tests/run_tests.py`, while `git status --porcelain --untracked-files=all` lists no product file outside `.hexaemeron/`. Proved by the joined demonstration, conformance cell `joined-demonstration`.
2. **Step 1 adds the runner.** The binding refuses unless the runner blob is absent at the run's starting commit and present, as a regular file, at Step 1's verified push head. Proved by a controller test in the new Fiat test module and by `controller-binding-custody`.
3. **Committed bytes must match.** After binding, a committed runner whose bytes differ from the bound digest refuses replay with `registered-source-drift`, and a push whose worktree runner differs from the pushed blob refuses binding. Proved by tests in both new modules and by the demonstration.
4. **In-step fixes are free.** A change to the runner inside Step 1's audit loop lands with zero runbook amendments. Proved by the demonstration's S1-R1-01 analogue.
5. **Nothing else moves.** A runbook with no deferred row yields the same gate result as 1.6.82 apart from `adapter_sha256`, and a receipt captured by the released 1.6.82 adapter replays under the successor. Proved by `released-adapter-replay`.
6. **Replay stays inside budget.** The successor adapter validates `docs/protasis-success-criteria/runbook.md` in at most 1,000 ms, median of five, at Step 2's head. Proved by `successor-replay-milliseconds`.

The demo path is `python3 docs/deferred-runner-binding/proof.py --candidate creating-step-binding --criterion joined-demonstration --report .hexaemeron/reports/creating-step-binding-joined-demonstration.json`, run from the repository root after Step 4. It drives the checked-in controller, never the init-pinned one, and its report names the controller bytes it ran.

## 2. Prior art

### In this repository

The adapter is `plugins/hexaemeron/skills/protasis/scripts/gate_commands.py`. `declared_interfaces` (line 407) accepts rows of `<path> | <builder> | <64-hex digest>` only, at most 32, with built-in overrides refused. `capture_runbook` (line 431) admits one baseline `command-interfaces` fence before Step 1 and one replacement fence per dated amendment region. `interface` (line 184) reads the source through the no-follow `read_source` (line 70) and compares the whole-file digest for a declared row. `replay` (line 603) revalidates the runbook against current source and compares the whole result with the stored receipt, admitting five released adapter digests in `REPLAY_COMPATIBLE_ADAPTERS` (line 24) and one runner timestamp pair (line 33).

Fiat loads that adapter from its own distribution (`gate_commands_module`, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:14080`). `capture_gate_commands` (line 14095) runs at `done runbook` (line 15063) and at runbook amendments (`cmd_amend_runbook`, line 20977). `verify_gate_commands` (line 14928) checks stored against ledger gate records and replays the latest one. `gate_recovery_preflight` (line 14979) runs that replay before every mutating command except init, halt, resume, reset and amend runbook (`main`, line 31332). `cmd_status` (line 29820) derives `gate_command_status` as `legacy`, `awaiting-runbook`, `current`, `stale-or-invalid` or `pending-amendment`. `done_push` (line 16131) already resolves and verifies the step's signed push head.

Success-criteria execution re-admits each Exit command with `gate.validate_command(source_root, command)` and no registrations (`plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py:498`). A declared criterion therefore cannot be settled by any locally registered runner today, pinned or not. This run leaves that unchanged and carries it forward (section 3).

The contract text lives in `plugins/hexaemeron/skills/protasis/references/gate-commands.md` and in the `protasis-gate-command-validation` stanza of `plugins/hexaemeron/skills/protasis/SKILL.md`. Tests that assert the current guarantees: `plugins/hexaemeron/tests/test_gate_commands.py`, `test_gate_command_registration.py`, `test_gate_adapter_checkpoint.py`, `test_gate_runner_compatibility.py`, `test_success_criteria.py` and `prove_issue_508.py`; root `tests/test_evolution_contract.py`, `tests/test_promise_machine_contract.py`, `tests/test_success_criteria_scaffold.py`, `tests/promise_machine_coverage.json` (cases M, O, P, R, S for the gate promise) and `tests/promise_machine_id_history.json`. `plugins/hexaemeron/skills/fiat/checkpoint-authority/native-profile.json` pins an older adapter digest (`eacd55c4…`) as a historical profile and is not a current-adapter assertion.

Registered runners in this repository, for comparison: `plugins/hexaemeron/tests/run_tests.py` is a coordinator that starts workers, so under the Elenchus no-descendant boundary it writes no report ([skills#1765](https://github.com/wildcat-finance/skills/issues/1765)). The per-plugin runners are near-copies of one hardened runner, and a fix to one does not reach the others, as [skills#841](https://github.com/wildcat-finance/skills/issues/841) records from PR #764.

### The last two merged pull requests that changed the subject

`git log --first-parent` over `gate_commands.py` and `gate-commands.md` names these two as the most recent merges:

- [PR #1915](https://github.com/wildcat-finance/skills/pull/1915) (merge `9a33c141`, 2026-09-25) added study-mode S010 and re-pinned `protasis.py` in `MODULE_BINDINGS`. Its body has no carried-forward section and names nothing unfinished. Reading its diff shows one consequence it did not state: the adapter digest moved from `ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119` (released 1.6.72 to 1.6.78) to `14a857dc44ce43d7a3771a2125b92f86435e39ab8ba2b027ef02b4f36ca48bad` (1.6.79 to 1.6.82), and neither digest is in `REPLAY_COMPATIBLE_ADAPTERS`. This run changes the adapter again, so it must admit `14a857dc…` after review or every live 1.6.79 to 1.6.82 run refuses `gate-receipt-drift` on upgrade. The older `ac527913…` gap predates this run and is carried forward by name (section 3).
- [PR #1830](https://github.com/wildcat-finance/skills/pull/1830) (merge `2b87b18b`, 2026-09-21) repaired committed study amendment recovery and admitted the 1.6.69 and 1.6.71 adapters for replay. Its only open item is "Related to fiat-checkpoints#1; service delivery remains in progress", which concerns checkpoint delivery, not gate commands; it stays outside this study.

Earlier merges that shaped the subject: [PR #1689](https://github.com/wildcat-finance/skills/pull/1689) for [skills#1356](https://github.com/wildcat-finance/skills/issues/1356) introduced `command-interfaces` rows (the `protasis-v5.13.0` generation this run follows); PR #1754 introduced released-adapter replay; PR #1777 for [skills#1773](https://github.com/wildcat-finance/skills/issues/1773) added the runner timestamp pair; PR #1814 for [skills#1762](https://github.com/wildcat-finance/skills/issues/1762) moved the 64-command bound after effective-field selection.

### Audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check` over the target root exited 0, so the whole-set currency check passed and synopses are the normal reading view. In-scope sources are every `audit/rounds/*.md` (their `.synopsis.md` views), `audit/AUDIT.md` (view `audit/AUDIT_SYNOPSIS.md`) and `plugins/hexaemeron/audit/AUDIT.md` (view `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`). Read mode: every round synopsis and the root synopsis were searched for gate-command terms (`gate_commands`, `gate command`, `command-interfaces`, `registered-source-drift`, `source-unavailable`, `interface-valid`, `MODULE_BINDINGS`, `unregistered-cli`, `REPLAY_COMPATIBLE`, `operation_ran`, `command validat`); only matching rounds were read, and only through their synopses. `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` was read in full. No authoritative source was read directly, and rounds with no match were not read.

- `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`: Step 0 rounds 1 and 2, 15 August 2026. F-01 medium, fixed. Audit schema, Covered, Not checked and Elenchus verdict are `[missing legacy field: ...]` and stay unknown. No gate content.
- `audit/rounds/fiat-508-restudy-residual-carryover-confinement-and-g.synopsis.md`, Step 6 round 1 (2026-09-15): S6-R1-01 low, fixed in `0fada5a5947f39301a4eb28df7821b6922d9bfb6` (plain status omitted the gate result). Elenchus verdict `guarded`. Not checked: the joined lifecycle, due in Step 7. Leads not pursued: `next` can emit an observational worker packet with stale gate source while later admission and mutation stay protected; the round classed this as not an execution bypass. Carried forward as a stated boundary: while a runner is unbound, `next` still emits packets naming its commands, and every mutation still replays first.
- `audit/rounds/fiat-1361-emitter-versus-declaration-check-at-a-pinne.synopsis.md`, Step 1 round 2 (2026-09-23): S1-R2-01 low, accepted and tracked as [skills#1861](https://github.com/wildcat-finance/skills/issues/1861). Elenchus verdict null. Leads not pursued: lead (1) is a cwd split accepted because the "runner not editable here", which is this issue's cost in a second run; lead (4) records that `tests/emit_run_observation_report.py` supplies functions to the digest-registered runner "but sits outside the runbook's `command-interfaces` fence", so a change to the helper would not trip the pin. This design answers lead (1) for a runner its own run creates. Lead (4) stays a stated boundary: a binding pins the runner file only.
- `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.synopsis.md`, Step 1 round 3 (2026-09-19): W1-R3-01 low, fixed that round; Elenchus verdict `unguarded`. It records `gate-receipt-drift` after the controller moved from 1.6.54 to 1.6.58 mid-session, because the whole adapter digest moved, recovered by a runbook amendment. Step 9 round 1 (2026-09-21): W9-R1-01 to W9-R1-07, all fixed; Elenchus verdict `inconclusive`; its lead that a prose correction was blocked at 64 of 64 gate commands pointed at skills#1762, since closed. The drift record is why this run admits the 1.6.79 to 1.6.82 adapter digest for replay.
- `audit/AUDIT_SYNOPSIS.md`: no gate-command match.

None of these names a failure in the code this run changes that must be guarded before product work, so the study declares no known-failure inventory.

### Elsewhere in the organisation

The miskatonic#14 evidence comes from the issue body only; that repository's audit record was not read. Open Skills issues that touch the same surface: [skills#1765](https://github.com/wildcat-finance/skills/issues/1765) and [skills#1909](https://github.com/wildcat-finance/skills/issues/1909) (the Hexaemeron runner under the Elenchus boundary), [skills#1861](https://github.com/wildcat-finance/skills/issues/1861) (runners reporting a missing surface as a failure), [skills#1688](https://github.com/wildcat-finance/skills/issues/1688) (the reference omits accepted constructor keywords), [skills#1575](https://github.com/wildcat-finance/skills/issues/1575) (a pending resolver naming `HEAD`) and [skills#1436](https://github.com/wildcat-finance/skills/issues/1436) (a `step:N` cell is checked when step N-1 pushes). None is answered here; the last two shape this study's resolvers and stop points.

### Outside

Two established ways to pin a dependency: pin in advance, where the digest is written before the bytes are fetched (pip's hash-checking mode, `--require-hashes`), and trust on first use, where the first observed identity is recorded and later ones must match (SSH `known_hosts`). The released route and two candidates pin in advance; `creating-step-binding` is trust on first use, with the first use fixed to a signed, verified commit that the controller already receipts. Git records a regular file as mode `100644` or `100755`, a symbolic link as `120000` and a submodule as `160000`; the binding admits the first two only.

## 3. Constraints and non-goals

Starting ref `e992a54b4e3e4671bae98b448d57690de8dfa044`. `origin/main` stood at `09f2169c` when this study was written, two commits later: an Alexandria change that also moved `.claude-plugin/marketplace.json`, `.horos/boundary.json`, `.horos/census.json` and `tests/test_version_propagation.py`, and nothing under `plugins/hexaemeron`. The last two files are on this run's version surface, so the integration sync will meet them. Python 3.14.6 per `.python-version`; Git 2.50.1 observed on this host. No dependency is added.

Self-hosting limits this run's own runbook. Its Exit and Elenchus commands must name built-in scripts: `scripts/run_checks.py` and `plugins/hexaemeron/tests/run_tests.py` for suites, and the five lint CLIs. `docs/deferred-runner-binding/proof.py` cannot appear in an Exit: it does not exist at `done runbook`, and 1.6.82 requires a registered file to be readable then. That is this issue occurring in the run's own repository. Mason runs each conformance resolver, and Fiat's `step:N` and `integration` design transitions consume the reports. The Hexaemeron runner is the only built-in that writes `unittest-json-v1`, and under the Elenchus boundary it returns `inconclusive` ([skills#1765](https://github.com/wildcat-finance/skills/issues/1765)), so a fix's guard evidence is a hand counterfactual recorded beside the verdict.

Version surfaces:

- Protasis and Fiat each take one generation row. The runbook carries a `version-relations` block with rows for `protasis` and `fiat`, relation `next-generation-after-integration-base`, and must then hold no concrete label token for either skill outside that block. Fiat's generation retains its open frontier tuple; Protasis's retains its mature one.
- Every step PR that changes any byte under `plugins/hexaemeron/` needs a Hexaemeron package version above its own PR base, in `plugins/hexaemeron/.claude-plugin/plugin.json`, `plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `tests/test_version_propagation.py` and `plugins/hexaemeron/tests/test_phylax_model_proxy.py`. Each number must also sit above every number another ref claims; `origin/claude/github-issue-1927-564298` claimed 1.6.83 when this study was written.
- A Fiat generation also moves `fiat/SKILL.md` frontmatter, `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` in `hexctl.py`, the agent-instruction fixture digest and `tests/fixtures/promise-machine/runtime/fiat-final-integration.json`.

Known digest cascades: any `hexctl.py` edit moves `tests/promise_machine_coverage.json`, then `docs/promise-machine/obligation-gates/evaluation-run.json`, then `integration-projection.json` and `.md`, then `.horos/census.json`. A promise-stanza edit moves `tests/promise_machine_id_history.json`. `plugins/hexaemeron/tests/test_hexctl.py` sits 11 bytes under the 262,144-byte Promise Machine read limit, so new controller tests go in new modules. `protasis.py` stays unedited, which keeps its `MODULE_BINDINGS` pin still. Edits to `fiat/SKILL.md` go in "Runbook command evidence", after the governed byte range that ends at 29,736.

Non-goals, each with its reason:

- `node-suite-in-gate-commands | none | the Elenchus no-descendant boundary is deliberate, and a repository's non-Python suite can still run outside the gate, so one occurrence does not justify a separate issue` (the issue's carryover row, kept verbatim).
- A creating step other than Step 1. Protasis fixes Step 1 as the scaffold, and a later creating step would need a rule that every command naming the path sits in that step or later; no evidence asks for it.
- A runner change after Step 1 closes. It keeps the existing append-only amendment with a concrete-digest row. Extending an existing registered runner mid-run (the fiat-1361 lead (1) pattern) is related, but the issue asks only for a missing runner.
- A reviewed runner shipped with Hexaemeron (candidate `reviewed-stdlib-runner`), rejected in section 4.
- Settling a declared success criterion through a local registration. `criteria_execution.py:498` already refuses every local registration; carried forward as `criteria-exit-local-registration`.
- Pinning modules a registered runner imports (fiat-1361 lead (4)); carried forward as `registered-runner-helper-pin`.
- Admitting the 1.6.72 to 1.6.78 adapter digest `ac527913…`; carried forward as `released-adapter-gap-1-6-72`.
- Known-failure inventory reporters, the Elenchus boundary, [skills#1765](https://github.com/wildcat-finance/skills/issues/1765) and [skills#1909](https://github.com/wildcat-finance/skills/issues/1909).

The run's pull request owes a `carryover` block. The four items above are its candidate rows; each needs a disposition at integration.

Boundaries:

- **Always.** Run `python3 scripts/run_checks.py` with the owning scopes before each push, and the full Hexaemeron suite on each step touching `plugins/hexaemeron`. Run Imprimatur and Brevitas on shipped prose, and Phylax, Ephoros and Hypomnema on changed code and docs. Keep refusals before any state, ledger or artefact write.
- **Ask first.** Changing the result schema string or init marker. Adding any adapter digest other than `14a857dc…` to `REPLAY_COMPATIBLE_ADAPTERS`. Widening the deferred row to steps other than 1. Changing the Elenchus runner boundary or the success-criteria admission.
- **Never.** Relax `source-unavailable` or `registered-source-drift` for a pinned row. Read or hash an unbound deferred path during replay. Execute a gate command in the adapter. Rewrite an earlier receipt or ledger event. Edit `test_hexctl.py` past its read ceiling. Claim a command ran when it did not.

## 4. Design options

### Candidates

1. **`creating-step-binding`.** A `command-interfaces` row names the runner path and builder with `step:1` in place of a digest. At runbook capture the path must be absent. Commands naming it are checked for everything except the runner's parser interface. At Step 1's `done push`, Fiat reads the pushed blob, checks it is new since the starting commit and matches the worktree, records its SHA-256 as the binding, and captures a fresh gate result that validates every command against it. After that the row behaves as an ordinary pinned registration. Trade: the parser interface of the runner's commands is checked at Step 1's push instead of at runbook receipt, so a command that does not fit the runner surfaces as a failing Exit inside Step 1 and as a binding refusal at the push.
2. **`reviewed-stdlib-runner`.** Hexaemeron ships one reviewed single-process stdlib unittest runner with its digest and builder in the controller. A row names it by reviewed identity; the gate checks the interface at runbook capture from the shipped bytes; Step 1 must commit a byte-identical copy. Trade: one reviewed implementation and an early interface check, against a runner no target can change inside its own run. A target-specific repair such as S1-R1-01 needs an amendment that switches to a local pinned row, or a Hexaemeron release. It still needs the absent-before and added-by-Step-1 checks of candidate 1, plus a new shipped runner and its contract, and each target still receives a copy, which is the divergence [skills#841](https://github.com/wildcat-finance/skills/issues/841) describes.
3. **`runbook-embedded-source`.** The runbook carries the complete runner source in a new fenced block; the gate checks the interface from those bytes; Step 1 commits exactly the embedded bytes. Trade: an early interface check with the bytes under the runbook's own review, against runner code written during runbook derivation, a runbook that grows by the whole source for every change, and an amendment for every in-step fix.
4. **`pre-placed-untracked`.** The released 1.6.82 route, measured as the baseline. It places the runner in the run worktree before Step 1, which the issue rules out.

A variant of candidate 2 that runs the shipped runner from the plugin root, with no copy in the target, was considered and left out of the matrix. It fails the acceptance clause "a runner that Step 1 adds", and its absolute `execution_argv` would name a per-machine plugin path that checkpoint relocation cannot rebind.

### Closed selection

`.hexaemeron/design-evidence.json` holds four candidates, twelve criteria and 48 cells: 28 resolved selection results and 20 pending conformance results. Its SHA-256 is `2ee92a4119378e5cfd8e7a6455ceebe850cd222f821fd6c75fd98d194c3aba22`. `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition design-lock`, run with the 1.6.82 plugin-cache copy of the checker, exits 0 and selects `creating-step-binding` under `unique-frontier`.

Every selection report came from `python3 .hexaemeron/design/probe.py --candidate <candidate> --criterion <criterion> --report .hexaemeron/reports/<candidate>-<criterion>.json`, run from the repository root, 28 invocations, each exit 0. The probe is a set of Surveyor policy specimens, not the product controller. It loads the released adapter from `git show e992a54b…:plugins/hexaemeron/skills/protasis/scripts/gate_commands.py` and refuses unless its SHA-256 is `14a857dc…`. It builds a disposable Git fixture with `src/`, `tests/test_core.py` and no runner, and wraps each candidate's rule around the released adapter. It walks one lifecycle: runbook capture; Step 1 adds a specimen runner; an audit fix adds `socket.getnameinfo` to the runner's denied events (the S1-R1-01 analogue); Step 1 pushes; Step 2 edits the runner with no amendment. The specimen runner is written as data and never executed. Values are fixture measurements, not production estimates.

| Criterion; concern and form | `creating-step-binding` | `reviewed-stdlib-runner` | `runbook-embedded-source` | `pre-placed-untracked` |
| --- | --- | --- | --- | --- |
| `pre-step-product-files`; correctness gate, at most 0 | 0 | 0 | 0 | 1, fails |
| `bound-drift-refused`; correctness gate, equals true | true | true | true | true |
| `interface-checked-by-step-close`; correctness gate, equals true | true | true | true | true |
| `legacy-results-unchanged`; compatibility gate, equals true | true | true | true | true |
| `replay-milliseconds`; time gate, at most 1,000 | 4 | 4 | 3 | 3 |
| `in-step-fix-amendments`; recovery metric, minimise | 0 | 1 | 1 | 1 |
| `runbook-growth-bytes`; space metric, minimise | 109 | 627 | 4,049 | 653 |

`pre-placed-untracked` fails the one gate the issue's acceptance sets. Of the three survivors, `creating-step-binding` needs no amendment for the in-step fix where the other two need one, and adds 109 runbook bytes against 627 and 4,049, so it dominates both on every comparative metric and is the unique non-dominated candidate. For the status quo the probe also observed the released adapter refusing `source-unavailable: tests/run_tests.py` before the file was placed. `bound-drift-refused` is the released `registered-source-drift` refusal in every candidate, because each reduces to a pinned row once Step 1 closes. `legacy-results-unchanged` shows each model delegating to the released adapter when its own syntax is absent; it is a property of the models, and the successor's version is conformance cell `released-adapter-replay`.

`python3 .hexaemeron/design/probe.py --hostile-cases` prints the binding model's refusals and writes nothing. It observed `deferred-source-present` for an untracked or tracked file at the path during runbook capture, `deferred-path-unsafe` for a symlinked `tests/` directory, `deferred-source-present-at-base` when the starting commit already holds the runner, `deferred-source-absent-at-head` when the push head lacks it, `deferred-worktree-mismatch` for an uncommitted edit at push, and `deferred-source-mode` for a symbolic link committed at the runner path. These are specimens of the intended refusals; conformance cells prove the product's.

### Selected construction

1. **Row grammar.** In `command-interfaces`, the third field accepts the literal `step:1` as an alternative to a 64-hex digest. Path, builder, count, duplicate and built-in override rules are unchanged. Any other step value refuses. A deferred row is admitted in the baseline fence, and in an amendment fence only while Step 1 has no implementation receipt. After that, an amendment fence may repeat an unbound deferred row byte for byte and nothing else; once bound, the path returns only as a concrete-digest row or leaves the set.
2. **Capture before Step 1.** At `done runbook`, and at any amendment receipted before Step 1's implementation receipt, each unbound deferred path must be absent. The adapter walks the path's components with `lstat` from the target root: a missing component means absent; a symbolic link or a non-directory parent refuses `deferred-path-unsafe`; an existing leaf of any type refuses `deferred-source-present`. Fiat passes this requirement explicitly; the adapter cannot infer the phase. `protasis.py --gate-root` applies it too, since it has no binding state and exists for pre-receipt authoring.
3. **Unbound commands.** An invocation naming an unbound deferred path passes every current check except the parser interface: literal `python3`, argv and loop grammar, report substitution through `report_operand`, and placeholder refusal. It records `cli` as `{"path": ..., "deferred": "step:1"}` and result `interface-deferred`. Its source is neither read nor hashed. A runbook with no deferred row yields a result equal to 1.6.82's apart from `adapter_sha256`, with no new member.
4. **Binding at Step 1's push.** `done push` for Step 1, after its existing head and range checks, reads each deferred path as Git objects. The path must be absent at the run's starting commit and a blob of mode `100644` or `100755` at the verified push head, reached through tree entries only, within the adapter's 2 MiB source cap. The worktree file, read through the adapter's no-follow `read_source`, must equal the blob. The bound digest is the blob's SHA-256. Fiat then captures a fresh gate result with that binding; the adapter reads the file, compares the digest, parses the builder and validates every effective command, so the runner's commands become `interface-valid`. Any refusal exits non-zero before a state, ledger or artefact write and names its cause token. Recovery is a fix on the step branch and a new push, or a runbook amendment.
5. **Records.** The Step 1 push receipt and its `done:push` ledger event carry one `gate_binding` object: path, builder, step, starting commit, push head, blob id, SHA-256 and the fresh gate record. `verify_gate_commands` collects gate records in ledger order (runbook, amendments, binding) and replays the latest against current source with the recorded binding. A binding present in state but absent from the ledger, or the reverse, refuses.
6. **After binding.** The row is an ordinary pinned registration: any byte change refuses `registered-source-drift` until an append-only amendment carries a concrete-digest row. The bound file stays covered by every later replay, merge step, sync and integration.
7. **Between runbook and binding.** `verify`, `next`, `status` and the replay before each mutation rerun the capture with no binding. Every other command is checked against current source as today; the deferred path is not read, whether it is absent, present or changing during Step 1; and the recomputed `interface-deferred` records must equal the stored ones. `hexctl status --field gate_command_status` reports `awaiting-binding`, with each deferred path and its step, between runbook receipt and binding, and `current` afterwards. Inspection never binds and never clears a refusal. `next` still emits worker packets while a runner is unbound, which is the fiat-508 lead's accepted boundary.
8. **Replay compatibility.** `REPLAY_COMPATIBLE_ADAPTERS` gains `14a857dc…` with a reference table row, after review shows the successor reproduces every other field of a result whose runbook has no deferred row. Unknown adapters and every other drift still refuse.
9. **Checkpoints and legacy.** Export and restore carry the binding event; a checkpoint taken before binding replays the row as unbound. Runs without the gate marker are untouched. A run initialised under an older controller cannot hold a deferred row, because its runbook passed a validator that refused one and amendments cannot introduce one after Step 1 starts.
10. **Unchanged.** The result schema string `protasis-gate-commands/v1`, the init marker, the built-in registry, `MODULE_BINDINGS`, `protasis.py` and success-criteria admission and execution.

### Pending conformance

Only the selected candidate's cells become due. Each resolver has the form `python3 docs/deferred-runner-binding/proof.py --candidate <candidate> --criterion <criterion> --report .hexaemeron/reports/<candidate>-<criterion>.json`, with literal values in each cell. It runs from the repository root, writes a fresh report and names no moving reference such as `HEAD`. A `step:N` cell is due when step N-1 pushes, so each cell names the step after the one that produces its evidence.

| Criterion | Evidence the resolver must observe | Stop point |
| --- | --- | --- |
| `validator-deferred-contract` (correctness) | The successor adapter accepts a baseline `step:1` row with the path absent and records `interface-deferred` without reading the path; it refuses a present path, a linked parent, a non-`step:1` value, a deferred row added after Step 1 starts, a deferred row after binding, a built-in override and escaping paths; with a binding it yields `interface-valid`; a changed file then refuses `registered-source-drift`. It runs the new adapter test module and reports whether every test passed. | `step:3` |
| `released-adapter-replay` (compatibility) | A receipt captured by the released adapter (read from Git at the starting commit and checked as `14a857dc…`) for a runbook without deferred rows replays under the successor; a changed command or source still refuses. | `step:3` |
| `successor-replay-milliseconds` (time, owner metron) | Median of five successor `validate` calls on `docs/protasis-success-criteria/runbook.md` at the step head, at most 1,000 ms. | `step:3` |
| `controller-binding-custody` (recovery) | The successor controller in a Git fixture reports `awaiting-binding`, binds at Step 1's push and then reports `current`; it refuses a runner present at the starting commit, absent at the head, committed as a link, or different from the worktree; `verify` and checkpoint restore replay the binding; a later edit refuses until a concrete-digest amendment; a legacy run is unchanged. | `step:4` |
| `joined-demonstration` (correctness) | The checked-in controller, identified by its bytes, drives a no-runner fixture through runbook receipt with zero untracked product files, Step 1 creation, an in-step runner fix with zero amendments, binding at push, and a later committed byte change that refuses. | `integration` |

### Proposed runbook units

An outline for derivation; each unit still needs its own Files, Entry, Exit, Tests and Disciplines and a full audit loop.

| Step | Work and homes | Exit commands (built-ins only) |
| --- | --- | --- |
| 1. Scaffold | `docs/deferred-runner-binding/`: study and runbook copies, `design-evidence.json`, selection reports, a byte-identical copy of `probe.py`, and a `proof.py` that refuses every criterion whose product does not exist yet. The draft `docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md`. A root scaffold test. No `plugins/hexaemeron` change, so no package bump. | `python3 scripts/run_checks.py --base fiat/1944-gate-commands-for-a-repository-with-no-runn --scope root --scope docs --format json` |
| 2. Adapter | `gate_commands.py` grammar, capture, deferred validation, bindings and replay; `REPLAY_COMPATIBLE_ADAPTERS`; `gate-commands.md`; the Protasis SKILL command section and `protasis-gate-command-validation` stanza; Protasis ledger row; new `plugins/hexaemeron/tests/test_gate_deferred_registration.py`; `proof.py` handlers for the three `step:3` cells; package bump. | `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-2-exit.json` and the checked runner with `--scope hexaemeron --scope root` |
| 3. Controller | `hexctl.py` binding at `done push`, record chain, `verify`, status value, amendment rules, checkpoint export and restore; the Fiat SKILL "Runbook command evidence" section; Fiat ledger row and version surfaces; new `plugins/hexaemeron/tests/test_gate_deferred_binding.py`; the digest cascade; `proof.py` handler for `controller-binding-custody`; package bump. | as Step 2, with its own report path |
| 4. Demonstration | `proof.py` `joined-demonstration` driving the checked-in `hexctl` through the fixture with the test harness's fake delivery tools; `docs/deferred-runner-binding/demonstration.md`; a demonstration test; package bump if a plugin file changes. | as Step 2, with its own report path |

Every step's Elenchus contract names `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, the only built-in that writes `unittest-json-v1`. A scratch runbook holding the Step 1 and Step 2 Exit commands above and that Elenchus line passed the 1.6.82 adapter's `validate` with five `interface-valid` records; that establishes argument shape only.

The `protasis-gate-command-validation` promise changes meaning, since an effective invocation may now be `interface-deferred` with its creating step, so Step 2 rewrites that stanza and re-pins its semantic digest. `fiat-receipted-delivery` lists "marked-run command evidence" among its evidence; Step 3 names the runner binding there, with the same re-pin.

## 5. Risk register seed

```risk-register
deferred-path-preexists | the target worktree and starting commit at runbook capture and at binding | a file, link or directory already at the deferred path refuses at capture, and a blob at the starting commit refuses at binding
deferred-path-escape | the deferred row's path field | absolute, dot, empty, backslash, .git and non-.py paths still refuse under the unchanged row grammar
deferred-link | parent components and the leaf at capture, binding and replay | a symlinked parent or leaf refuses and a committed 120000 or 160000 entry refuses binding
binding-byte-mismatch | the pushed blob against the worktree file at Step 1's push | the bound digest is the pushed blob's and a differing worktree file refuses before any write
post-binding-edit | a later step's copy of the runner | any byte change after binding refuses registered-source-drift until an amendment carries a concrete-digest row
deferred-row-misuse | amendment fences and step values | a non-step:1 value, a deferred row added after Step 1 starts, and a deferred row after binding each refuse
unbound-authority | gate records before binding | interface-deferred grants no execution or success claim and run-exit still refuses local registrations
binding-custody | push receipt, done:push ledger event, verify and checkpoint restore | state and ledger binding records must agree and replay uses the recorded binding, with forged or missing records refused
partial-binding-write | a push interrupted between state and ledger | the existing state fingerprint and ledger chain refuse a half-written binding and recovery repeats the push
replay-allowlist-widening | REPLAY_COMPATIBLE_ADAPTERS | only 14a857dc is added, and a changed command, source, declaration or report still refuses
legacy-isolation | runs without the marker or captured by an older adapter | legacy results stay byte-identical apart from the adapter digest and no run gains a binding it did not receipt
self-hosting-proof | the acceptance demonstration | the report names the checked-in controller bytes it drove and never the init-pinned 1.6.82 copy
helper-module-outside-pin | modules the bound runner imports | the boundary is stated in the reference, and a binding claims only the runner file
```

The last row is fiat-1361's lead (4), kept as a boundary rather than repaired.

## 6. Glossary seeds

- **Deferred row.** A `command-interfaces` row whose third field is `step:1` instead of a digest.
- **Creating step.** The step whose push binds a deferred row; Step 1 only in this generation.
- **Binding.** The recorded SHA-256 of the runner blob at Step 1's verified push head, with the fresh gate record captured against it.
- **Unbound.** A deferred row with no binding yet; its path is never read or hashed.
- **`interface-deferred`.** The invocation result for a command naming an unbound runner: every check except the parser interface has passed.
- **`awaiting-binding`.** The `gate_command_status` value between runbook receipt and binding.
- **Released adapter.** The Hexaemeron 1.6.79 to 1.6.82 `gate_commands.py`, SHA-256 `14a857dc…`.
- **Successor controller.** The `hexctl.py` and adapter this run checks in, as distinct from the init-pinned 1.6.82 copy that drives the run.

## 7. Sources

- Issue: [skills#1944](https://github.com/wildcat-finance/skills/issues/1944), read 2026-09-27, no comments.
- Adapter: [gate_commands.py at the starting commit](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py); reference [gate-commands.md](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/references/gate-commands.md).
- Controller: [hexctl.py at the starting commit](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/fiat/scripts/hexctl.py) lines 14080 to 15063, 16131, 20977, 29820 and 31332; [criteria_execution.py line 498](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py#L498).
- Design checker: `plugins/hexaemeron/skills/protasis/scripts/design_evidence.py` (D007 frontier, D008 due evidence).
- Pull requests: [#1915](https://github.com/wildcat-finance/skills/pull/1915), [#1830](https://github.com/wildcat-finance/skills/pull/1830), [#1689](https://github.com/wildcat-finance/skills/pull/1689).
- Audit views: `audit/rounds/fiat-508-restudy-residual-carryover-confinement-and-g.synopsis.md`, `audit/rounds/fiat-1361-emitter-versus-declaration-check-at-a-pinne.synopsis.md`, `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.synopsis.md`, `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`, `audit/AUDIT_SYNOPSIS.md`.
- Precedent demonstration: `docs/protasis-success-criteria/demonstration.md`, `docs/protasis-success-criteria/proof.py`, `plugins/hexaemeron/tests/hexctl_harness.py` (fake delivery tools).
- Probe and record: `.hexaemeron/design/probe.py`, `.hexaemeron/design-evidence.json`, `.hexaemeron/reports/`.
- Adapter digests by release: `git show <merge>:plugins/hexaemeron/skills/protasis/scripts/gate_commands.py | shasum -a 256` at `8c147d02` (1.6.70, `3549ce4a…`), `2b87b18b` (1.6.72, `ac527913…`), `9a33c141` (1.6.79, `14a857dc…`) and `e992a54b` (1.6.82, `14a857dc…`).
- Baseline timing: the 1.6.82 `validate` on `docs/protasis-success-criteria/runbook.md` took 488 ms, median of three, on this 18-CPU host on 2026-09-27.

## 8. Signals, and the questions behind them

`hexctl` runs when an operator or delegated agent invokes it; nothing here runs unattended, so there are no metrics or alerts. Three questions someone resuming a run will ask, and the signal that answers each:

1. "Why does the gate say the runner is not bound yet, and which path?" `hexctl status --field gate_command_status` returns `awaiting-binding` with each deferred path and its step. Emitted by Step 3.
2. "Which runner bytes did this run bind, from which commit?" The `gate_binding` object on the Step 1 push receipt and its `done:push` ledger event: path, push head, blob id and SHA-256; `hexctl verify` replays it. Emitted by Step 3.
3. "Why did Step 1's push refuse?" The refusal names one cause token (`deferred-source-present-at-base`, `deferred-source-absent-at-head`, `deferred-source-mode`, `deferred-worktree-mismatch`, or the adapter's own token) and its recovery, exits non-zero and writes nothing. Emitted by Step 3.

[ephoros](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal carries.

## 9. Boundaries, per capability

Phylax owns the boundary list and controls ([phylax](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/phylax/SKILL.md)). This run opens or changes five:

- **Runbook text into the adapter.** Worth taking: an acceptance of a digest-free row. Control: the closed row grammar with one literal alternative, the unchanged 32-row cap, and placement rules tied to Step 1's implementation receipt.
- **Target worktree at capture.** Worth taking: acceptance while a file already sits at the path. Control: the `lstat` component walk that refuses links, non-directory parents and any existing leaf.
- **Git objects at binding.** Worth taking: a bound digest for bytes Step 1 did not add or did not push. Control: full-SHA starting commit and verified push head, tree-entry reads only, the mode allowlist, the 2 MiB cap, and Fiat's existing bounded Git helpers with their closed environment.
- **Worktree file at binding and replay.** Worth taking: a link or a file swapped during the read. Control: the adapter's existing no-follow, bounded, identity-checked `read_source`.
- **Replay allowlist.** Worth taking: acceptance of changed evidence under an old adapter identity. Control: one reviewed digest, a regression test that every other field must still match, and ask-first for any other digest.

Nothing new executes: the adapter stays inert with `operation_ran:false`, the runner runs only under Mason's and Elenchus's existing boundaries, and `run-exit` is unchanged. No network, secret or dependency is involved. These feed rows in section 5.

## 10. The budget, or its absence

Replay runs before every mutating `hexctl` command, so its cost matters. Baseline: the released adapter validated `docs/protasis-success-criteria/runbook.md` in 488 ms, median of three, on this host. Budget: the successor adapter does the same in at most 1,000 ms, median of five, at Step 2's head, measured by `python3 docs/deferred-runner-binding/proof.py --candidate creating-step-binding --criterion successor-replay-milliseconds --report .hexaemeron/reports/creating-step-binding-successor-replay-milliseconds.json` (cell `successor-replay-milliseconds`, due at `step:3`). The selection specimens replayed the fixture runbook in 3 to 4 ms. The binding adds two Git object reads and one validation, once per run, so it carries no budget of its own. [metron](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/metron/SKILL.md) owns how the budget is checked.

## 11. The fail-closed posture

What stops the run: any adapter refusal at `done runbook`, at an amendment, or in the replay that precedes each mutating command; any binding refusal at Step 1's `done push`; `gate-receipt-drift` against an unadmitted adapter; and D008 when a due conformance report is missing or fails at `step:N` or `integration`. Each exits non-zero before a state, ledger or artefact write, as the current controller does. Refusal reasons are fixed tokens, never free text from the target.

Guard convention: each fix lands with a test that fails on the fix's parent and passes on the fix, in `plugins/hexaemeron/tests/test_gate_deferred_registration.py` (adapter) or `plugins/hexaemeron/tests/test_gate_deferred_binding.py` (controller), never in `test_hexctl.py`. The Elenchus contract names the Hexaemeron runner, whose verdict is expected to be `inconclusive` under the runner boundary; record the verdict as returned and the hand counterfactual beside it, and never relabel it. [elenchus](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.

## 12. Decisions and their homes

Expensive to reverse, because receipts and runbooks will depend on them:

1. The deferred row grammar (`step:1` in the digest field), binding at the creating step's push from the verified head's blob, and the additive `interface-deferred` result inside `protasis-gate-commands/v1` rather than a new schema or init marker. Home: the numberless draft `docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md`, written in Step 1 and numbered at integration, bound by the bridge below.
2. Admitting `14a857dc…` for replay. Home: the released-adapter table in `plugins/hexaemeron/skills/protasis/references/gate-commands.md` and the Protasis ledger row, as the 1.6.69 and 1.6.71 admissions were recorded; no separate decision record.
3. The `awaiting-binding` status value. Home: `gate-commands.md` and the Fiat SKILL "Runbook command evidence" section.
4. The Protasis and Fiat generations. Home: `plugins/hexaemeron/skills/protasis/EVOLUTION.md` and `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, resolved by the runbook's version relations.

[hypomnema](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where each lives.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | creating-step-binding
record | docs/decisions/drafts/bind-a-step-created-runner-at-its-push.md
```
