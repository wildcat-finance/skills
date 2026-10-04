# Runbook command validation

The command validator checks declared arguments against registered source interfaces without executing the runbook commands or importing their target modules. Its result records interface validity, not test execution, command success or an audit verdict. Fiat owns the receipt that consumes this result.

Run the optional check from the target repository, using its supported Python:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py runbook.md --gate-root . --format json
```

With `--gate-root`, one bounded no-follow document capture supplies both the runbook shape check and the command check. A refused interface adds `P008` to the normal findings output and makes the command exit nonzero. Combining `--study` with `--gate-root` refuses. Without `--gate-root`, Protasis retains its existing shape check. The CLI does not write a gate receipt. Fiat captures the result when it receipts a marked runbook or amendment.

## Registered interfaces

The registry names exact repository paths and parser-builder functions. It covers the checked runner, the Hexaemeron test runner, Brevitas, Protasis, Imprimatur, Phylax, Ephoros and Hypomnema. An unregistered executable or script refuses; the validator does not import a target to discover an interface.

Each invocation must start with literal `python3` followed by a registered script path. Literal arguments pass to a local parser reconstructed from the script's argument declarations. The validator accepts a finite per-file loop in this form:

```sh
for file in first.md second.md; do python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file"; done
```

The loop has a literal item list and exactly one whole, double-quoted `"$file"` operand. Each item produces a separate invocation. There is no general shell evaluator: substitutions, other variables, pipes, redirects, command chaining, glob expansion, backticks and unsupported loops refuse. A four-file invocation of Brevitas does not become valid because four one-file invocations would be valid. Command text containing `#` or `~` also refuses, including quoted occurrences; the grammar does not interpret comments or expand a home directory.

The parser reads Python syntax as AST data. Each registration pins the module AST with only the designated builder's body omitted. The actual builder body must then supply a supported literal `ArgumentParser` construction and a direct prefix of `add_argument` declarations. Its terminal statement must return the parser or assign a direct `parse_args` call with no arguments or its declared `argv` parameter. Other terminal arguments, keyword arguments and dynamic statements refuse. Supported actions are `store`, `append`, `store_true` and `store_false`; other actions and dynamic declaration builders refuse. Before `add_argument`, `nargs` must be absent, `None`, `?`, `*`, `+`, or an exact integer from 0 through 128; booleans refuse. `argparse` still decides whether that bounded arity is valid for the declared action. Private test-worker flags do not enter the public interface.

A registered module whose AST digest differs from the current pin is admitted
under the caller's `starting_bindings`, described below, only when that
module's entry carries the AST digest the adapter computed and the digest of
the exact bytes it read. The comparison is the pair `prior_runner_bindings`
already uses. A missing entry, a mismatch in either digest, or a bindings value
outside its closed shape refuses `unregistered-cli-module-bindings`, as today.
The adapter derives nothing: the caller reads the starting commit and supplies
the pair, and the adapter reads no Git.

Built-in integer and floating-point conversion use the local built-in operations. The registered `positive_int` and `positive_jobs` converters use fixed local scalar behavior only after their reviewed AST digests match; `positive_jobs` also binds its range constant. A custom converter is not imported or executed. Extending the registry requires a reviewed source path, parser-builder shape and tests for supported and refused arguments. A changed converter body or range requires a new reviewed binding.

## Source and report evidence

A target repository may add reviewed local interfaces through one
`command-interfaces` fence before Step 1. Its first line is exactly
`schema | protasis-command-interfaces/v1`. Each following line has three fields:
`<relative Python path> | <parser-builder name> | <complete source SHA-256>`.
There are at most 32 entries. Paths use portable ASCII components and end in
`.py`; absolute paths, empty or dot components, `.git`, duplicates and built-in
registry overrides refuse. Every declared source is checked, including one
that no current command invokes.

The runbook review owns acceptance of each complete source, including its
module bindings and behavior outside the parser declaration. A digest is a
source identity, not evidence of that review or of safe execution. The adapter
checks the declared digest before parsing the same captured bytes. The builder
must use the local name `parser` and the same closed declaration prefix as the
built-in interfaces. Local `str` and `pathlib.Path` conversion are also admitted;
they use the validator's scalar operations and do not access the filesystem.
Unsupported converters still refuse. The adapter never imports the source.

A dated runbook amendment may contain one replacement registration fence. The
latest complete set governs all effective commands. A schema-only fence
retires the set; it does not make an unregistered command valid. Earlier
declarations stay in the preserved document and receipt prefixes. A second
fence in one region or a baseline fence after Step 1 refuses. Protasis's
runbook check and Fiat still own amendment shape, chronology and receipt
acceptance. Changing a source requires a reviewed registration update through
that append-only process.

The closed result schema is `protasis-gate-commands/v1`. It binds the complete captured runbook digest, captured `source_root` and full adapter digest. Each command retains its source text, UTF-8 byte offset and digest. Each expanded invocation records the original `argv`, the substituted `execution_argv`, the CLI path, full CLI digest, declaration digest and `interface-valid` result. An invocation that names an unbound runner created by Step 1 records `interface-deferred` instead, as the next section describes.

The source-owned Elenchus declaration supplies the exact command, report format and report file. Its format is `unittest-json-v1`; the normalized Elenchus verdict and raw producer report remain separate artifacts. Exactly one whole `{report}` argument binds to the declared report path. Unbound or partial substitutions, unsupported formats and escaping report paths refuse. Constructing `execution_argv` does not run it or create its report.

The latest complete replacement of a step's Exit or Tests field supplies its effective commands. Superseded commands retain their raw source, offset, digest and `superseded-source` status; their obsolete interfaces are not relabelled as currently valid. Commands outside those fields remain active. This selects effective source within the captured document without changing any earlier runbook bytes.

The result retains `operation_ran:false`. That field states that the declared command did not execute; source parsing and interface checking cannot supply a test result. Replay still checks the complete CLI bytes when the visible argument declarations have not changed. New captures bind the full current adapter digest.

After a checkpoint relocation, the receipt keeps its original `source_root` and absolute `execution_argv`. Replay checks that this historical operand still derives from the captured root and unchanged relative report declaration. It independently validates the report destination under the current root, including its path refusals. The stored operand grants no authority to execute at the historical root, and replay does not rewrite the receipt or relax full source matching. Fiat's checkpoint identity and ledger checks own relocation.

## Runner created by Step 1

A target with no runner of its own can register one that Step 1 will add. The
row puts the literal `step:1` where the digest goes:
`<relative Python path> | <parser-builder name> | step:1`. Any other step
value refuses `deferred-step-unsupported`. Path, builder, count, duplicate and
built-in override rules are unchanged.

A deferred row is admitted in the baseline fence, and in an amendment fence
while Step 1 has no implementation receipt. After that receipt, an amendment
fence may repeat an unbound deferred row byte for byte and add no other
deferred row (`deferred-row-after-step-start`). Once the path is bound it
returns only as a digest row or leaves the set; a deferred row for it refuses
`deferred-row-after-binding`. An amendment may still retire the path or pin it
by digest.

Until a binding names the path, the adapter never reads or hashes it. When the
caller requires absence, the capture walks the path's components with `lstat`
from the target root. A missing component means the path is absent. A linked or
non-directory parent, or one that changes between `lstat` and open, refuses
`deferred-path-unsafe`. An existing leaf of any type, a link included, refuses
`deferred-source-present`.

An invocation naming an unbound path must still pass every other check:
literal `python3`, argv and loop grammar, report substitution and placeholder
refusal. It records `cli` as `{"path": <path>, "deferred": "step:1"}` and the
result `interface-deferred`, with no new result member. Its arguments are not
parsed until a binding exists. The capture that supplies the binding refuses a
command that does not fit the runner. `interface-deferred` grants no execution
or success claim. Success-criteria execution still refuses every local
registration.

A binding maps a deferred path to the SHA-256 of the runner recorded when
Step 1 pushed. The adapter does not record bindings; its caller supplies them.
With a binding, the row is an ordinary pinned registration. The adapter reads
the source through the no-follow reader, compares its digest, parses its
builder and validates every effective command to `interface-valid`. A later
byte change refuses `registered-source-drift` until an amendment carries a
digest row. A binding pins the runner file only. Modules the runner imports
stay outside that pin, so a change to one does not refuse.

The adapter cannot infer the run's phase, so `validate` and `replay` take it as
keyword arguments:

- `require_absent`: each unbound deferred path must be absent. Capture only;
  replay never checks absence.
- `regions_before_implementation`: how many leading runbook regions (the
  baseline, then each dated amendment in order) were receipted before Step 1's
  implementation receipt. `None` while Step 1 has none.
- `bindings`: each bound path and its recorded SHA-256.
- `regions_before_binding`: how many leading regions were receipted before the
  binding. Required exactly when `bindings` is non-empty.
- `starting_bindings`: what the caller derived from the run's starting commit.
  `None` admits nothing. The closed shape is one object with exactly
  `adapter_sha256`, that commit's adapter digest, and `modules`, a table with
  at most one entry per registered module path. Each entry holds exactly
  `ast_sha256`, the module digest the adapter at that commit pinned, and
  `source_sha256`, the digest of the module's complete source. Every digest is
  64 lowercase hexadecimal characters. A value outside this shape, a table
  larger than the registry included, admits nothing and names no new cause.
  The same keyword reaches `validate_with_criteria`, `validate_command`,
  `interface` and `parser_bindings`, and it leaves the result shape unchanged.

The adapter starts a region at each exact `### Amendment -- YYYY-MM-DD` heading
outside a fence. Protasis and Fiat also accept other whitespace between `###`
and `Amendment`, which would give the caller a region the adapter did not
count. A runbook with a deferred row therefore refuses such a heading as
`invalid-registration-amendment`. Without a deferred row it reads as before.

A binding must name exactly the deferred rows effective when it was recorded
(`deferred-binding-unknown`, `deferred-binding-incomplete`). A malformed
binding refuses `deferred-binding-invalid`, and an inconsistent phase record
refuses `deferred-phase-invalid`. So does a region count beyond the document
when the runbook holds a deferred row. The counts govern deferred rows only: in
a runbook without one the adapter ignores them, as it ignores an uncounted
heading. The defaults describe pre-receipt authoring: absence required, no
binding, and deferred rows admitted in any region. `protasis.py --gate-root`
uses them. A runbook with no deferred row yields the result the Hexaemeron
1.6.82 adapter gives, apart from `adapter_sha256`.

## Fiat receipt and legacy boundaries

Newly initialized runs record `contracts.gate_commands` with `protasis-gate-commands/v1` in both state and the immutable init event. A runbook or amendment receipt then carries the exact gate evidence in state and its ledger event. A changed marker or disagreement between stored and ledger evidence refuses verification.

From runbook receipt until Step 1's push binds the row, Fiat reports `gate_command_status` as `awaiting-binding`, with each deferred path and its step. After the binding it reports `current`. Every adapter call Fiat makes carries the region counts its receipts record.

Legacy runs without that marker retain their earlier contract. They do not receive fabricated validation records, and inserting gate evidence into an unmarked run refuses. This distinction preserves historical receipt bytes without describing them as newly checked interfaces.

Historical gate records retain the exact command text, offset and digest from each captured runbook prefix. Current-interface replay validates the latest effective result against the current CLI and adapter source. A stale CLI source outside the reviewed timestamp pair below, or a changed command/report binding, cannot reuse its prior result. Unknown adapter digests also refuse. These changes require freshly validated evidence through the owning runbook amendment process while keeping prior records intact.

Replay also accepts seven reviewed, released adapter digests when every other
field agrees with current validation, subject to the relocation rules above:

| Release | Source | Adapter SHA-256 |
| --- | --- | --- |
| 1.6.54 | [gate_commands.py](https://github.com/wildcat-finance/skills/blob/41116f4f9901b7b70a22db9f42235af65951957e/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py) | `18eb52e7e6bc741bd2c80c55838de74831777ea0833147570963c10e0904c093` |
| 1.6.58 | [gate_commands.py](https://github.com/wildcat-finance/skills/blob/04968a0bc5b3636687136661257897ea10e622cf/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py) | `c2d14b0f262ecde17f679a73a462cd2ed0f4305a54528e93e375f2b36514bbc6` |
| 1.6.59 | [gate_commands.py](https://github.com/wildcat-finance/skills/blob/75e3a0c76faa0dfeb31f84aeff133b37ec3ad0d9/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py) | `00d4c9f2a0905ea65d56a3ddca9a429c9a20d464d9b66f69098a954b5e7c37b0` |
| 1.6.69 | [gate_commands.py](https://github.com/wildcat-finance/skills/blob/a06cd696cbfade69eeb42a49e91d876550ccdb36/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py) | `d7e49768547fe0c4673c8204d3392c57e60824448fac5bfe8a5bdf4ab5c1bef4` |
| 1.6.71 | [gate_commands.py](https://github.com/wildcat-finance/skills/blob/3b49d3825716a6eb349afe1901ab5096f664a9a5/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py) | `3549ce4afff9cdbd3f8ba04beece3eb17d5cb4f51d954f71dd1d50733c237b0c` |
| 1.6.79 to 1.6.82 | [gate_commands.py](https://github.com/wildcat-finance/skills/blob/e992a54b4e3e4671bae98b448d57690de8dfa044/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py) | `14a857dc44ce43d7a3771a2125b92f86435e39ab8ba2b027ef02b4f36ca48bad` |
| 1.6.84 | [gate_commands.py](https://github.com/wildcat-finance/skills/blob/6f4312c3ba706c1df88f535967d2d59e184c1f79/plugins/hexaemeron/skills/protasis/scripts/gate_commands.py) | `6f50cd844a3543aa7ef05fc6631c72ba2fd91aab44ad3f06d62bb4f7312682de` |

The first two sources differ only in the module pin for the Hexaemeron test runner.
The third adds their reviewed replay rule.
`REPLAY_COMPATIBLE_ADAPTERS` records this closed compatibility decision for
released adapters. Beside it, replay substitutes one more digest: the
`adapter_sha256` in the caller's `starting_bindings`, which the caller derived
from the run's starting commit. Neither route admits an unknown adapter or
relaxes CLI, command, argument, declaration, report or runbook matching.
Replay uses the current validator, executes no old adapter, and leaves the
historical receipt unchanged. A run whose commands still match can therefore
retain its post-push checkpoint boundary without an amendment. Adding another
digest to the reviewed list requires review of that released source and
regression evidence; equality of visible arguments alone does not suffice.
This compatibility rule governs the gate receipt only. Success-criteria
admission and execution retain their separate checks.

Hexaemeron 1.6.69 and 1.6.71 are also reviewed for replay. Their adapter sources
differ only in moving the command-count check after effective-field selection.
Every previously accepted command result must still match byte for byte; newly
accepted documents require a fresh capture. Fiat's read-only criteria replay
separately checks the declaration and complete join against the retained gate,
and this compatibility result does not authorize a command execution.

Hexaemeron 1.6.79 to 1.6.82 and 1.6.84 are reviewed for replay as well. Their
sources differ only in the `ephoros.py` module pin, and neither accepts a
deferred row. The regression test reads each from Git at the commit that
shipped it, captures a runbook with no deferred row and no Ephoros command, and
requires the current adapter to reproduce every field except the adapter
digest. The maintainer approved the 1.6.84 digest on 2026-09-27. The 1.6.72 to
1.6.78 adapter
(`ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119`) is not
in the reviewed list. It is admitted for a run whose starting commit carries
it, through the `starting_bindings` that run's caller derives, and for no
other run.

Inspect the current boundary with plain `hexctl status` or `hexctl status --field gate_command_status`. The separate field reports `legacy`, `awaiting-runbook`, `current`, `stale-or-invalid` or `pending-amendment`; a pending amendment reports `validation:not-complete`. It is a derived observation, not a new state field or a full-status JSON mutation. Inspection does not clear a refusal or complete an interrupted amendment. The adapter result carries no provenance member: when a replay admitted caller-derived starting-commit bindings, the caller that derived them owns that record.

## Reviewed runner timestamp transition

A second, narrower rule addresses the completed #1676 run. Its five runner
commands remain identical after the published descriptor timestamp repair,
but the full runner source digest changed. The repair checks descriptor
support and stamps the completed report through its held descriptor. It does
not change parser declarations.

`RUNNER_TIMESTAMP_PAIR` admits only this exact pair:

- Captured adapter: `eacd55c44ff05a8a8899143066795bdb1a02fd869c9f4ec12cca55a20252b279`.
- CLI path: `plugins/hexaemeron/tests/run_tests.py`.
- Captured CLI: `ac11ed0c2a403e509badf8f78a7583062965691c4ea28d9518148d7a50c54e4b`.
- Current CLI: `c8e63d2c2f0d595172d6be22f387da66a8b4bbb0b0d3f8404f772519b504deb8`.

Every command must have at least one invocation, and every invocation must use
that runner and current digest. The complete comparison substitutes only the
captured adapter and runner digests. Every other field, including declarations,
arguments, report derivation, raw command bytes and runbook digest, must match.
Mixed commands, empty or superseded command records and unknown source pairs
refuse. Even a comment-only source change falls outside this pair.

## Reviewed runner manifest cap transition

Issue #2014 added signer-email tests. Before those tests, discovery used
393,182 of its 393,216-byte manifest cap. Five new test IDs brought it to
393,727 bytes. The current eight tests bring the manifest to 394,322 bytes
under the new 395,264-byte cap. Its parser and report format are unchanged.

`RUNNER_MANIFEST_CAP_PAIR` records the exact `run_tests.py` transition from
`c8e63d2c2f0d595172d6be22f387da66a8b4bbb0b0d3f8404f772519b504deb8`
to `0af4aa499ff841eb9ab3086af2a48d655f1558b94857f29ae1d2852cd9b6bd53`.
The prior adapter `550ac4def7d019213a345d1ddf348d3ff263118dc90a425ec091c4fcd47007cf`
remains replay compatible when the entire command result matches.
The successor accepts the old runner's module binding only when its complete
source digest matches the recorded pre-cap runner.
An earlier receipt with the same adapter replays only when every invocation
uses that runner and prior digest, with all other fields identical. The
timestamp pair above remains recorded and can replay through this second
reviewed source change under the same full-record comparison. Unknown runner
changes still refuse.

Fresh captures retain the current source digests. Replay leaves historical
receipts unchanged and executes no captured command or old adapter. This rule
establishes interface compatibility for one reviewed source transition; it does
not turn earlier execution evidence into a test of the new runner. The
regression reconstructs the old runner by removing only the timestamp repair
and checks both complete source digests. See
[skills#1773](https://github.com/wildcat-finance/skills/issues/1773).

## Reviewed single-process runner transition

The runner now accepts an optional `--single-process` argument and uses the
same path when its first worker cannot start. Existing argument forms retain
their meanings. The current runner source digest is
`3eb4de8552253e384a1c4f5d6e4a8736d954a21b6b46df99f1732a37a40c8204`;
its CLI declaration digest is
`8a590400e12a8cee800d2c0ef41dfbbd9d291e669ce6a414c8462bad2f63b805`.

`RUNNER_SINGLE_PROCESS_TRANSITION` admits a receipt captured with runner source
`ac11ed0c2a403e509badf8f78a7583062965691c4ea28d9518148d7a50c54e4b`
or `c8e63d2c2f0d595172d6be22f387da66a8b4bbb0b0d3f8404f772519b504deb8`
and CLI declaration digest
`5e7831594e54926d37f999e03b923d02ede258a6d3d9b5420718ff6533eded66`.
It applies only to the reviewed released adapters and the adapter immediately
preceding this change. Replay substitutes the adapter, runner source and
declaration digests, then compares every other receipt field exactly. A
historical invocation containing `--single-process` refuses. The older
timestamp pair keeps its narrower requirement that every invocation use the
runner. A historical receipt remains evidence of its own command result;
replay does not execute that command or establish a result for the new mode.
See [skills#1765](https://github.com/wildcat-finance/skills/issues/1765).

## Bounds and refusals

The current parser limits a captured document to 256 KiB and each CLI source to 2 MiB. It admits at most 64 effective command records, 64 loop items, 256 expanded invocations, 128 argv operands per invocation and 8 KiB per operand. Superseded Exit and Tests records remain in the captured history without consuming the effective-command allowance. A command string is limited to 64 KiB. These are parser bounds, not execution resource limits.

CLI source reads require bounded regular files through no-follow path components. The absence check for an unbound deferred path opens parent directories only and never opens the leaf. Unavailable files, an observed identity change, unsupported parser syntax, malformed or unclosed command fences, unknown placeholders and argument errors refuse. Source observations do not establish atomic namespace protection or a security verdict about the command's behavior.

A valid interface result authorizes only its use as the named gate evidence. The separate test runner, Elenchus, Warden and Fiat delivery gates still own their execution, failure, audit and receipt claims.
