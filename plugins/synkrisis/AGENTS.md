# Synkrisis runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Synkrisis.** Synkrisis compares validated Promise Machine run observations across one operator-declared cohort and recomputes bounded, evidence-linked findings. Use Ephoros to design what a step emits, Metron for controlled measurement verdicts, Elenchus to work one failure to its cause, and Horos for the reading boundary a finding may point at. **Current frontier:** Synkrisis is a committed specification with a refusing command stub, and none of its runbook's cohort, diagnosis, render or verification steps has yet landed behaviour.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Synkrisis contains one Agent Skill. Select `synkrisis` to read the committed
cross-run comparison specification, to run the scaffold's declared surface,
or to continue the runbook's held steps, then read
`skills/synkrisis/SKILL.md` in full. At this step every operation refuses
with a stable code naming the runbook step that implements it; do not
present a cohort, finding, report or verification as a Synkrisis result.

`skills/synkrisis/SKILL.md` is the only canonical instruction document. Do not
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

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, output files, and exit codes when using an equivalent
local tool. A non-zero exit from a check means the check failed; do not report
a run as clean when it exited 1.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`, unless
  that file defines it differently.
- `$PLUGIN_ROOT` means this `plugins/synkrisis/` directory.
- The command is `scripts/synkrisis.py`, resolved against `$PLUGIN_ROOT` and
  not the user's target repository. The interpreter is the exact pin in the
  suite's `.python-version`.
- Names such as `synkrisis:synkrisis` and `/synkrisis:synkrisis` are logical
  aliases. Load the canonical path from the selection above.

## Network and side effects

Nothing here reaches the network. The Step 1 command parses its arguments,
prints one refusal naming the runbook step that implements the operation, and
exits 1; it reads no record, writes no file, executes no observed content and
has no GitHub, Git or controller mutation path. Treat a target repository as
the user's, and obey its own instructions before writing anything into it.

## What this skill must refuse

These are properties of the tool rather than reminders, and a local agent must
not route around them:

- No analytical result from the scaffold. Every operation refuses until its
  runbook step lands; a refusal is not a cohort, finding, report or
  verification.
- No inferred comparability. The operator declares the comparison policy;
  Synkrisis checks that declaration and never decides that unlike tasks,
  models, hosts, repositories or tokenizers are comparable.
- No evidence strengthening. Findings are specified to stay at the inferred
  class and carry their counterevidence, unknown runs and nearest forbidden
  claim.
- No cause and no model judgement, in a rule, a finding or a report.
- No autonomous transition. A suggested handoff is the whole action; filing
  issues, editing repositories and dispatching siblings belong to a person.

If an operation, a check or a suite did not run, say so plainly and do not
describe its result.
