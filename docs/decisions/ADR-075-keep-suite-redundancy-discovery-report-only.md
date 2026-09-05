# ADR-075: Keep suite-redundancy discovery report-only

## Status

Accepted, 2026-09-04.

## Context

The repository carries 236 test files and 7,341 test methods across 20 Python
checks. Nothing said which of them still earn their place. A test can be
obsoleted by the code it was written against, superseded by a later test, or
duplicated outright, and none of those states announces itself: an obsolete
test usually still passes.

A first sweep answered the mechanical part of that question. Attributing
covered source lines to the test that executed them, then asking which files
cover a line nothing else covers, established that 171 of 236 files each
reach a line no other test file reaches, and that no test file in the
repository is unreachable from `tests/check-map-v1.json`. It also produced 25 files with no
unique coverage, of which 9 were an artefact of near-identical scaffold tests
in separate plugins running one shared helper over different data.

The remaining 16 were then put through mutation. Four killed a mutant no other
file killed and are therefore irreplaceable. Twelve did not, under budgets
ranging from 528 mutants down to 3.

That spread is the decision this record exists to fix in place. Line coverage
is insensitive to assertions: `plugins/ariadne/tests/test_schema_agreement.py`
covers 1,718 lines and none of them uniquely, and its docstring records three
drift findings it caught that nothing else did. A candidate count cannot
authorise a deletion, and neither can an unproven mutation verdict, which is
absence of evidence rather than evidence of absence.

[ADR-053](ADR-053-keep-dead-code-discovery-report-only.md) already settled the
same question for source: dead-code discovery reports, and never deletes.

## Decision

Provide one report-only command, `scripts/suite_redundancy.py`, that attributes
covered lines to test files and test methods and classifies them. Its universe
is the repository source outside any test tree, excluding the analyser itself.
Findings are candidates for review. No count fails the command, blocks a merge
or authorises removing a test.

The report separates three states rather than two. A file that uniquely covers
a line cannot be removed without losing that line, and the report says so; that
negative result is the half a reader can rely on. A file that covers lines but none uniquely is a review
candidate. A file that covers no measured line at all is neither, because the
tracer runs in-process and cannot see a subject driven through a subprocess or
a subject that is prose, a schema or a fixture.

A method-level pass names two tests only when they share both a covered-line
set and a hash of their normalised body. Coverage identity alone groups 1,796
methods and means nothing; the intersection named 2 pairs.

The `suite-redundancy` scope owns the command, its tests and this record. The
checked runner continues to own scope selection and process budgets.

## Alternatives

Run the suite once per test file and diff coverage. Rejected because it is
236 suite runs for an answer one traced run already contains: removing a file
removes exactly the lines its own tests executed.

Gate CI on the candidate count. Rejected for the reason ADR-053 gives and one
more of its own. Twelve of the sixteen strongest candidates survived mutation
without being shown redundant, and seven of those twelve had fewer than 50
mutants to survive.

Ship the mutation harness alongside the analyser. Rejected for now. It must
mutate source to work, so it needs a copy of the tree and a per-candidate
budget, and against the hexaemeron suite it spent 2,040 seconds to produce 54
mutants. It is a deliberate manual investigation, not a check.

Report a method as removable when its covered-line set matches another's.
Rejected because table-driven cases share a set by construction: 26 methods in
`tests/test_agent_instruction.py` cover the same 48 lines with different
inputs.

## Consequences

Contributors get one deterministic report over any set of traced suites,
naming what is irreplaceable before what is doubtful. The analyser adds no
dependency: it uses `sys.monitoring`, claims a free tool identity so a run
under another tracer does not collide, and edits nothing it measures.

Tracing costs 1.2 to 1.5 times an untraced run, so the full sweep is a command
a contributor runs, not a check CI carries. Only the analyser's own tests run
in CI.

One duplicate found by the first sweep is removed with this record:
`test_scan_without_the_flag_is_byte_for_byte_unchanged` in
`plugins/horos/tests/test_census.py` was byte-identical, over the same fixture,
to `test_the_cli_json_output_matches_the_committed_boundary` in
`plugins/horos/tests/test_discipline.py`. No scenario made one fail while the
other passed. The boundary file keeps the assertion.

Two limits are worth stating before somebody reads a verdict as more than it
is.

A vacuous assertion is invisible here, and this report will rank it highest.
`plugins/lazarus/tests/fake_rpc.py` answered every `eth_getProof` with
`proof_records[0]` whatever address was asked for, so a test asserting one
account's proof was asserting against another account's record and passing.
Those tests covered lines nothing else covered, so this analyser would have
reported them as the only tests reaching those lines for as long as the fixture
stayed wrong. #1183 made
the fixture address-aware. The general shape survives the fix: a unique-coverage
verdict says a line would go uncovered without this test, never that the test
proves anything about it.

Reachability is not execution. This report establishes that every test file is
reached by some check in `tests/check-map-v1.json`, which is a claim about the
map and not about what ran. A class whose `setUpClass` aborts takes its tests
out of a run while its file stays reachable, and #1183 found the hexaemeron
shard doing exactly that. `plugins/hexaemeron/tests/run_tests.py` is that
suite's only correct entry point; `unittest discover` raises an ImportError on
that tree and reports a clean suite. Neither state is a redundancy question,
and neither is answered here. A per-suite expected test count answers both.

Twelve files stay unresolved. A later decision may gate on them; it will need
assertion-level evidence this record does not claim to have.
