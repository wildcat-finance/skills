# instruction architecture workbench

this directory is a research boundary, not a production loader. Markdown at
`a2b634d8e039af988bf30c8316defccf70071d8d` remains authoritative. the Step 1
commands inventory that source, prove its loader edges, classify every physical
byte and seal disjoint development and holdout cohorts.

generate the baseline:

```text
python3 research/instruction-architecture/benchmark.py build-baseline
```

verify it without rewriting anything:

```text
python3 research/instruction-architecture/benchmark.py verify-corpus --manifest tests/fixtures/instruction-architecture/corpus-manifest.json
python3 research/instruction-architecture/benchmark.py verify-loader --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --graph tests/fixtures/instruction-architecture/loader-graph.json
python3 research/instruction-architecture/benchmark.py verify-partition --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --partition tests/fixtures/instruction-architecture/byte-partition.json
python3 research/instruction-architecture/benchmark.py verify-seal --manifest tests/fixtures/instruction-architecture/corpus-manifest.json --cohorts tests/fixtures/instruction-architecture/cohorts.json --seal tests/fixtures/instruction-architecture/holdout-seal.json
```

every accepted JSON record is canonical UTF-8 with duplicate keys and
non-finite numbers refused. object fields are closed by the validator and the
companion schema. source reads are bounded regular-file reads matched against
the fixed Git blob. Git runs from a closed set of absolute system-owned paths,
with lazy fetch, global and system configuration, prompts and ambient
environment disabled. writes use a same-directory temporary file, `fsync`,
atomic replacement and a complete reread.

the 231 declared scenarios cover the 93 base combinations of 31 selectable
canonical skills and three actual host routes: repository checkout, isolated
Agent Skills and standalone plugin. each closure starts at that route's entry,
binds one selected plugin runtime and skill plus a closed condition vector, and
follows only matching source-directed workflow edges. every Ariadne scenario
chooses one operation; every Kronos scenario chooses one target and dispatches
it through Fiat.

the holdout seal names membership and case-slot classes, but contains no task,
answer, scorer key or model output. do not add those fields before the frozen
experiment opens the envelope.
