# Lazarus runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Lazarus.** Lazarus captures the finite fixed-block Ethereum state and RPC evidence an application test needs, verifies the proof-backed part and replays only exact recorded requests. Use Alexandria for a lending-data archive, Tabularium for event interpretation and Ariadne to bind a released fixture to its evidence. **Current frontier:** Receipts and logs are recorded RPC evidence only; nothing proves them against the captured header's receiptsRoot.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Lazarus contains one Agent Skill. Select `lazarus` to capture, verify, replay or
release a finite historical Ethereum fixture, then read
`skills/lazarus/SKILL.md` in full.

`skills/lazarus/SKILL.md` is the only canonical instruction document. Do not
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
- `$PLUGIN_ROOT` means this `plugins/lazarus/` directory.
- The command path is `$PLUGIN_ROOT/scripts/lazarus.py`. The current build
  implements format validation, finite capture, manifest construction, offline
  verification, exact loopback replay, and writing and reading back a
  preservation release.
- A plan-v2 capture maps each declared anchor source at runtime with repeated
  `--anchor-rpc-env SOURCE_ID=ENV_VAR` arguments. The argument names an
  environment variable; its RPC URL value does not enter argv.
- Names such as `lazarus:lazarus`, `/lazarus:lazarus` and `$lazarus` are
  logical aliases. Load the canonical path from the table above.

## Network and side effects

`capture` is the only networked command. It uses the explicit primary RPC URL
and, for plan v2, the exact declared source-to-environment mapping. Every
anchor client shares the primary capture's request, response-byte,
component-byte, total-byte and elapsed-time limits. Capture queries each source
for the mainnet chain ID and fixed block, scans staged bytes against the union
of all provider secrets, verifies the complete fixture and atomically finalises
it. Provider URL values and raw provider errors are discarded. Format
validation, manifest construction and fixture verification reach no network.
`build-manifest` writes only
`manifest.json` beneath its explicit fixture root. `verify` checks schemas,
safe paths, canonical manifest bytes, component sizes and SHA-256 digests,
then verifies the header, EIP-1186 account and storage proofs, proved response
fields and captured code. `replay` verifies before binding loopback.
It has no provider, proxy or fallback. `release` verifies its fixture, holds the
statement it is handed to what that verification recomputed, and writes its
output whole or not at all, into a directory that must not exist and must not
sit inside the fixture. `verify-release` reads a release back and writes
nothing. Neither reaches a network, and neither signs anything.

## What this skill must refuse

- No moving block in an effective plan. `latest` and `pending` are resolved or
  rejected before the stored plan is written.
- No proof claim for an ordinary RPC result. Logs, receipts, calls and traces
  remain recorded evidence.
- No silent live fallback. An uncaptured replay request is a visible miss.
- No secret persistence. Provider URLs, headers, credentials and raw provider
  errors do not enter a fixture or its diagnostics.
- No unsafe fixture path. Absolute paths, parent traversal and symlinks are
  rejected.
- No canonical-chain claim from a self-consistent header alone. The expected
  block hash needs an external provenance record.
- No provider independence claim from distinct operator-chosen source IDs or
  matching anchor records.
- No partial anchor capture. Missing, extra or duplicate mappings, unavailable
  environment values, provider failure, identity disagreement, exhausted
  limits, secret detection or failed final verification leaves no fixture.
- No proof claim for an account, storage slot or code blob unless the current
  `verify` command checked it against the captured header state root.
- No release over a statement whose counts the fixture does not verify to, in
  either direction, and no release built on counts read from a manifest rather
  than recomputed from the records.
- No release described as checked unless `verify-release` ran over the bytes on
  disk and exited 0.

If capture, verification, replay or a test did not run, say so plainly and do
not describe its result as successful.
