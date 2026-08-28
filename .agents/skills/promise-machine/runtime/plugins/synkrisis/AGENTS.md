# Synkrisis runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Synkrisis.** Synkrisis owns bounded comparison across validated Promise Machine run observations. This release builds the checked cohort, classifying every declared run under an operator-declared policy, infers bounded findings over it from a digest-bound rule catalogue, renders the fixed-template report, and verifies that all three artefacts recompute from their original inputs. Ephoros designs what a step emits, Metron owns controlled measurement verdicts, Elenchus works one failure to its cause, and Horos owns the reading boundary a finding may point at. **Current frontier:** Synkrisis builds one checked cohort, infers bounded findings from a digest-bound rule catalogue, renders the fixed-template report and verifies the whole path, and its measured work budget and demonstration path have not yet landed.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Synkrisis contains one Agent Skill. Select `synkrisis` to build one checked
cohort from declared run-observation records, to infer bounded findings over
one cohort from a digest-bound rule catalogue, to render or verify those
artefacts, or to read the committed cross-run comparison specification, then
read `skills/synkrisis/SKILL.md` in full. The measured work budget is Step 5
and has not landed, so do not present a runtime or memory claim as a
Synkrisis result.

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

Nothing here reaches the network. Every operation reads the declared
manifest, policy, record, cohort, catalogue, findings and report files from
repository-relative paths beneath the working root through single bounded
descriptors, and writes only the named output file, atomically, refusing to
overwrite different bytes and leaving no partial output behind a refusal.
Verification writes nothing at all. Nothing
executes observed content, follows a symlink, or holds a GitHub, Git or
controller mutation path. Treat a target repository as the user's, and obey
its own instructions before writing anything into it.

## What this skill must refuse

These are properties of the tool rather than reminders, and a local agent must
not route around them:

- No measured work claim. The benchmark and its declared ceilings are Step 5
  of the runbook and have not landed.
- No inferred comparability. The operator declares the comparison policy;
  Synkrisis checks that declaration and never decides that unlike tasks,
  models, hosts, repositories or tokenizers are comparable. An unknown run
  stays visible and satisfies no sample.
- No evidence strengthening. A finding stays at the inferred class and
  carries its counterevidence, unknown runs and nearest forbidden claim.
- No cause and no model judgement, in a rule, a finding or a report.
- No autonomous transition. A suggested handoff is the whole action; filing
  issues, editing repositories and dispatching siblings belong to a person.

If an operation, a check or a suite did not run, say so plainly and do not
describe its result.
