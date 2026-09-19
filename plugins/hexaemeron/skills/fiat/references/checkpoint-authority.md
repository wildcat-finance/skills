# Checkpoint authority conformance interface

## Current state

Only the Step 1 reporting scaffold ships. Every protocol criterion is
unimplemented and unresolved. The selected candidate is `ordered-replay`;
`eager-index` remains historical comparison evidence and cannot run here.
Native checkpoint v1 remains unchanged. The governing design is
`adr/verify-checkpoint-authority-by-ordered-replay`.

## Invocation and evidence

Run from the repository toolchain:

```bash
python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py --candidate ordered-replay --criterion records-and-signatures --report .hexaemeron/reports/ordered-replay-records-and-signatures.json
```

The other closed criterion names are `native-boundary-coverage`,
`authority-replay` and `released-interoperability`. The report operand must
be exactly `.hexaemeron/reports/ordered-replay-<criterion>.json`.
The implementation locates its repository from its installed source path;
the working directory does not redirect the output.

An admitted request writes a closed `protasis-design-report/v1` containing
`value: false` and `exit: 3`, then returns exit 3. Its sibling
`ordered-replay-<criterion>.evidence.json` records the same criterion, the
report digest, actual implementation and fixture-manifest digests, no executed
cases, `complete: false`, and `criterion-not-implemented`. The event is also
printed as one JSON line. These outputs answer which gate was requested,
which source was used and why it has no conformance result. No source bodies,
credentials, archive bytes or arbitrary diagnostics appear.

The public design's selection reports remain original measurements. A new
scaffold report cannot satisfy Protasis: its value is false and its exit is
nonzero. Later steps must execute their declared behavioral cases before
issuing a passing report and preserve source, fixture and output identities.

## File boundary and recovery

Candidate and criterion values come from fixed sets. Unknown values, unknown
options and abbreviated options return exit 2 with a fixed invocation code.
Paths outside the exact report grammar refuse before any report write.
Inputs are fixed source paths, regular single-link files, read without
following symlinks with a 64 KiB cap and stable identity checks. The fixture
manifest has one closed unsupported-work shape; altered or unreadable inputs
refuse. Each output is capped at 16 KiB and created exclusively with mode 600.
Existing outputs, symlinks, special files and symlinked parents refuse.

The evidence file precedes the design report. A crash or write failure may
leave a partial pair, which still cannot establish success. Preserve that
pair for inspection; a retry cannot overwrite it. An operator may move the
owned prior attempt to retained evidence before rerunning the same command.
Directory descriptors and observed namespace checks detect substitutions;
they do not make concurrent directory renames atomic. The caller must own the
report directory and exclude competing writers. The command reads no cloud
or live controller state and does not authenticate any authority record.
