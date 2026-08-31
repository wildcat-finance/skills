# Homologia runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Homologia.** Homologia compares one pinned on-chain computation with one pinned off-chain mirror over declared vectors. `check` now admits the closed pair and evidence-classed expected answers into deterministic, cap-bounded checked inputs; mirror execution and every verdict still refuse. Use Hexaemeron Fizz to generate vectors or fuzz one implementation, Pandects for economic laws, Lazarus for proved chain-side answers, and Synkrisis to compare agent runs rather than implementations. **Current frontier:** `check` admits one closed, cap-bounded manifest and its declared vectors into a deterministic checked-inputs record. It executes no mirror and produces no verdict, so nothing yet establishes that a pair agrees.
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
do not report a comparison: only checked-input admission has shipped. Mirror
execution, comparison, rendering and verification must refuse.

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

It executes no mirror, compares no vector, and produces no verdict. It also
executes no EVM: the chain side arrives as evidence rather than as a call.
Vector generation and minimisation, economic laws, and performance claims
remain outside its charter.
