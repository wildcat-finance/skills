# Audit applicability and bounded source reads

Step 2 implements the accepted `typed-applicability` parser. It checks original
source bytes and derives routes from existing Protasis captures. Fiat admission,
replay and native execution remain due in Steps 3 and 4. This step supplies no
parent-red guard, service result or host-isolation claim.

## Author and check a declaration

[contract.md](contract.md) gives the closed fields, four dispositions, limits
and refusal codes. Add one isolated column-zero `audit-applicability` JSON
fence to a study with a valid known-failure inventory. Preserve its complete
source/view set, cite exact source byte spans and statuses, and select only
existing finding or criterion ids. Then run from the repository root:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py runbook.md --gate-root . --applicability study.md
```

The command validates the registered runbook interfaces and the source join;
it executes no declared command. Ordinary prose naming `audit-applicability`
remains absent. Malformed attempted declarations, including nested fences,
refuse. Null source status means unknown. Historical and excluded rows grant
no current success; an integration requirement still owes observed execution.

`plugins/hexaemeron/tests/test_audit_applicability.py` builds complete authored
fixtures with all four dispositions and an explicit empty-inventory case.
The original [shape example](fixtures/applicability.json) and its source bytes
remain unchanged. That original example is not a checked inventory or a record
of execution.

## Run the two implemented proofs

```bash
python3 docs/native-guard-admission/proof.py --candidate typed-applicability --criterion applicability-parser --report .hexaemeron/reports/design/typed-applicability-applicability-parser.json
python3 docs/native-guard-admission/proof.py --candidate typed-applicability --criterion bounded-reader --report .hexaemeron/reports/design/typed-applicability-bounded-reader.json
```

Each resolver exercises the parser, then creates its report and a companion
ending in `.evidence.json`. The companion binds the report and source digests,
actual test counts and any resource measurements. The bounded-reader proof
loads one fixture three times: a 256 KiB study, 32 source/view pairs, 128 rows,
64 KiB spans, one 2 MiB source, one 2 MiB view and 16 MiB aggregate source/view
bytes. Each load must stay within 30 seconds and 64 MiB of traced allocation.
Fixture construction is outside those measurements. This checks a budget on
the recorded host and interpreter; it makes no speedup claim.

The [Step 2 records](reports/conformance/) preserve those reports and companions
from the executed resolvers. Their source digests identify the implementation
that produced each observation.

Report operands must name JSON files below `.hexaemeron/reports/`. Existing
leaves, linked ancestors, traversal and outside paths refuse. The writer uses
exclusive leaves, retains partial evidence after interruption and never
replaces a report. Use a fresh path after inspecting an interrupted write.

The selected candidate's four later operations and all twelve operations for
the rejected candidates still exit 2 with `operation-unavailable`. They create
no report. Source checks and parser proofs cannot settle native execution.

## Preserve the original evidence

The accepted [study](study.md), [runbook](runbook.md) and
[design record](design-evidence.json) keep their original bytes, dates,
version assumptions, paths and eighteen pending conformance declarations.
The completed resolver reports supply evidence at the named stop points;
they do not rewrite that design record. Its `.hexaemeron/` paths name the
original run. The decision remains `adr/route-audit-obligations-to-their-evidence`.

The fifteen selection reports remain exact. To reproduce them, place
`research/design_probe.py` and `research/candidate-models.json` in an empty
disposable directory under `.hexaemeron/research/` and run each report's
recorded command there. The archived probe overwrites its operand; use it
only in that disposable directory. These calculations compare authored
models, execution ownership, engine counts and serialized sample size.
They establish no product conformance or machine-learning result.

`fixtures/provenance.json` binds the public documents, sources and examples.
No local service archive, credential or private-custody input is published.
The Hex runner discovers the parser and scaffold tests.

## Continue after this step

Step 3 joins immutable routes to Fiat receipts. Step 4 demonstrates native
execution in a separate signed disposable repository and settles release
conformance. Both old service runs remain halted. Service work needs a fresh
reviewed run after the completed release is installed; old controller markers
and receipts cannot be backfilled.
