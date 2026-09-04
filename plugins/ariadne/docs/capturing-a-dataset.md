# Capturing a dataset release

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
<!-- marketplace-context:end -->

`capture-dataset` reads a release directory that already exists and writes a
statement of type `https://ariadne.wildcat.finance/dataset/v1`. It runs no
producer, reaches no network, and guesses nothing.

```bash
python3 scripts/ariadne.py capture-dataset \
  --release tests/fixtures/dataset-release/v2 \
  --name aave-v4-credit-events-v2 \
  --coverage-dimension block \
  --coverage-start 11370000 --coverage-end 15000000 \
  --gap 'start=12000000,end=12000100,reason=the archive node returned no receipts here' \
  --input 'name=aave-v4 capture,locator=alexandria://aave-v4/2024-01,file=<path>' \
  --producer-tool tabularium --producer-version 0.3.0 \
  --producer-command python3 --producer-command scripts/tabularium.py \
  --parameter venue=aave-v4 \
  --record-count mapping.json=1 \
  --previous tests/fixtures/dataset-release/v1 \
  --previous-name aave-v4-credit-events-v1 \
  --out release.json
```

## What it reads from the files

Every file under `--release`, sorted, digested with a streaming read so a large
release never lands in memory whole. Nested directories are walked and their files
are captured.

Nothing is skipped quietly. A symlink to a file is refused, because it reads fine
and its digest would describe something the release does not contain. A symlink to
a directory is refused too, and for a sharper reason: the walk does not descend
one, so leaving it in place would drop everything under it from both the statement
and the release digest with nothing recording that anything had been dropped. A
`.git` or `__pycache__` directory inside the release is refused the same way,
naming what to remove.

Record counts come from the file for `.jsonl` and `.ndjson`, where one record per
line is the format rather than an assumption. A final line with no trailing
newline still counts.

## What you have to tell it

Four things the files cannot answer. None of them has a default, because a default
here is a value nobody supplied sitting in a field a gate reads as evidence.

**Coverage.** `--coverage-dimension`, `--coverage-start` and `--coverage-end` are
required. A directory of records does not say which interval it was meant to
describe, so it cannot say where it falls short of one. Bounds are whole numbers:
block heights are integers, timestamps are not necessarily, and comparing across
the two is how an interval check comes to pass on values it never really ordered.

**Gaps.** `--gap start=<n>,end=<n>,reason=<why>`, repeated. A gap must sit inside
the bounds and carry a reason, and two gaps must not overlap. Passing none writes
`"gaps": []`, which is a claim that you looked: the predicate refuses an absent
`gaps` key precisely so that an interval with no gaps cannot read as complete by
accident.

**Inputs.** `--input name=<n>,locator=<l>` with either `file=<path>` to digest, or
`disposition=<state>,reason=<why>` when the input cannot be digested. A locator on
its own is refused, because it records nothing about what was read or whether it
could be read at all. `disposition=passed` is refused too: an input that was read
has a digest, and `passed` without one was a single word that got around the check.
The dispositions this field accepts are `failed`, `skipped`, `timed_out` and
`redacted`. Passing no inputs writes an empty array, which says the question was
asked.

**Record counts for anything that is not line-delimited.**
`--record-count <path>=<n>`. A file whose count is neither derivable nor stated is
refused:

```text
capture failed: mapping.json is not line-delimited JSON, so its record count
cannot be derived; state it with --record-count mapping.json=<n>
```

That refusal is the design. A count read off a filename records nothing about the
file.

**The producer.** `--producer-tool`, `--producer-version` and `--producer-command`
are all required. Ariadne read this release; it did not produce it, and gate 2
reads the producer block as the thing that made the files. An earlier draft
defaulted these to `ariadne`, `unstated` and `["ariadne", "capture-dataset"]`, and
gate 2 passed on that: a statement asserting a recoverable environment while
recording nothing recoverable. `--parameter key=value` is optional and feeds
`parameters_digest`, which is a digest over the canonical form of whatever was
passed, so the same parameters in a different order give the same digest.

A `--record-count` naming a file the release does not hold is refused too, so a
typo does not leave the count you thought you gave out of the statement.

## Comparing against a previous release

`--previous` with `--previous-name` identifies both sides. Each side's digest is
over the whole release rather than one file, because with several files picking
one would name an artefact the comparison is only partly about.

No record-level difference is written. Telling which records changed between two
releases needs a record identity this capture does not have, so the statement
carries a skipped claim saying exactly that. Fill `deltas.records` in by hand if
you have a record identity, and the gates will hold you to naming both sides of
every change.

Without `--previous`, `--first-release-reason` is required. It becomes the reason
beside a null baseline, because an absent `deltas` block reads as nothing having
changed rather than as there being nothing to change from.

## Writing the output

`--out` writes through a temporary file in the same directory and replaces the
target, so a run that dies partway leaves neither a truncated statement nor a
stray temporary file. Without `--out` the statement goes to standard output.

## Checking the result

```bash
python3 scripts/ariadne.py verify release.json
```

Seven numbered gates and three checks, and no line saying a gate went unchecked.
Exit 0 when every one holds, 1 when any does not.
