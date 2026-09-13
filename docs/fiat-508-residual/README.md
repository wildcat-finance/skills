# Issue 508 contracts and fixtures

Delivery status:

- Step 1 preserves the receipted design and defines inert fixture shapes.
- Step 2 adds the native worker supervisor described below.
- Controller launch admission, carryover admission and command validation remain pending.

The decision `adr/confine-the-worker-before-admitting-its-output` records the
selected construction and rejected alternative.

## Preserved evidence

[study.source.txt](study.source.txt) preserves the exact study bytes.
[study.md](study.md) is a reading copy: its five discipline links change from
`../plugins/` to `../../plugins/`, and a `design-bridge` block joins the selected
candidate to its standing decision. No other study text changes.
[source-inventory.json](source-inventory.json) records source paths and digests
for the original study, runbook, design record, audit inventory, probe scripts
and observed selection reports. Their original absolute paths are historical
identities, not portable execution instructions.

[runbook.md](runbook.md) preserves the immutable original runbook named by
`source-inventory.json`. [amended-runbook.md](amended-runbook.md) copies the
current canonical runbook, including its eight appended amendments. Those
amendments select the `unittest-json-v1` Elenchus adapter while retaining the
`elenchus.unittest.v1` output schema, and name
`test_confined_replacement_lifecycle.py` for Step 7. The eighth amendment adds the current Fiat version to Step 2's checkpoint
compatibility set and names its documentation paths.
Read the amendments with
the original step text; the preserved source inventory remains unchanged.
Both runbooks record this delivery against its fixed starting commit and
toolchain. For ordinary runtime use, follow [`.python-version`](../../.python-version).

## Fixtures and conformance

The JSON schemas under `plugins/hexaemeron/tests/fixtures/issue508/` describe
inert envelopes only. Their tests check a closed JSON Schema subset without
adding a dependency. Shape acceptance does not establish safe paths, signatures,
attachment truth, complete carryover payloads or executable command validity.
The `.invalid` attachment URL and repeated-letter hashes are fixture data.
Later steps own those runtime checks and their full record formats.

The conformance fixture inventory mirrors every pending criterion and transition
in the frozen design. `prove_issue_508.py` executes `worker-deadline` and
`worker-output-cap` for `whole-worker-sandbox`. It writes a
`protasis-design-report/v1` boolean only after every named native specimen passes,
with capture observations in a companion `.observations.json` file. Every other
candidate and criterion exits 1 with `executor-unimplemented` and opens no
report path. A caller must require a fresh zero exit before consuming a report,
including an existing report.

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


## Native worker capture

[`worker_exec.py`](../../plugins/hexaemeron/skills/fiat/scripts/worker_exec.py)
runs a declared Python, shell or patch worker on supported macOS hosts. It does
not confine the host task or write a controller receipt. Unsupported hosts,
unresolved runtime dependencies and failed native policy probes refuse launch.
The supported-host startup test fails if the policy cannot start Python.

Each launch uses fresh scratch below the target's `tmp/`. The native policy
allows writes there and data writes to the literal `/dev/null` special device.
Content reads are limited to scratch, the installed Python runtime, declared
executables and resolved dependency files, `/System/Library`, `/usr/lib`, three
literal device files and the root directory itself. Global metadata reads remain
allowed: this is not filename or metadata confidentiality. Network and host IPC
have no grants. Shell dispatch declares and hashes both `/bin/sh` and `/bin/bash`.
The supervisor starts with a fixed environment and closes inherited descriptors.
Native specimens check outside content, write, hard-link and symlink denial.

The default 1 MiB cap is shared by stdout, stderr and all admitted artifacts.
At most 32 declared files, 128 inventory entries and eight path components are
accepted. A first excess byte refuses admission; retained streams never exceed
the cap. File-size and CPU limits also apply per process. These limits do not
provide a total scratch disk quota or aggregate descendant resource accounting.

The supervisor observes leader exit without reaping, sends its group signals,
then reaps. A process group cannot prove that no descendant detached. Scratch is
therefore permanently retired even after a normal exit, and uncertain cleanup
remains explicit. The two-second specimen must return within ten seconds. Timeout
admits no output. A successful capture copies declared regular files through
held, no-follow descriptors into private files that the worker cannot change.
Symlinks, hard links, special files, missing outputs and identity drift refuse.
A detached-writer specimen changes scratch after capture while the private copy
retains its original bytes. No later consumer may use the retired scratch as its
artifact source or reuse it for another worker.

The capture record reports policy and executable identities, deadline, shared
cap, elapsed time, retained byte counts, snapshot digests, exit and cleanup state.
On refusal it names a cause and admits no snapshot. Inspect the retired scratch
and repair the cause before starting a fresh launch. The conformance observation
files retain metadata, not the temporary specimen snapshots after fixture cleanup.
