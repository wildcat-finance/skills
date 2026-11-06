# Runbook: emitter-versus-declaration check at a pinned commit

Task: [#1361](https://github.com/wildcat-finance/skills/issues/1361). This
runbook derives from the receipted study for Fiat run 1361. It starts from
`main` at `e9e95b891b3ae642516e017c46b97a18a1480164` on the run branch
`fiat/1361-emitter-versus-declaration-check-at-a-pinne`. The audited source is `wildcat-finance/v2-protocol` at
`f5a26146987926f4811b72a795d662813dedfe85`, with the compiler ABI read at
tag v2.0.0, `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`.

The selected design is `source-and-abi`: a static scan of the two assembly
emitter files and every `event` declaration under `src/`, cross-checked
against the recorded compiler ABI for WildcatMarket and HooksFactory.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 3e98bb53aafb080cf7de9f2f0990cab9dfc9783d7354c526ca817c1e9bdbd703
candidate | source-and-abi
```

The Elenchus runner below was written before Step 1 so that every step can
name it. Step 1 commits it byte for byte; no later step edits it.

```command-interfaces
schema | protasis-command-interfaces/v1
tests/emit_emitter_declarations_report.py | build_parser | b8dc87bf6311782a38587771bb917fe395765185fd80126fd0197c9764e5cfc3
```

## Step 1: Scaffold the generator, its Keccak core and the committed specification

**Goal.** Land the directory layout, the Elenchus runner, the stdlib Keccak-256
core with pinned vectors, and committed copies of the study and runbook.
**Entry.** The run branch at `e9e95b891b3ae642516e017c46b97a18a1480164`, with
the untracked runner `tests/emit_emitter_declarations_report.py` at the digest
registered above.
**Exit.** The root suite, the prose lint and the Phylax lint all exit 0.

```sh
python3 scripts/run_checks.py --base fiat/1361-emitter-versus-declaration-check-at-a-pinne --scope root --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/emitter-declaration-check-study.md docs/emitter-declaration-check-runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
```

**Files.** `scripts/emitter_declarations.py` (module skeleton, argument
parser with `build` and `check` subcommands that refuse with exit 2 until
Step 2, and the Keccak-256 function), `tests/test_emitter_declarations.py`,
`tests/emit_emitter_declarations_report.py`,
`docs/emitter-declaration-check-study.md`,
`docs/emitter-declaration-check-runbook.md`, `.horos/census.json`,
`.horos/boundary.json` where a scan moves them, and `tests/check-map-v1.json`
only if the plan names an unowned path.
**Tests.** Elenchus command: `python3 tests/emit_emitter_declarations_report.py {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`
Keccak-256 vectors for the empty input and the ERC-20
`Transfer(address,address,uint256)` signature, and a test that the committed
study and runbook copies exist. About 4 tests.
**Disciplines.** phylax: none beyond the lint, this step reads no external
input. ephoros: none, nothing runs unattended. metron: none, no performance
claim. elenchus: none, no failure in hand. hypomnema: the committed study and
runbook copies are the step's record.

## Step 2: Build the scanner, the ABI cross-check and the check command

**Goal.** Implement `build` and `check`: digest-verified source reads from a
clone or HTTPS, emitter and declaration parsing, the source and ABI
comparisons, the mismatch classes, and atomic JSON and Markdown output.
**Entry.** Step 1's pushed head.
**Exit.** The root suite and the Phylax lint exit 0, and the five seeded
specimen classes each fail for their named reason inside the root suite.

```sh
python3 scripts/run_checks.py --base fiat/1361-emitter-versus-declaration-check-at-a-pinne --scope root --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
```

**Files.** `scripts/emitter_declarations.py`,
`tests/test_emitter_declarations.py`, and the Horos scans where they move.
**Tests.** Elenchus command: `python3 tests/emit_emitter_declarations_report.py {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`
Offline synthetic Solidity fixtures written inside the test, never target
source: one clean emitter and declaration pair; the five specimen classes from
the study (changed topic0 literal, dropped topic, swapped indexed topics,
short data region, declaration marked `anonymous`); an emitter body with zero
or two `logN` sites recorded as unreviewed; a size or digest mismatch
refusing with exit 1; a redirect off `raw.githubusercontent.com` refusing; the
fixed `git show` argv; `check` writing nothing and exiting 1 on a byte
difference; a mismatch row written, not dropped, by `build`. About 20 tests.
**Disciplines.** phylax: this step opens the HTTPS fetch, the clone read and
the untrusted Solidity text boundaries named in study section 9. ephoros:
none, the command is run by a person or a step exit and reports on stderr.
metron: the 10 s `check` budget and 5 s test budget from study section 10
apply to this step's code. elenchus: any failure the specimens surface is
worked to its cause with a guard. hypomnema: the table schema
`wildcat.emitter-declarations.v1` is fixed here and documented in Step 3.

## Step 3: Commit the table at the pin and demonstrate the check

**Goal.** Generate and commit `docs/kickoff/1361/emitters.json` and its
rendered `docs/kickoff/1361/emitters.md` at
`f5a26146987926f4811b72a795d662813dedfe85`, then run the demo path from the
study.
**Entry.** Step 2's pushed head.
**Exit.** The root suite, the prose lint and the Phylax lint exit 0; the
demo observations named under Tests are recorded in the step's pull request
body.

```sh
python3 scripts/run_checks.py --base fiat/1361-emitter-versus-declaration-check-at-a-pinne --scope root --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/kickoff/1361/emitters.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
```

**Files.** `docs/kickoff/1361/emitters.json`,
`docs/kickoff/1361/emitters.md`, `tests/test_emitter_declarations.py`,
`scripts/emitter_declarations.py` only for a defect the table exposes, and
the Horos scans.
**Tests.** Elenchus command: `python3 tests/emit_emitter_declarations_report.py {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`
Offline tests that the committed Markdown is byte-equal to its rendering from
the committed JSON, that the JSON names the pin, the tag and both verification
input digests, that every emitter appears in a row or in the unreviewed list,
and that no `v2-protocol` source file is tracked. Demo, run against a local
clone and recorded but not part of the offline suite: `check` at the pin
exits 0; `check --ref bea503c2736d47de7fd34130c64f10783dc35b39` exits 1 and
names the moved source digests. The design conformance resolver
`.hexaemeron/design/resolve_conformance.py` writes the
`committed-table-regenerates` report before the final merge-step. About 5
tests.
**Disciplines.** phylax: the demo reads a clone and HTTPS under Step 2's
controls, no new boundary. ephoros: none, nothing runs unattended. metron: the
demo times `check` against the 10 s budget. elenchus: a row that disagrees
with the study probe is worked to its cause, never edited by hand. hypomnema:
`emitters.md` records where the table lives, its schema and what it does not
establish, including that runtime fidelity belongs to the #1601 differential.
