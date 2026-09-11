# Design probes: an archived record of method, not runnable tooling

These eight modules are the ones that produced the sixteen reports under
`../reports/`. They are kept byte-for-byte as they ran, so each report's
`command` field remains a true statement about the code that produced its
value. They are a record, not a tool, and they do not run from this directory.

## Why they fail here

`clone_verdict.py`, `recall.py` and `strategies.py` compute
`ROOT = Path(__file__).resolve().parents[2]`. That is the repository root from
the working directory they ran in, `.hexaemeron/design-probes/`, and it is
`docs/` from this one, so the import of the checker resolves to a path that
does not exist. Six of the eight fail at import here: those three, plus
`failclosed.py`, `runtime.py` and `space.py`, which import `strategies`.
`deps.py` and `specimen.py` import cleanly and still measure nothing on their
own.

Repointing `ROOT` would make them import and would falsify the reports, which
name `.hexaemeron/design-probes/...` as what ran. It would also not make them
reproduce, because of the inputs below.

## What they read that is not here

- `recall.py` and `clone_verdict.py` read a 19 MB extraction of the pinned
  application clone at `.hexaemeron/validation/wildcat-app-v2`, which is
  gitignored and was never a tracked path.
- `recall.py` also reads `corpus/decoy.ts` beside itself, the one stated decoy
  file holding two occurrences that appear only inside a block comment and
  inside a string literal. It is not shipped here. The study describes its
  contents and the 14-against-16 result that separates a masked reader from an
  unmasked one.

So the reports are reproducible from the study's description of the method, not
by running these files. The three `clone-verdict-e001` cells in
`../design-evidence.json` read `pending` and name
`python3 .hexaemeron/design-probes/clone_verdict.py` as their resolver. The
selected candidate's cell is settled by the sixteenth report,
`../reports/span-index-clone-verdict-e001.json`, which that resolver wrote once
the recognisers existed and which records a count of 14; the record passes
its `integration` transition against it. The two rejected candidates' cells
stay pending, because only the selected candidate's cell is due.

## What is checked mechanically

`tests/test_ephoros_typescript_parity.py` proves the shipped record's schema and
selected candidate, that the fifteen cited reports resolve at the digests the
record states, that those paths stay record-relative, and that every relative
link in the shipped study resolves. It asserts nothing about these modules.
