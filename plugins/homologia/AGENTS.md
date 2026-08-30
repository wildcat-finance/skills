# Homologia runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Homologia.** Homologia compares one pinned on-chain computation with one pinned off-chain mirror over declared vectors, and preserves every divergence as a specimen. Use Hexaemeron Fizz to generate the vectors and to fuzz one implementation on its own, Pandects for the economic laws a transition must preserve, Lazarus to capture and prove the chain-side answers, and Synkrisis to compare agent runs rather than implementations. **Current frontier:** Homologia ships its contracts, packaging and a help-only command. No manifest is checked, no mirror is executed and no verdict is produced, so nothing yet establishes that a pair agrees.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Homologia contains one Agent Skill. Select `homologia` when an off-chain
reimplementation of a contract's arithmetic has to be held against what the
contract answers, then read `skills/homologia/SKILL.md` in full.

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

## What this plugin will not do

It executes no EVM, so the chain side of any comparison arrives as evidence
rather than as a call. It does not generate, mutate or minimise vectors. It
judges no economic law and makes no performance claim. It never reports
agreement as correctness.
