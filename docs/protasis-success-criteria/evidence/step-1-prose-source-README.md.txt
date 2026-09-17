# Declared success criteria: Step 1 evidence

This package publishes the accepted #1273 study, runbook, design selection and
decision. `proof.py` checks their design-home join and replays the selection
specimens. The declaration, execution, completion and joined-controller
operations remain unavailable until their owning steps land.

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
observations. Both destinations must be absent. Reads and writes refuse linked
paths below the chosen root; input files are capped at 1 MiB and the input set
at 8 MiB. The check observes source stability around execution and before
publication; it does not lock the repository against concurrent writers.

Existing output is preserved. An interrupted two-file publication can leave a
companion without its report; inspect that evidence and choose a fresh report
name for a deliberate retry. The companion records local observations and is
not a signed attestation or a controller receipt.

## What remains unavailable

| Operation | Owning implementation step |
| --- | --- |
| `declaration-contract` | 2 |
| `execution-custody` | 3 |
| `terminal-compatibility` | 4 |
| `joined-demonstration` | 5 |

Each returns `operation-not-implemented:<criterion>:step-<number>` and exit 1
without producing a report. The two losing candidates also receive no
conformance report. `design-home` establishes only the published join and
selection replay. Step 1 makes no feature-completion claim.

## Preserved sources

[study.md](study.md), [runbook.md](runbook.md) and
[design-evidence.json](design-evidence.json) retain their accepted bytes.
The runbook names the opening accepted study; [opening-study.md](evidence/opening-study.md)
is that exact prefix of the current study, before its accepted operating-boundaries
amendment. Historical `.hexaemeron/evidence/` references map to the same filenames
under [evidence](evidence/). The provenance inventory records the copied paths
and digests; it includes the issue and PR sources, bounded audit-reading evidence,
selection executions and the prose checks needed to interpret the accepted text.

[selection_probe.py](selection_probe.py) and the eighteen selection reports are
unchanged Surveyor evidence. Replay uses a disposable copy and leaves those
reports intact. The measured one-versus-three launch count and 345-byte sample
record describe synthetic policy specimens. They establish neither production
latency nor production storage cost, custody security, criterion sufficiency or
semantic correctness. Production conformance requires the later proof operations
and a separate execution of the successor controller.

Run the owning cases with `python3 -m unittest tests.test_success_criteria_scaffold -v`.
The checked repository runner includes that module through the root suite.
