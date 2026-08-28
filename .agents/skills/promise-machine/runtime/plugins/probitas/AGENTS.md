# Probitas runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Probitas.** Probitas builds a sourced record of what a counterparty did across lending venues from addresses they declared, without identifying a person or issuing a Wildcat verdict. Use Alexandria for archived lending inputs and Tabularium when the job is publishing a reusable credit-event release rather than assessing one counterparty. **Current frontier:** Morpho Midnight fixed-maturity coverage now ships API-scoped on Base; secondary-market borrow exits stay refused as unattributable and Morpho curation remains uncollected.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Probitas contains one Agent Skill. Select `probitas` to build a sourced dossier
on what a counterparty did across on-chain lending venues, then read
`skills/probitas/SKILL.md` in full.

`skills/probitas/SKILL.md` is the only canonical instruction document. Do not
add a sibling browsing README.

## Translate tool names by capability

The canonical skill was written for hosts that name their tools. A local agent
must map those names to equivalent capabilities:

| Instruction term | Required capability | Preserve |
| --- | --- | --- |
| `Read` | Read the named file completely or at the stated range | Named range and byte content |
| `Write` or `Edit` | Create or patch the named file | Intended path and patch scope |
| `Bash` | Execute the command in a shell and inspect its exit status | Argument order and exit status |
| `Glob`, `Grep`, or `find` | Enumerate or search files with the stated pattern | Pattern and matched paths |
| `AskUserQuestion` | Ask the stated question through structured UI or concise text | Literal question and answer |

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, output files and exit codes when using an equivalent local
tool. `verify` exiting non-zero means the dossier does not ship; do not report a
run as clean when it exited 1.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`, unless
  that file defines it differently.
- `$PLUGIN_ROOT` means this `plugins/probitas/` directory.
- The tool's own commands are relative to `$PLUGIN_ROOT`, so
  `scripts/probitas.py` resolves there and not in the user's target repository.
- Names such as `probitas:probitas` and `/probitas:probitas` are logical
  aliases. Load the canonical path from the table above.

## Network and side effects

Without `--fixtures` or `--alexandria-index`, `collect` makes outbound requests
to public venue APIs.
It sends the addresses it was given and nothing else, and it needs no
credential for either shipped venue. Ask for whatever approval the runtime or
the target repository requires before running it against a live counterparty,
and prefer a fixture directory when demonstrating rather than investigating.

`--alexandria-index` reads a disposable Alexandria SQLite index and its
referenced verified releases without reaching the network. It keeps the
original venue and archive provenance on every record and reports every
unharvested registry venue as a gap.

`collect`, `render` and `verify` write only where `--out` points. Nothing else
in the plugin writes outside its own directory.

## What this skill must refuse

These are properties of the tool rather than reminders, and a local agent must
not route around them:

- No personal data. The evidence schema rejects a value key that names a
  person, so an adapter cannot record one. Do not add a field to carry one, and
  do not answer a question about which individual controls an address.
- No unsourced assertion. A record cannot exist without a transaction hash, a
  URL or a document reference. If a figure has no record behind it, drop the
  claim rather than softening it.
- No score without a rubric printed beside it. This version emits none.
- No silent gap. A venue nobody checked gets a row saying so. Never present an
  unchecked venue as a clean one, and never delete a coverage row to tidy a
  document.

If a lint, a test, a network call or a gate did not run, say so plainly and do
not describe its result.
