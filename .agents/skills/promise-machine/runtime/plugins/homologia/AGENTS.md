# Homologia runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Homologia.** Homologia defines the future boundary for comparing one pinned on-chain computation with one pinned off-chain mirror over declared vectors. The current scaffold is selectable so contributors can build that boundary, but every substantive operation refuses. Use Hexaemeron Fizz to generate vectors or fuzz one implementation, Pandects for economic laws, Lazarus for proved chain-side answers, and Synkrisis to compare agent runs rather than implementations. **Current frontier:** Homologia ships its contracts, packaging and a help-only command. No manifest is checked, no mirror is executed and no verdict is produced, so nothing yet establishes that a pair agrees.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Homologia contains one Agent Skill. Select `homologia` to inspect or implement
the declared comparison boundary. Read `skills/homologia/SKILL.md` in full and
do not report a comparison: the current command surface is help-only and every
substantive verb must refuse.

`skills/homologia/SKILL.md` is the only canonical instruction document. Do not
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

It validates no manifest, executes no mirror, compares no vector, and produces
no verdict. In the completed design it will also execute no EVM: the chain side
will arrive as evidence rather than as a call. Vector generation and
minimisation, economic laws, and performance claims remain outside its charter.
