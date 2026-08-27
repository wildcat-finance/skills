# Berean runtime contract

<!-- marketplace-context:start -->
> **Marketplace context: Berean.** Berean pins the corpus, chain readings and evaluation record a protocol agent's answers rest on, so a release can be checked without the model that produced it. Use Lemma to produce source-linked chunks, Lazarus to preserve the chain evidence itself, and Ariadne to bind a released artefact digest to its evidence. **Current frontier:** The reference release answers against a frozen demonstration corpus and preserved Goldfinch mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
<!-- marketplace-context:end -->

## Promise Machine binding

Before selecting or running a skill, read the local
[Promise Machine contract](PROMISE_MACHINE.md). This `promise-machine/v1`
file is a generated installation copy of the suite law. A result authorises
only the transition its canonical skill declares; missing, stale or
insufficient evidence blocks that dependent transition while leaving recovery
available.

Berean contains one Agent Skill. Select `berean` to build, verify or evaluate
an evidence-backed protocol-agent release, then read
`skills/berean/SKILL.md` in full.

`skills/berean/SKILL.md` is the only canonical instruction document. Do not
add a sibling browsing README.

## Translate tool names by capability

The canonical skill may name host tools. A local agent must map them to
equivalent capabilities:

| Instruction term | Required capability | Preserve |
| --- | --- | --- |
| `Read` | Read the named file completely or at the stated range | Named range and byte content |
| `Write` or `Edit` | Create or patch the named file | Intended path and patch scope |
| `Bash` | Execute the command in a shell and inspect its exit status | Argument order and exit status |
| `Glob`, `Grep`, or `find` | Enumerate or search files with the stated pattern | Pattern and matched paths |
| `AskUserQuestion` | Ask the stated question through structured UI or concise text | Literal question and answer |

Tool names describe capabilities, not mandatory API identifiers. Preserve the
arguments, ordering, output files and exit codes when using an equivalent
local tool. A non-zero exit means the requested operation did not succeed.

## Resolve placeholders

- `$SKILL_DIR` means the directory containing the active `SKILL.md`, unless
  that file defines it differently.
- `$PLUGIN_ROOT` means this `plugins/berean/` directory.
- The tool's own commands are relative to `$PLUGIN_ROOT`, so
  `scripts/berean.py` resolves here and not in the user's target repository.
- Names such as `berean:berean` and `/berean:berean` are logical aliases.
  Load the canonical path from the table above.

## Network and side effects

The plugin reaches no network. `build-corpus` reads the named tree and writes
only the named manifest. `verify-corpus`, `check-citation`, `check-answer`,
`verify-release`, `export-cases` and `promotion-chain` read local files and
write nothing beyond the output path they were given. `run-evals` writes only
its report. `promote` and `rollback` append one record to the release's
promotion file and change nothing else. Every builder stages its output and
lands it with one rename.

## What this skill must refuse

- No path escape. Absolute paths, parent traversal and symlinks are refused
  everywhere a document names a file.
- No verification by declared digest alone. Citations are re-sliced from
  pinned bytes, request keys are recomputed, and digests are recompared.
- No evidence upgrade. Source classes and read evidence classes are closed
  vocabularies and never widen at read time.
- No blockless live value. A current value that names no chain and no block
  is not accepted as evidence.
- No silent time-domain choice. A document claim and a later chain state that
  disagree are both reported.
- No grading against an unpinned corpus. A digest mismatch stops the
  evaluation before the first case.
- No model execution and no retrieval. Berean checks recorded answers; it
  does not produce them.

If a build, verification, evaluation or test did not run, say so plainly and
do not describe it as successful.
