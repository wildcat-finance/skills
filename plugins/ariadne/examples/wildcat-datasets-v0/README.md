# Wildcat dataset statements

This example binds both accepted Ethereum mainnet Wildcat releases through
Ariadne's existing `dataset/v1` interface. It ships one unsigned statement per
estate, exact inventories, and complete verification and refusal reports.

- V1 covers inclusive blocks 18743513 to 22074622: 110 file subjects and
  111 outer subjects including the bundle.
- V2 covers inclusive blocks 21866550 to 26022093: 128 file subjects and
  129 outer subjects including the bundle.

V1 release ID: `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`.
V2 release ID: `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`.

The [study](https://github.com/wildcat-finance/skills/tree/main/plugins/ariadne/examples/wildcat-datasets-v0/spec/study.md), [runbook](https://github.com/wildcat-finance/skills/tree/main/plugins/ariadne/examples/wildcat-datasets-v0/spec/runbook.md) and
[design evidence](https://github.com/wildcat-finance/skills/tree/main/plugins/ariadne/examples/wildcat-datasets-v0/spec/design-evidence.json) preserve the accepted Fiat records
unchanged. The full-release choice binds every file; the
[Ariadne ledger](../../skills/ariadne/EVOLUTION.md) records why manifest-only
lost. V1 and V2 are separate estates. Each statement has a null baseline and
an explicit first-statement reason.

## Build and verify

Use a full source checkout and its pinned Python. The caller reads the two
existing release trees; it executes no producer or historical command. These
are the external directories used for the accepted rebuilds on this host:

```bash
export ARIADNE_WILDCAT_V1_RELEASE='/Users/c0rtexzer0/.codex/worktrees/95b4/Wildcat Skills/tmp/fiat-evidence/fiat-1374/v1-rebuild/release'
export ARIADNE_WILDCAT_V2_RELEASE='/Users/c0rtexzer0/.codex/worktrees/95b4/Wildcat Skills/tmp/fiat-evidence/fiat-1374/v2-rebuild/release'
python3 plugins/ariadne/examples/wildcat-datasets-v0/demo.py build --output /absolute/existing-parent/wildcat-statements-1
python3 plugins/ariadne/examples/wildcat-datasets-v0/demo.py verify --output /absolute/existing-parent/wildcat-statements-1
python3 plugins/ariadne/examples/wildcat-datasets-v0/demo.py build --output /absolute/existing-parent/wildcat-statements-2
python3 plugins/ariadne/examples/wildcat-datasets-v0/demo.py verify --output /absolute/existing-parent/wildcat-statements-2
diff -r /absolute/existing-parent/wildcat-statements-1 /absolute/existing-parent/wildcat-statements-2
```

Replace the output examples with fresh sibling directories under an existing
parent. The release variables may name relocated, byte-identical copies.
Both are required; no historical path is opened by default. The two builds
produce identical statement bytes and report contents. `verify` reads both
external trees again, reconstructs every output, reruns the real verifier and
compares the complete output inventory and bytes. A zero exit means all those
checks passed. A refusal exits 1 and names the failed relation.

Each estate directory contains `statement.json`, `inventory.json`,
`coverage.json`, `provenance.json`, `verify.json` and `verify.txt`.
`refusals/` holds JSON and text reports for missing `gaps`, a missing gap
reason, and a gap extending outside the declared interval. Each positive
report retains seven numbered gates and three dataset checks. Each negative
report comes from mutating the actual statement and running the real verifier;
only its `coverage` check fails. `observation.json` records zero attempted
Python socket calls and the observation's limited boundary.

The adapter verifies every manifest and component digest, exact file inventory
and declared size. It derives counts from `/records`, `/epochs`, `/shards` or
`/entries`, then compares them with the source collection and coverage counts.
`manifest.json` counts as one metadata document. It does not count arbitrary
JSON objects as events. Digests stream through bounded reads; component JSON
is bounded by Alexandria's 67,108,864-byte source cap. No speedup or peak-memory
claim follows from those controls.

Existing output, input/output containment, traversal, symlinks, non-regular
files, missing or extra files, digest drift, unsupported selectors and count
mismatches refuse. The adapter checks release bytes before and after capture.
These checks observe drift; they do not lock the filesystem or provide an
atomic snapshot against concurrent namespace changes. An interrupted write
may leave its new output incomplete. Inspect that directory and use a fresh
one; reruns never replace it.

## Verify the committed records

```bash
python3 plugins/ariadne/examples/wildcat-datasets-v0/demo.py verify-preserved
python3 plugins/ariadne/tests/run_tests.py
```

`verify-preserved` needs no archive or release environment. It checks the
[committed statements and reports](https://github.com/wildcat-finance/skills/tree/main/plugins/ariadne/examples/wildcat-datasets-v0/preserved/) against the exact accepted
metadata, reconstructs inventories, checks producer, claims, coverage and
baseline fields, and reruns Ariadne's statement and coverage-refusal gates.
It does not reread external components, derive their counts again, rebuild a
release or repeat the saved socket observation. Reading preserved execution
reports does not establish a new execution.

The tests exercise independent hostile path, count, digest, identity and report
specimens. Full real-input builds are separate mandatory delivery evidence;
they are not silently skipped when archives are absent.

## Input custody and producer

[inputs.json](https://github.com/wildcat-finance/skills/tree/main/plugins/ariadne/examples/wildcat-datasets-v0/inputs.json) pins the original specification, ten design reports,
source metadata, and observed input checks. Its `subjects` values exclude the
outer bundle subjects. Its 39-file Step 1 inventory remains unchanged.
The fourteen estate JSON documents use deterministic gzip with `mtime=0` and
separate encoded and decoded byte counts and SHA-256 digests. Both forms have
a 1,048,576-byte metadata limit. The reader checks encoded bytes before bounded
decoding and then checks the exact original decoded bytes.

Each estate preserves the manifest, plan, registry, staging manifest, archive
digest and capture history. Statements bind the exact source and provenance
inventories, decoded metadata digests, archive digest and pinned producer
source files. Archive and producer-source digests are preserved provenance;
this adapter does not open the archives or reconstruct the historical source
checkout. Full release trees and staging archives remain external, with access
required separately and no promise of public availability.

The producer is the observed offline Alexandria rebuild argv, source revision
`104f6f82c390003fb61039d3023d07c1abe05086` and Python `3.14.6`. Original collection
commands, runtime ambiguity and timestamps remain separate provenance. The V2
record does not establish its original collection argv. No command in these
records is executed by Ariadne. V2's old mutable staging omitted
`reconciliation/errors.jsonl`; the observed rebuild used a fresh copy of the
verified archive. Both the refusal and recovery remain in
[inputs/observations/](https://github.com/wildcat-finance/skills/tree/main/plugins/ariadne/examples/wildcat-datasets-v0/inputs/observations/).

## Evidence limits

All 667 V1 and 3,463 V2 interval shards completed in the accepted handoff.
A reasoned whole-interval gap conservatively represents semantic omissions;
it does not say the blocks were unread. The exact captures in `coverage.json`
retain every original gap, unsupported collection, scope, source, evidence
class and access label. Partition notes remain partition notes.

Targeted traces omit transactions without matching subject logs. V1 has twelve
unknown deployment blocks and five equivalent source checkouts; V2 retains its
private source references. The capture does not establish complete positional
agreement, provider completeness, canonical finality or publisher identity.
Both statements are unsigned. Ariadne creates no signature and checks no
signature identity.

The local no-socket observation patches Python socket construction and
connection helpers while this adapter executes. It records zero attempts,
without claiming an operating-system sandbox, syscall trace, native-code
containment, other-process isolation or a restriction on original collection.

The portable package retains only this README from the example. Its metadata,
specification, adapter and reports require the full source checkout. Core
Ariadne capture, verifier and schema runtime files remain installed. This
example reuses the repository licence, Python pin and CI; it adds no dependency
or service.
