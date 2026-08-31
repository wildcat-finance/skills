# Alexandria runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Alexandria contains one Agent Skill. Select `alexandria` to build or verify a
digest-bound lending-data release or inspect the archive contract, then read
`skills/alexandria/SKILL.md` in full.

`skills/alexandria/SKILL.md` is the only canonical instruction document. Do
not add a sibling browsing README.

## Translate tool names by capability

| Instruction term | Required capability | Preserve |
| --- | --- | --- |
| `Read` | Read the named file completely or at the stated range | Named range and byte content |
| `Write` or `Edit` | Create or patch the named file | Intended path and patch scope |
| `Bash` | Execute the command in a shell and inspect its exit status | Argument order and exit status |
| `Glob`, `Grep`, or `find` | Enumerate or search files with the stated pattern | Pattern and matched paths |
| `AskUserQuestion` | Ask the stated question through structured UI or concise text | Literal question and answer |

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, output files and exit codes when using an equivalent
local tool.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`.
- `$PLUGIN_ROOT` means this `plugins/alexandria/` directory.
- The command is `$PLUGIN_ROOT/scripts/alexandria.py`.
- Names such as `alexandria:alexandria` and `/alexandria:alexandria` are
  invocation aliases, not shell commands.

## Network and side effects

- `ingest --plan <path> --output <directory>` reads the plan and the confined
  local source paths it declares. It builds a sibling temporary directory and
  atomically installs the requested release directory. It reaches no network,
  does not change the source files and refuses to replace a different release.
- `verify <release-directory>` reads the canonical manifest and its confined
  digest-keyed objects. For a derived release it also reads and rebuilds the
  two declared JSONL files. It refuses undeclared release entries, reaches no
  network and does not change the release.
- `statement <release-directory> --output <file>` completes that same offline
  verification before projecting the release and every component into a
  canonical unsigned in-toto Statement v1. It refuses an output inside or
  aliased into the release, writes through a fresh no-follow sibling temporary
  file and atomically replaces only an absent or regular output. It reaches no
  network and does not change the release. A result authorises only use of
  those statement bytes; signing and publisher identity remain downstream.
- `derive <raw-release> --output <directory>` first verifies and reads the raw
  release, then writes a new release through a temporary sibling directory.
  It does not change the input or reach the network. It reads components
  without keeping an aggregate cache and stops above 100,000 rows or 64 MiB
  for either JSONL file.
- `index <derived-release>... --output <database>` verifies each release,
  rebuilds a disposable SQLite database through a temporary sibling file and
  replaces the named database. It refuses an output path inside any input
  release, does not change a release and reaches no network.
- `query --index <database> --address <address>` opens the database read-only,
  checks its exact schema and logical digest, re-verifies every referenced
  release and compares the indexed rows with those releases one at a time. It
  prints canonical JSON, changes no file and reaches no network.
- `examples/credit-history-v0/demo.py build --output <directory>` reads only
  the two digest-pinned repository sources, builds the complete offline path in
  a new directory and removes a partial output after failure. `verify` changes
  no demo file and reaches no network. Its short-lived Probitas handoff files
  live in an operating-system temporary directory, not in the demo tree.
- `scripts/compound_v3_phase0.py registry` reads one local Comet checkout at
  the fixed commit and writes the canonical 28-market registry. `build` and
  `check` consume local files only; `check` is read-only.
- `scripts/usdc_interval.py collect` is the interval collector's one network
  path. It reads the HTTPS endpoint from `ALEXANDRIA_COMPOUND_RPC_URL`, never
  records the endpoint, headers or credentials, follows no redirect, bounds
  every response and the whole run, writes a checkpoint only after fsync, and
  leaves a receipt for every refusal. `reconcile` opens the same boundary
  against a second provider. `build` and `check` reach no network: `build`
  writes one release through the existing `ingest`, and `check` changes no file.
- `examples/usdc-interval-v0/demo.py build --output <directory>` runs the whole
  collector path against checked-in synthetic fixtures, removes a partial
  output after failure and opens no socket. `verify` changes no file.
- `scripts/compound_v3_phase0.py capture` is the one explicit network path. It
  reads the HTTPS endpoint from `ALEXANDRIA_COMPOUND_RPC_URL`, writes the fixed
  bounded corpus through a sibling temporary directory and never records the
  endpoint, headers or credentials.

## What this skill must refuse

- No claim that Alexandria archived, verified, indexed or queried data unless
  that exact operation ran successfully.
- No publisher-authenticity claim from a digest check alone.
- No claim that an Alexandria statement is signed, that Ariadne registered its
  predicate, or that Ariadne checked the predicate-owned gates.
- No claim that provider-reported or recorded data proves a canonical chain
  boundary.
- No rewriting raw objects to fit a common schema.
- No universal repayment, default or current-balance conclusion from an event
  without separately sourced position evidence.
- No address-to-person inference, personal data or counterparty score.

If an operation, source check or test did not run, say so plainly.
