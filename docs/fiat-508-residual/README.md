# Issue 508 contracts and fixtures

Step 1 preserves the receipted design and defines inert fixture shapes. Runtime
launch, carryover admission and command validation are not implemented here.
The [decision](../decisions/drafts/confine-the-worker-before-admitting-its-output.md)
records the selected construction and rejected alternative.

[study.source.txt](study.source.txt) preserves the exact study bytes.
[study.md](study.md) is a reading copy: its five discipline links change from
`../plugins/` to `../../plugins/`, and a `design-bridge` block joins the selected
candidate to its standing decision. No other study text changes.
[source-inventory.json](source-inventory.json) records source paths and digests
for the original study, runbook, design record, audit inventory, probe scripts
and observed selection reports. Their original absolute paths are historical
identities, not portable execution instructions.

The JSON schemas under `plugins/hexaemeron/tests/fixtures/issue508/` describe
inert envelopes only. Their tests check a closed JSON Schema subset without
adding a dependency. Shape acceptance does not establish safe paths, signatures,
attachment truth, complete carryover payloads or executable command validity.
The `.invalid` attachment URL and repeated-letter hashes are fixture data.
Later steps own those runtime checks and their full record formats.

The conformance fixture inventory mirrors every pending criterion and transition
in the frozen design. `prove_issue_508.py` exits 1 with
`executor-unimplemented` for each candidate and criterion. It opens no report
path and emits no `protasis-design-report/v1`. A caller must require a fresh
zero exit before consuming a report, including an existing report.

Two operator questions are answered by the refusal: which candidate and
criterion could not run, and what must happen before acceptance. Its structured
fields identify both and require implementing and executing the complete named
specimen set. No launch, test execution or successful result is inferred.

Run the focused scaffold checks from the repository root:

```bash
python3 -m unittest discover -s plugins/hexaemeron/tests -p test_delivery_contract_fixtures.py
```

The preserved four-draft Brevitas specimen reproduces the current parser's exit
2. It is negative evidence for the later command validator, not a claim that the
new validator has caught it.
