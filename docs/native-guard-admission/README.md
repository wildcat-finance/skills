# Native guard admission scaffold

Step 1 publishes the accepted `typed-applicability` design, synthetic examples
and the original selection evidence. Applicability parsing, controller
admission and native execution remain pending. This scaffold supplies no
parent-red guard, service result or host-isolation claim.

## Read the contract

[contract.md](contract.md) describes the closed declaration and its four
routes. [fixtures/applicability.json](fixtures/applicability.json) demonstrates
all four dispositions with byte spans over an authored synthetic source.
These examples have not passed the future applicability parser. A local
regression keeps the existing guard route; an integration requirement waits
for its referenced controller-observed criterion. Historical and excluded
rows grant no current success. Null source status means unknown.

The accepted [study](study.md), [runbook](runbook.md) and
[design record](design-evidence.json) retain their original bytes, dates,
version assumptions, paths and pending results. Their `.hexaemeron/` paths
name the original run. The cross-skill decision is
`adr/route-audit-obligations-to-their-evidence`.

## Inspect the proof interface

From the repository root, run:

```bash
python3 docs/native-guard-admission/proof.py --candidate typed-applicability --criterion native-execution --report .hexaemeron/reports/native-proof.json
```

The command exits 2 with a bounded JSON refusal naming the unavailable
operation and its implementing step. It creates no report. All six
conformance operations currently refuse. Report operands must name JSON
files below the current directory's `.hexaemeron/reports/`; existing leaves,
linked ancestors, traversal and outside paths refuse. No supplied report
is read or replaced. The command launches no child or declared resolver.

## Reproduce the selection evidence

The fifteen files in `reports/design/` are exact accepted selection reports.
The original `research/design_probe.py` and `research/candidate-models.json`
are preserved research sources. Their commands describe the original layout.
To reproduce those bytes, place both sources in an empty disposable directory
under `.hexaemeron/research/` and run each report's recorded command there.
The archived probe overwrites its report operand; use it only in that empty
disposable directory. The public proof CLI does not invoke that probe.

The scaffold tests reconstruct this layout and compare all fifteen reports
byte for byte. Those calculations compare authored routing models, execution
ownership, additional engine counts and serialized sample size. They establish
no product conformance, runtime, allocation or machine-learning result.

`fixtures/provenance.json` records every published research/report/fixture
path and digest, plus the accepted documents and decision. No local service
archive, native report, credential or private-custody input is published.
Run `python3 -m unittest discover -s plugins/hexaemeron/tests -p test_native_guard_admission_scaffold.py`
for the focused checks; the existing Hex runner discovers the same tests.

## Continue after this step

Step 2 implements the parser and bounded reader. Step 3 joins immutable routes
to Fiat receipts. Step 4 demonstrates actual native execution in a separate
signed disposable repository and settles release conformance. Both old service
runs remain halted. Service work needs a fresh reviewed run after the completed
release is installed; old controller markers and receipts cannot be backfilled.
