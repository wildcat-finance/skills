# Declared success criteria: Step 1 evidence

This package publishes the accepted #1273 study, runbook, design selection and
decision. `proof.py` checks their design-home join, replays the selection
specimens, checks the bounded declaration and effective-Exit join, and records
real bounded child-process outcomes for execution custody. Completion, replay
compatibility and the joined controller demonstration remain pending their
owning steps.

## Run the design-home check

From the repository root, using the interpreter in `.python-version`:

```bash
python3 docs/protasis-success-criteria/proof.py --candidate controller-capture --criterion design-home --report .hexaemeron/reports/controller-capture-design-home.json
```

The check runs Hypomnema's explicit study/design bridge, Protasis's design-lock
selection evaluation and the three policy specimens. It compares all eighteen
observed values and units with the digest-bound selection reports. The standing
decision is `adr/settle-study-criteria-from-recorded-execution`; its stable
selector survives the later number assignment while its decision text stays
fixed.

A successful check creates the seven-field `protasis-design-report/v1` file and
an adjacent `.evidence.json` file. The companion binds the report digest, input
and checker digests, interpreter, resolved decision home and actual specimen
observations. Both destinations must be absent. Reads and writes refuse symbolic
link components below the chosen root; input files are capped at 1 MiB and the input set
at 8 MiB. The check observes source stability around execution and before
publication; it does not lock the repository against concurrent writers.

Existing output is preserved. An interrupted two-file publication can leave a
companion without its report; inspect that evidence and choose a fresh report
name for a deliberate retry. The companion records local observations and is
not a signed attestation or a controller receipt.

## Declaration contract

The Step 2 resolver checks the single `success-criteria` fence in the accepted
study, rejects malformed or ambiguous rows, and binds every descriptor to one
effective registered Exit command. It does not execute a command or claim that
the command's result settles its claim:

```bash
python3 docs/protasis-success-criteria/proof.py --candidate controller-capture --criterion declaration-contract --report .hexaemeron/reports/controller-capture-declaration-contract.json
```

The report has the same source-bound companion format as the design-home check;
the companion records the declaration, runbook, adapter and interpreter
digests, plus named refusal observations. Both output files must be absent
before a run.

## Execution custody

Step 3 proves that the selected executor records an observed result rather than
accepting caller-supplied success:

```bash
python3 docs/protasis-success-criteria/proof.py --candidate controller-capture --criterion execution-custody --report .hexaemeron/reports/controller-capture-execution-custody.json
```

The proof launches real disposable children for zero exit, non-zero exit and
incremental output overflow. It binds the executor and target controller
digests, preserves bounded stdout and stderr observations, and writes a
create-only report with its companion evidence. This establishes bounded
execution custody for the recorded command; it does not establish semantic
criterion correctness, host isolation or a later-tree guarantee.

## What remains unavailable

- `terminal-compatibility`: implementation Step 4.
- `joined-demonstration`: implementation Step 5.

Each returns `operation-not-implemented:<criterion>:step-<number>` and exit 1
without producing a report. The two losing candidates also receive no
conformance report. `design-home` establishes only the published join and
selection replay. `execution-custody` records bounded child-process outcomes;
it does not make the later completion or demonstration claims. Step 3 makes no
semantic-correctness claim.

## Preserved sources

[study.md](study.md), [runbook.md](runbook.md) and
[design-evidence.json](design-evidence.json) retain their accepted bytes.
The runbook names the opening accepted study; [opening-study.md](evidence/opening-study.md)
is that exact prefix of the current study, before its accepted operating-boundaries
amendment. The [provenance inventory](evidence/provenance.json) maps historical
`.hexaemeron/evidence/` sources to their copied paths and digests under
[evidence](evidence/). Archived prose and code copies use `.txt` suffixes where
listed, including `step-1-prose-source-README.md.txt`. The inventory includes issue
and PR sources, bounded audit-reading evidence,
selection executions and the prose checks needed to interpret the accepted text.
The prepared decision remains in [prepared-decision-draft.md](evidence/prepared-decision-draft.md);
[decision-publication.json](evidence/decision-publication.json) records its single
status-line repair to the required dated form.

[selection_probe.py](selection_probe.py) and the eighteen selection reports are
unchanged Surveyor evidence. Replay uses a disposable copy and leaves those
reports intact. The measured one-versus-three launch count and 345-byte sample
record describe synthetic policy specimens. They establish neither production
latency nor production storage cost, custody security, criterion sufficiency or
semantic correctness. Production conformance requires the later proof operations
and a separate execution of the successor controller.

## Fixture repair evidence

The accepted runbook amendment covers two archive-test fixture repairs. The
archive specification check reads its tracked study and reference. The cleanup
check gives its child process a test-owned temporary parent and still detects an
owned leak. A controlled foreign-directory reproduction failed before the repair
and passed afterwards.

The [history inventory](evidence/history/step-1-before-fixture-repair/history.json)
preserves the earlier unconsumed design-home report, companion and changed inputs,
the failed Hex result, the earlier root pass and isolated reproductions. Those
results describe their recorded sources. The current design-home companion binds
the amended runbook and current proof.

The [evaluation projection](evidence/evaluation-projection/applied.json) refreshes
the source-tree digest after the fixture repair. Its producer verified the same
eleven prompts, raw answers, model, date and fifty-five outcomes. This is not a
new model observation. The original evaluation record and both prompt manifests
remain beside the projection record.

The [later history](evidence/history/step-1-before-evaluation-projection/history.json)
preserves the next unconsumed design-home output and its inputs before the
evaluation-projection amendment. The scaffold fixtures resolve the actual
decision home, so they remain usable after its number is assigned.

The [restricted-environment history](evidence/history/step-1-before-closed-environment-repair/history.json)
preserves the signed candidate's ordinary green checks, refused controller
admission and diagnostic failures. The affected fixtures now select the declared
Python and real signing tools explicitly. Their temporary launchers restore the
incoming environment; an empty search path exposes only the selected launchers.
The two ordinary-Git control observations enable replacement objects only within
their own scope. Native verification and refusal checks retain their controls.

The [current evaluation projection](evidence/evaluation-projection/closed-environment-applied.json)
refreshes the source binding after these repairs and preserves the same prompts,
answers, model, date and outcomes. Each earlier projection remains in evidence.

The fixture checks run real signatures and offline demonstrations. They do not
replace the full suites or the controller's separate implementation receipt.

## Adopted controller and audit repair

The admitted study permits one published external-controller replacement.
[PR #1698](https://github.com/wildcat-finance/skills/pull/1698) supplies signed
commit `c572009b7922b4b7b9400893c5adc6d4df641a72`. The
[adoption record](evidence/controller-adoption/adoption-record.json) binds its
source, signature, publication and adapter readbacks. The original source stays
unchanged; this Step 1 repair leaves the target controller unchanged too.

The [pre-adoption history](evidence/history/step-1-before-controller-adoption/history.json)
preserves the reports, inputs and implementation admission from
`d230b3ac07158bd5786a5c58539e6999ed3dda54`. The current design-home companion
binds the admitted study and runbook amendments. The path-escape fixture now
owns its temporary parent, still refuses the symlink and preserves an occupied
sibling. Its isolated collision failed twice before this repair and passed
afterwards.

The [evaluation recheck](evidence/controller-adoption/evaluation-unchanged.json)
reproduced the current record byte for byte with the owning producer: eleven
prompts and fifty-five outcomes remain unchanged. No source projection changed
and no new model observation occurred.

Run the owning cases with `python3 -m unittest tests.test_success_criteria_scaffold -v`.
The checked repository runner includes that module through the root suite.
