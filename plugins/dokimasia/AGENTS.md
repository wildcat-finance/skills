# Dokimasia runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Dokimasia.** Dokimasia defines the boundary for compiling a frontend's routes, actions and access guards into a coverage denominator and reconciling a reviewed UAT workbook against it, so every scoped item carries exactly one disposition. Every declared verb is built. Use Horos to decide what an agent does not read, Hexaemeron Fizz to fuzz a contract, and Synkrisis to compare agent runs. None of them compiles a frontend inventory or holds an oracle. **Current frontier:** Dokimasia admits a confirmed entry only when it names the person who confirmed it and, where a rule was applied, a row in the set's `rules` table stating that rule and who stated it, and its coverage and scrutiny records report confirmations by person and by rule. The pinned scrutiny of `wildcat-app-v2` at `bb9685fb` still closes at 202 over 261 with `covered` at zero, now attributed to one person under one stated rule. Every one of those entries was drafted from the workbook; none records anything observed in the running application.
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

It executes nothing. It reads a pinned checkout and never runs the application,
drives no browser, holds no signing key and reaches no chain, so no disposition
it drafts records anything observed in the running application: every drafted
entry comes from the workbook or the compiled inventory, and only a person's
confirmation, under that person's name and any rule they applied, admits it to
a closure ratio. It does not verify that a named person agreed; the name is a
claim the disposition set makes. It never drafts `covered`, and it cannot
confirm an entry on its own. The harness that executes a release belongs to the
application repository.
