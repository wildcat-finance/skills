# Janus runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Janus.** Janus tests a contract hook at the threshold it controls: what it can observe and change before a host action, what changes are allowed after, and what it must never touch. Use Hexaemeron Fizz to generate a protocol-specific fuzz harness, Pandects for the economic laws a hook-driven transition must preserve, and Ariadne to carry a manifest revision and its conformance result with a release. **Current frontier:** Janus ships the Wildcat v2.5 host adapter and its seven gates against modeled hooks, and no second host adapter yet shows the manifest format holds for another callback model.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Janus contains one Agent Skill. Select `janus` to state and enforce what a hook
may observe and change around a host action, or to add a host adapter and its
manifest, then read `skills/janus/SKILL.md` in full.

`skills/janus/SKILL.md` is the only canonical instruction document. Do not add a
sibling browsing README.

## Translate tool names by capability

The canonical skill was written for hosts that name their tools. A local agent
must map those names to equivalent capabilities:

| Instruction term | Required capability | Preserve |
| --- | --- | --- |
| `Read` | Read the named file completely or at the stated range | Named range and byte content |
| `Write` or `Edit` | Create or patch the named file | Intended path and patch scope |
| `Bash` | Execute the command in a shell and inspect its exit status | Argument order and exit status |
| `Glob`, `Grep`, or `find` | Enumerate or search files with the stated pattern | Pattern and matched paths |

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, output files, and exit codes when using an equivalent
local tool. A non-zero exit from a check means the check failed; do not report a
run as clean when it exited 1.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`, unless that
  file defines it differently.
- `$PLUGIN_ROOT` means this `plugins/janus/` directory.
- The harness is the Foundry project under `harness/`; `forge` runs there. The
  validator and reporter are `scripts/janus.py`, resolved against `$PLUGIN_ROOT`
  and not the user's target repository.
- Names such as `janus:janus` and `/janus:janus` are logical aliases. Load the
  canonical path from the table above.

## Network and side effects

Nothing here reaches the network, and the Solidity has no dependency to fetch.
`forge` compiles and runs the harness locally against modeled host code;
`janus.py` reads a manifest or a findings file and prints. The harness reads
manifests and writes findings only under the plugin's own directories, through a
declared `fs_permissions` set, and uses no `vm.ffi`.

Running a host adapter's suite compiles and executes that host's modeled code
in a local EVM. Treat a target repository as the user's, and obey its own
instructions before writing anything into it.

## What this skill must refuse

These are properties of the tool rather than reminders, and a local agent must
not route around them:

- No conformance verdict on an incompletely recorded delta. An effect the
  state-delta recorder cannot classify is a violation, not an ignored unknown.
- No gate weakened to let a hostile hook pass, and no hostile reference hook
  committed that its owning gate does not catch.
- No exit liveness reported as a proof. A bounded run holds a property over the
  sequences it drove; it does not prove that an exit always completes.
- No claim that a hook is safe. The suite says a hook stayed inside a declared
  boundary under a described search, for one host adapter.
- No cross-host claim. Passing one adapter's suite says nothing about another
  host's callback model.

If a build, a test, a validation, or a report did not run, say so plainly and
do not describe its result.
