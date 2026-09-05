# Evidence bundle: the content-addressed object rule on the skills repository

The v9.2.3 reopening's second job: the content-addressed object rule left
the draft it had been since commit `5d5aba7` and shipped with the record
that lets someone else trust it. The rule's binding condition did not
change. What changed is that its central property is now pinned by a test
that fails without it, the skill and the example document it, and this
bundle records what the rule binds on this tree and what it costs, from
commands a reader can rerun. Measured on 2026-09-05 from the repository
root, on the tree at the step's entry.

## What the rule binds on this tree

Read from [.horos/boundary.json](../../../../.horos/boundary.json):
every entry whose category is `content_addressed`, grouped by the store
root above the algorithm segment.

- 78 entries, 7,850,052 bytes in total, out of 2,524 files walked at the
  step's entry (2,525 once this bundle is tracked). Every entry carries the
  evidence
  `sha256 digest of the file's own bytes equals its name` at grade `hard`.
- `plugins/alexandria/examples/compound-v3-phase0-v0/release/objects/sha256/`:
  70 files, 7,844,877 bytes. A real store, the sharded layout, the release
  of the Compound v3 Phase 0 method proof. This is the store the v9.2.3
  epoch row found as the census's `(no suffix)` row.
- `plugins/alexandria/examples/proof-backed-state-v0/release/objects/sha256/`:
  6 files, 5,081 bytes. A real store, the sharded layout.
- `plugins/horos/examples/fixture/store/`: 2 files, 94 bytes. The shipped
  example's store, one flat object under `blobs/sha256/` (49 bytes) and one
  sharded object under `objects/sha256/7d/` (45 bytes). The fixture is a
  specimen, not a store anyone releases from; its bytes are counted here
  because the boundary counts them, and they are not evidence that a real
  flat-layout store exists in any home tree.

Recompute the inventory with:

```bash
python3 -c "
import json, collections
doc = json.load(open('.horos/boundary.json'))
rows = collections.Counter(); total = collections.Counter()
for e in doc['entries']:
    if e['category'] != 'content_addressed': continue
    root = e['path'].split('/sha256/')[0] + '/sha256/'
    rows[root] += 1; total[root] += e['bytes']
for root in sorted(rows): print(rows[root], total[root], root)
print(sum(rows.values()), sum(total.values()))
"
```

## What it costs

The rule is the only one in `horos.py` that reads a whole file rather than
a bounded prefix, so the shape gate runs first and only a path already
shaped like a content-addressed object is ever hashed. The study's budget
is that hashing every store object the boundary classifies stays at or
under 250 ms.

Re-measured at this step:

```bash
python3 .hexaemeron/design-reports/resolve.py harden-record store-hash-ms
```

Result: 5 ms, the median of five runs whose samples were 12.1, 4.7, 4.7,
4.7 and 4.7 ms, hashing all 78 objects (7,850,052 bytes) through
`digest_matches_name`. The resolver writes the report
`harden-record-store-hash-ms.json` beside itself, and the report written at
this step is byte-identical to the one the closed design record pins
(SHA-256 `07ba5e3e65b4fec56d54e1df202884ae991e509e539aaabf088f7d21aaf6c220`).
The budget holds with a margin of 245 ms.

## The drift demonstration

The property the run pins: when one byte of a store object changes,
`check` names that object as drift and exits 1. Step 2 pinned it in a
disposable git repository
(`test_a_tampered_store_object_is_named_as_drift`); the same demonstration
runs by hand against the shipped example.

```bash
printf x >> plugins/horos/examples/fixture/store/objects/sha256/7d/7d2aa7ee1155c6102a2dbb74ff9efa27115cec234f2ea4555a0d3a92663d7e82
python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture
git checkout -- plugins/horos/examples/fixture/store
```

The second command prints, in this order, exit 1:

```text
drift: .horos/boundary.json#counts: field changed: {'bytes_binary': 17, 'bytes_content_addressed': 94, 'bytes_generated': 190, 'bytes_lockfile': 54, 'bytes_vendored': 94, 'files_skipped_unreadable': 0, 'files_walked': 15} -> {'files_walked': 15, 'files_skipped_unreadable': 0, 'bytes_generated': 190, 'bytes_binary': 17, 'bytes_vendored': 94, 'bytes_content_addressed': 49, 'bytes_lockfile': 54}
drift: store/objects/sha256/7d/7d2aa7ee1155c6102a2dbb74ff9efa27115cec234f2ea4555a0d3a92663d7e82: in the boundary but no longer evidenced by the tree
2 path(s) drifted
```

The `#counts` line records the 45 bytes that left the content-addressed
count; the second line names the tampered object. The third command
restores the fixture.

## The four guard tests

All four live in `plugins/horos/tests/`, each observed red against a rule
broken on purpose before it was kept, and the horos suite runs at 239
tests:

- `test_a_tampered_store_object_is_named_as_drift`: a sharded store object
  in a disposable git repository is scanned, checked clean, overwritten,
  and named as drift by `check` with exit 1.
- `test_an_unreadable_store_object_is_skipped_never_classified`: a mode-000
  store object is counted under `files_skipped_unreadable` and never
  classified; the test skips by name when the suite runs as root.
- `test_a_deeper_shard_path_stays_readable`: `objects/sha256/ab/cd/<digest>`
  is not a store shape the rule accepts, so the file stays readable.
- `test_an_uppercase_algorithm_segment_stays_readable`: `objects/SHA256/`
  is not an algorithm segment the rule accepts, so the file stays readable.

## The refused candidates

The closed design record, `.hexaemeron/design-evidence.json` in the run
worktree and tabulated in section 4 of the committed
[study](../content-addressed-objects/study.md), compared four candidates on
six criteria; three were refused on measured
gates, and the next run that wants one of them should re-measure against
this record rather than re-argue it.

- `widen-layouts` (add npm cacache's two-level shard layout): refused on
  `added-layouts-unwitnessed`, measured 1 against a gate of 0. The
  resolver searched 2,550 paths (this tree's `git ls-files` plus every
  entry and candidate path in the v2-protocol and wildcat-app-v2
  boundaries) for the shape `content-v<n>/<algorithm>/<xx>/<yy>/` and found
  no witness.
- `aggregate-entries` (collapse a fully verifying store into one directory
  entry): refused on `exact-match-misses`, measured 78 against a gate of 0.
  Every one of the 78 store files would leave the boundary as an exact
  path while issue 896 is open. Its space advantage is real and recorded:
  the aggregated document renders at 12,587 bytes against 37,014 for the
  shipped per-file document.
- `record-only` (documents and the ledger row, no code and no test):
  refused on `open-hardening-gaps`, measured 4 against a gate of 0. The
  resolver enumerates six gaps in the draft and verifies each open on the
  tree by a grep that finds nothing; `record-only` closes only the two
  documentation gaps.

## What witnesses the two layouts

The sharded layout, `objects/<algorithm>/<xx>/<digest>`, is witnessed by
the two Alexandria release stores above. The flat layout,
`blobs/<algorithm>/<digest>`, is witnessed by the OCI image layout
specification (`image-layout.md` in the opencontainers/image-spec
repository, the `blobs/<alg>/<encoded>` rule) and by the shipped fixture
only; no home tree holds a flat store. This is the study's risk
`self-witness`, accepted and recorded here rather than hidden by counting
the fixture as a real store.

## Where the pinned property goes next

Issue 380 (the horos-3 wish, a verified exclusion list) is the natural
consumer of the property this run pins: a `check` that re-derives every
digest before it prints. That issue is generation work behind the frontier
and was not touched here.

## The agent-instruction fixture chain

`plugins/horos/skills/horos/SKILL.md` is bound by whole-file digest in
`tests/fixtures/agent-instruction-v1/manifest.json`, and the offsets of its
reviewed span, the `horos-boundary-check` promise, enter the corpus digest
that the measurement and parity records carry. This run's edits to that
file all sit before the reviewed span, which stayed byte for byte where its
digest says it is. The chain was therefore re-pinned by carrying the
recorded token counts and parity responses unchanged: every derived field
(byte lengths, digests, offsets, correlation ids, deltas and the summary)
was recomputed exactly as the checker's validators compute it, and only
the observed values, which were measured on the same reviewed bytes, were
carried. That is the procedure the repository used on 2026-09-04, and it is
honest because the bytes the counts describe did not move.

## Machine-readable capture lines

<!-- content_addressed:entries 78 -->
<!-- content_addressed:bytes 7850052 -->
<!-- content_addressed:store_hash_ms 5 -->

## Demonstration at the run head

The study's demo path, run in order from the repository root at run head
43b516f6 on 2026-09-05, with
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false`
exported for every `unittest` command. The root suite is shown twice: once
in a clean detached snapshot of the head, which is the exit, and once inside
the Fiat run worktree, where two `test_agent_instruction_corpus` tests are red
because the #1098 prover reads the run's own `.hexaemeron/design-evidence.json`
(audit finding S1-R1-02, accepted, carried to integration).

```text
$ python3 plugins/horos/skills/horos/scripts/horos.py check .
boundary matches the tree
exit 0

$ python3 -m unittest discover -s plugins/horos/tests -t plugins/horos
Ran 239 tests in 5.784s
OK

$ printf x >> plugins/horos/examples/fixture/store/objects/sha256/7d/7d2aa7ee1155c6102a2dbb74ff9efa27115cec234f2ea4555a0d3a92663d7e82

$ python3 plugins/horos/skills/horos/scripts/horos.py check plugins/horos/examples/fixture
drift: .horos/boundary.json#counts: field changed: {'bytes_binary': 17, 'bytes_content_addressed': 94, 'bytes_generated': 190, 'bytes_lockfile': 54, 'bytes_vendored': 94, 'files_skipped_unreadable': 0, 'files_walked': 15} -> {'files_walked': 15, 'files_skipped_unreadable': 0, 'bytes_generated': 190, 'bytes_binary': 17, 'bytes_vendored': 94, 'bytes_content_addressed': 49, 'bytes_lockfile': 54}
drift: store/objects/sha256/7d/7d2aa7ee1155c6102a2dbb74ff9efa27115cec234f2ea4555a0d3a92663d7e82: in the boundary but no longer evidenced by the tree
2 path(s) drifted
exit 1

$ git checkout -- plugins/horos/examples/fixture/store
(tree clean after restore)

$ python3 -m unittest discover -s tests   # clean detached snapshot of 43b516f6
Ran 1207 tests in 95.942s
OK

$ python3 -m unittest discover -s tests   # inside the run worktree
FAIL: test_a_candidate_outside_the_design_record_is_refused (test_agent_instruction_corpus.AgentInstructionCorpusTests.test_a_candidate_outside_the_design_record_is_refused)
FAIL: test_prover_selftest_exits_zero_and_writes_a_closed_report (test_agent_instruction_corpus.AgentInstructionCorpusTests.test_prover_selftest_exits_zero_and_writes_a_closed_report)
Ran 1207 tests in 102.193s
FAILED (failures=2)

$ python3 -m unittest tests.test_marketplace_prose
Ran 23 tests in 0.260s
OK
```
