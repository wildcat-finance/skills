# Tabularium runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Tabularium contains one Agent Skill. Select `tabularium` to build or verify a
preserved, sourced ledger of on-chain credit events, then read
`skills/tabularium/SKILL.md` in full.

`skills/tabularium/SKILL.md` is the only canonical instruction document. Do not
add a sibling browsing README.

## Translate tool names by capability

The canonical skill may name host tools. A local agent must map them to
equivalent capabilities:

| Instruction term | Required capability | Preserve |
| --- | --- | --- |
| `Read` | Read the named file completely or at the stated range | Named range and byte content |
| `Write` or `Edit` | Create or patch the named file | Intended path and patch scope |
| `Bash` | Execute the command in a shell and inspect its exit status | Argument order and exit status |
| `Glob`, `Grep`, or `find` | Enumerate or search files with the stated pattern | Pattern and matched paths |
| `AskUserQuestion` | Ask the stated question through structured UI or concise text | Literal question and answer |

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, output files and exit codes when using an equivalent
local tool. A non-zero exit means the requested operation did not succeed.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`, unless
  that file defines it differently.
- `$PLUGIN_ROOT` means this `plugins/tabularium/` directory.
- The tool's own commands are relative to `$PLUGIN_ROOT`, so
  `scripts/tabularium.py` resolves here and not in the user's target
  repository.
- Names such as `tabularium:tabularium` and `/tabularium:tabularium` are
  logical aliases. Load the canonical path from the table above.

## Network and side effects

The plugin reaches no network. `build` reads the source and capture manifest
named by its flags, then writes canonical JSONL and a coverage manifest only
to the named output paths. Every artefact must sit inside the coverage
manifest's directory. `verify` reads those local files, rebuilds expected event
bytes and writes nothing.

`compound-witness` first verifies the named sibling Alexandria release, then
writes non-canonical facts and a witness manifest to the named paths.
`verify-compound-witness` reads the release and those two outputs, rebuilds the
facts and writes nothing. Neither command changes the Alexandria release.

## What this skill must refuse

- No path escape. Absolute paths, parent traversal, symlinks and release
  artefacts outside the manifest directory are refused.
- No verification by declared digest alone. `verify` rebuilds canonical bytes
  from the bound source and checks one-to-one source selectors.
- No publisher-authenticity claim. The release is unsigned; offline
  verification proves internal consistency, not publisher identity or
  authenticity.
- No rewriting raw evidence. Each mapping retains the source record beside its
  interpretation rather than replacing it.
- No semantic flattening. Venue-qualified meanings must not be promoted to a
  universal claim about repayment, delinquency or default.
- No identity inference or score. The ledger records sourced events; it does
  not identify people or rate a counterparty.
- No chain-proof claim. The captured block is what the hosted indexer reported;
  neither it nor each event is independently proved against Ethereum here.

If a build, verification, source check or test did not run, say so plainly and
do not describe it as successful.
