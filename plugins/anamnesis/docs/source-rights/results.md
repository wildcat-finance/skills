# Source-rights results

All three corpora rebuild twice to the identities below. Their sources,
policies and graph components retain the bytes recorded at
`7952eafa337f5ba1c4f45417ceb154673f629c1c`; their release identities and
consumer projections changed to bind the retained rights decision.

| Corpus | Release ID | Findings | Remediations | Rounds | Empty rounds |
| --- | --- | --- | --- | --- | --- |
| pilot | `4fb98a0684cd4704ce038787f62e860e33a0fc1c3562670c2d9146a39f0aea9f` | 41 | 19 | 31 | 12 |
| estate | `b321c3541cc665b9adc8734fe83c342ee9260612a3e93ff519f97922d28279b2` | 17 | 0 | 4 | 0 |
| synopsis | `8e827216e88a2735e0e88619c72c93e1a67b0891b7e9c6beac7625a1878cdb3d` | 41 | 19 | 31 | 12 |

## Evidence

The [three-corpus record](three-corpus-demo.json) retains each demo command,
its output and two refusals per corpus: changing the rights digest without
changing the release ID refuses `A109`; an old four-field source row refuses
`A012`. The [governed demonstration run](demonstration-run.json) verifies the
pilot record's current program and source identities with network denied.
The [selected conformance report](reports/retained-rights-implementation.json)
ran the plugin suite and compared all three manifests with the independent
`retained-rights` construction. Its result is `true`.

The [whole-path suite](../../tests/test_s3_source_rights_demo.py) executes the
three demo commands, independently recomputes the six-field source rows and
release preimages, compares both consumer views and their denominators, and
checks that unique holder and statement sentinels reach no release or
projection. [Preserved-input digests](preserved-inputs.json) cover the source,
policy and graph files, prior decision and audit records, historical consumer
input, and both prior ledger histories. The held second-producer job and its
declared input remain unchanged at `anamnesis-v5.2.0`; the demonstration
frontier remains unchanged at `anamnesis-demo-v0.7.0`.

## Rebuilding an old manifest

A four-field manifest cannot verify under this implementation. Keep it as a
historical artifact and rebuild from its original admission policy, curation
policy and exact source bytes into a fresh directory:

```sh
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py release \
  --policy plugins/anamnesis/specimens/pilot/policy.json \
  --curation-policy plugins/anamnesis/specimens/pilot/curation-policy.json \
  --out tmp/pilot-retained-rights
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py verify \
  --release tmp/pilot-retained-rights
```

Use the estate or synopsis policies for those corpora. The destination must
not exist. Preserve the previous identity in historical records; use the new
identity only for the rebuilt release and its newly generated projections.

## Limits

The digest identifies the checked rights decision; it does not establish
legal sufficiency or encrypt its text. Measured demo durations and peak memory
are observations on one machine, with no performance budget. Corpus counts
cover only the preserved records. No finding's truth, remediation correctness,
second producer, per-source mapper or Synkrisis admission is claimed.
