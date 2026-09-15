# Issue 508 contracts and fixtures

Delivery status:

- Step 1 preserves the receipted design and defines inert fixture shapes.
- Step 2 adds the native worker supervisor described below.
- Step 3 adds controller launch and private report admission, preserving independent origin changes.
- Step 4 adds cumulative packet export, evidence validation and detached attachment binding; see the [format and custody reference](../../plugins/hexaemeron/skills/fiat/references/carryover-packet.md).
- Step 5 adds complete replacement reconstruction and executed current guard coverage. Its conformance reports, implementation checks and independent audit passed.
- Step 6 adds command-interface validation and receipt replay, including checkpoint relocation. Conformance reports, implementation checks and the independent audit passed.
- Step 7 adds the joined replacement lifecycle fixture. All eleven conformance criteria pass; the full suite, independent product audit and delivery remain pending.

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
current canonical runbook, including its twenty-one appended amendments. Those
amendments select the `unittest-json-v1` Elenchus adapter while retaining the
`elenchus.unittest.v1` output schema, and name
`test_confined_replacement_lifecycle.py` for Step 7. The eighth amendment adds the current Fiat version to Step 2's checkpoint
compatibility set and names its documentation paths. The ninth permits Step 3's current admission-status updates and this exact amended-runbook copy. The tenth names Step 4's format and custody documentation, current status and exact amendment copy; it leaves replacement admission for Step 5. The eleventh adds the custody promise's coverage cases and structural reader specimens. The twelfth names its identity history, current count assertions and current demonstration input and count refresh, while preserving historical evidence. The thirteenth permits the new custody promise in the existing test's expected Fiat population, keeping the exact equality assertion. The fourteenth names Step 5's reconstruction and guard modules, internal worker input, documentation and separate replacement promise coverage; it preserves exact current-count assertions and historical evidence. The fifteenth permits the existing verification test to assert `allow_pending_replacement=True` and ordered observation and filing events. The sixteenth names Step 6's canonical command grammar, version records, distinct validation promise and current consumers, preserving historical evidence and all entry and exit requirements. The seventeenth permits explicit historical fixture creation in the shared controller harness before its first init receipt, while real initialization and new gate tests keep the strict contract. The eighteenth records command validation as Consequence 1, keeps the runtime count at 49 without a new native binding, and preserves existing reader evidence and unknowns. The nineteenth permits registered CLI source and literal Exit commands in two current-init fixture families while preserving strict initialization and every existing assertion. The twentieth updates the one Protasis evolution-contract test for the new generation while retaining its historical row assertions and mature-frontier checks. The twenty-first permits the ordinary relative-root replay fix and current evidence-binding refresh while retaining identity, symlink and historical-evidence checks.
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
Step 4's [packet validation and attachment readback](../../plugins/hexaemeron/skills/fiat/references/carryover-packet.md) and Step 5's replacement admission provide separate runtime checks. Step 6 adds separate [command-interface validation](../../plugins/hexaemeron/skills/protasis/references/gate-commands.md); it does not execute declared commands.

The conformance fixture inventory mirrors every pending criterion and transition
in the frozen design. For `whole-worker-sandbox`, `prove_issue_508.py` executes
`worker-deadline`, `worker-output-cap`, `whole-launch-dispatch`,
`origin-drift-recovery`, `single-cumulative-reconstruction`,
`executed-inoculation-guards`, `carryover-lineage-recovery`,
`source-owned-report-compatibility`, `gate-parser-no-execution` and
`gate-receipt-replay` and `whole-path-demonstration`. All eleven current criterion reports pass. Step 7 freshly reran the ten earlier criteria to separate report destinations, preserving their twenty historical canonical artifacts. The three command reports
were refreshed after the relocation repair; earlier runtime evidence remains
bound to its observed sources, with historical report bytes preserved. The Step 5 fixtures use actual local signed Git, checkpoints,
controller admission and native guard execution with controlled attachment
transport. They preserve historical unknowns and do not establish an independent
audit or a model evaluation.

The Step 7 report covers six specimens within one passing lifecycle test. It
uses actual local signed Git, archived exhaustion, export and retirement,
complete current-base reconstruction, native mapped guards, strict current
command receipts and controller integration transitions. Attachment and host
Git/GitHub delivery transport are controlled fixtures. Its new audit round
checks transition handling; it does not replace the independent product Warden
audit. Missing or changed producer evidence, a missing gate receipt and CLI
source drift refuse integration. The missing gate-receipt specimen establishes
state/ledger disagreement, not a separate semantic verdict about that receipt.
The test also retains symlink refusal. Default relative-root verification now
passes an absolute spelling to replacement replay without resolving symlink
components. The same-test old/fixed execution pair records that repair directly;
it is separate from a normalized Elenchus Git-parent verdict. No model backend,
VM deployment, external publication or protection of conversation tools is
claimed.

The resolver writes a `protasis-design-report/v1`
boolean only after every named specimen passes, with observations in a companion
`.observations.json` file. Every other candidate and criterion exits 1
with `executor-unimplemented` and opens no report path. A caller must require a fresh zero exit before consuming a report,
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
2. It remains historical negative evidence. A fresh Step 6 parser specimen
separately refuses the same four-operand shape without executing the command.


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
Process inspection is explicitly denied; sysctl reads permit only the five named
queries needed by `os.uname`. Native specimens check both numeric process-argument
interfaces against a controlled environment sentinel, plus outside content,
write, hard-link and symlink denial.

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
