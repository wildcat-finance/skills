# Dokimasia runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Dokimasia.** Dokimasia defines the boundary for compiling a frontend's routes, actions and access guards into a coverage denominator and reconciling a reviewed UAT workbook against it, so every scoped item carries exactly one disposition. Every declared verb is built. Use Horos to decide what an agent does not read, Hexaemeron Fizz to fuzz a contract, and Synkrisis to compare agent runs. None of them compiles a frontend inventory or holds an oracle. **Current frontier:** Dokimasia compiles a pinned checkout, imports a reviewed workbook, reconciles both into dispositions, and has run one scrutiny of `wildcat-app-v2` at `bb9685fb`: 261 scoped items, none carrying a disposition. No code path helps a reviewer write one, and 261 entries by hand is the whole cost of using this.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Dokimasia contains one Agent Skill. Select `dokimasia` to inspect or implement
the declared coverage boundary. Read `skills/dokimasia/SKILL.md` in full.
Every declared verb is built. Report a closure ratio only for an inventory and
workbook pair whose digests the disposition set names. A closure ratio states
that nothing is unaccounted for, never that anything passed, and no item may be
reported as covered without a reviewed oracle a person named.

`skills/dokimasia/SKILL.md` is the only canonical instruction document. Do not
add a sibling browsing README.

## Translate tool names by capability

The canonical skill was written for hosts that name their tools. A local agent
must map those names to equivalent capabilities:

| Instruction term | Required capability | Preserve |
| --- | --- | --- |
| `Read` | Read the named file completely or at the stated range | Named range and byte content |
| `Bash` | Run the exact command with its arguments | Argument order and exit status |
| `Write` | Create or replace the named file | Exact path and bytes |

A host that cannot preserve the right-hand column cannot run the skill.

## What this plugin does not yet do

It compiles no inventory, imports no workbook, records no disposition and emits
no coverage record. In the completed design it will also execute nothing: it
reads a pinned checkout and never runs the application, drives no browser,
holds no signing key and reaches no chain. The harness that executes a release
belongs to the application repository.
