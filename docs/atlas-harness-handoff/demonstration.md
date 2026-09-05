# Demonstration: the harness record end to end

This is the run record for step 5 of the Atlas hand-off delivery. It re-runs the
documented demo path on this host, states the exit code observed at each
position, and reads the manifest's recorded block back off every surface
generated from it.

Host `darwin-arm64`, the interpreter pinned in `.python-version`, reportlab
5.0.1. Entry state `8851ea80b59631cfafcdd3c8bbbb979ebe3bba79`, which is step 4's
audit head and the ref the probe recorded against.

## The four commands, as the step lists them

```bash
python3 scripts/probe_harnesses.py --out docs/harness-classification.json
python3 scripts/render_harness_roster.py --check
python3 scripts/build_contributor_guide.py
python3 -m unittest tests.test_harness_manifest -v
```

| Position | Command | Exit observed |
| --- | --- | --- |
| 1 | `probe_harnesses.py --out docs/harness-classification.json` | 0 |
| 2 | `render_harness_roster.py --check` | **1** |
| 3 | `build_contributor_guide.py` | 0 |
| 4 | `python3 -m unittest tests.test_harness_manifest -v` | **1** |

**The sequence does not run green as written.** This is a finding about the
step's own Exit list, not a defect in the scripts, and it is recorded here
rather than reordered silently.

Position 2 failed with three drifted surfaces:

```
render_harness_roster: README.md: the roster region does not match the manifest
render_harness_roster: docs/how-to-help-shoggoth.md: the roster region does not match the manifest
render_harness_roster: docs/pdf/how-to-help-shoggoth.pdf: the harness page does not show 'MANUAL ONLY - PROBED DARWIN-ARM64, 2026-09-05'
render_harness_roster: 3 surface(s) drifted from the manifest
```

The cause is ordering. `--check` never writes; the only command that writes the
README and guide surfaces is the renderer in its default mode, and the list does
not contain it. So position 1 rewrites the manifest, and position 2 then
compares surfaces still generated from the previous one.

Position 4 failed with 7 failures of 95. Six are the same cause: they name
`README.md` and `docs/how-to-help-shoggoth.md` as no longer matching the
manifest. The PDF is absent from those six because position 3 had just rebuilt
it, which is the one thing the listed order does put in the right place. The
seventh failure is a separate defect the re-probe exposed, recorded below.

## The order that works

Adding the renderer's write mode between the probe and the check runs green at
every position:

```bash
python3 scripts/probe_harnesses.py --out docs/harness-classification.json
python3 scripts/render_harness_roster.py          # the write the Exit list omits
python3 scripts/render_harness_roster.py --check
python3 scripts/build_contributor_guide.py
python3 -m unittest tests.test_harness_manifest -v
```

| Position | Exit | Output |
| --- | --- | --- |
| 1 | 0 | `wrote 6 harnesses to docs/harness-classification.json` |
| 2 | 0 | `rendered 6 harnesses into three surfaces` |
| 3 | 0 | `three surfaces match 6 recorded harnesses` |
| 4 | 0 | `wrote docs/pdf/how-to-help-shoggoth.pdf (2702681 bytes, reportlab 5.0.1)` |
| 5 | 0 | `Ran 95 tests` / `OK` |

A second `--check` after position 4 also exits 0, so rebuilding the PDF on top
of the renderer's own build leaves the page saying what the manifest says.

## What the re-probe moved

The probe was run twice: once to a scratch path outside the tree, and once to
the committed path. Both produced identical bytes, so the probe is deterministic
on this host.

Against the manifest that shipped from step 3:

| Field | Shipped | This run | |
| --- | --- | --- | --- |
| `recorded.host` | `darwin-arm64` | `darwin-arm64` | same |
| `recorded.date` | `2026-09-04` | `2026-09-05` | moved |
| `recorded.base_ref` | `c0524f0cd1288cc35316ae9acec6c7d2a6bd4272` | `8851ea80b59631cfafcdd3c8bbbb979ebe3bba79` | moved |
| 59 per-harness fields across 6 entries | — | — | **0 differences** |

Entry order is identical, every `name`, `classification`, `client_present`,
`client_version`, `version_read`, `auth_configured`, `launcher_contract`,
`blocker`, `testable_here` and `probe` is unchanged, and the schema is still
`harness-classification/v1`. Manifest digest moved
`a1f6b224…` to `d03ba6f0…`; the PDF moved `a6b87be1…` to `f992873b…` at an
unchanged 2,702,681 bytes.

**Nothing the probe observed changed. Only the metadata describing when and
where it observed it changed** — and that alone rewrote both Markdown surfaces
and a 2.7 MB PDF.

That churn is a filed defect,
[skills#1247](https://github.com/wildcat-finance/skills/issues/1247), not
something this step repairs. `recorded` reaches all three surfaces through
`_provenance` (`scripts/render_harness_roster.py:733`), `readme_block` (766),
`guide_block` (793) and `pdf_label` (828), and `base_ref` defaults to
`git rev-parse HEAD`, so it moves on every commit. Nothing here decouples those
surfaces or changes the comparison semantics.

One consequence is worth stating plainly, because it looks like a fault and is
not: the committed manifest records the ref it was probed against, which is the
parent of the commit carrying it, so `recorded.base_ref` always lags `HEAD` by
at least one commit. The entry state was green in exactly that condition, with
`base_ref` at `c0524f0c…` and `HEAD` at `8851ea80…`. No check compares the two.

## The six verdicts

Every entry was written from an observed probe result. No client answered on
this host.

| Harness | Class | Probe command | Client found | Version read | Authenticated |
| --- | --- | --- | --- | --- | --- |
| GitHub Copilot | manual route | `copilot --version` | no | no | no |
| Cursor | manual route | `cursor-agent --version` | no | no | no |
| Gemini CLI | manual route | `gemini --version` | no | no | no |
| Windsurf | manual route | `windsurf --version` | no | no | no |
| Cline | manual route | `cline --version` | no | no | no |
| Roo Code | unsupported | none declared | no | no | no |

`testable_here` is `false` for all six.

## The five named blockers

Acceptance conditions 2, 3 and 4 asked for authenticated read-only client runs
of five harnesses. None of the five can be run on this host. Roo Code is the
sixth verdict rather than a sixth blocker: it is sunset, so there is nothing to
authenticate.

1. **GitHub Copilot.** `copilot` did not resolve on `PATH`, so the command was
   not run. No declared authentication signal on this host. No Copilot seat is
   held on the active account and the organisation's Copilot CLI policy is
   unconfigured. Seat entitlement is a network fact this probe does not read;
   clearing this needs either an organisation policy change or a new personal
   plan.
2. **Cursor.** `cursor-agent` did not resolve on `PATH`. No declared
   authentication signal. Authentication is an interactive account sign-in, and
   this environment has no Cursor account.
3. **Gemini CLI.** `gemini` did not resolve on `PATH`. No declared
   authentication signal, and no authentication method is configured here.
4. **Windsurf.** `windsurf` did not resolve on `PATH`. No declared
   authentication signal. The product the issue names is now published as
   Cascade inside Devin Desktop, so which product a Windsurf row should describe
   is a naming question a maintainer has to settle before any run.
5. **Cline.** `cline` did not resolve on `PATH`. No declared authentication
   signal, and the client is unauthenticated. Its positional-prompt form still
   defaults to act mode with auto-approval on, so the recorded hazard is
   unchanged.

The sixth entry, **Roo Code**, declares no client binary, so no client run was
attempted. The product is sunset and its repository archived, and no active
successor was named.

Both boundaries the issue forbids — an organisation policy change and a new
account — are the only things that would clear blockers 1 through 5. The run
therefore delivers the record and the machinery, and records five named
blockers instead of five passes.

## Signals read back

The study records two questions the manifest has to answer once it is serving
generated prose. Both were read back on this run.

**"Is the roster the site is showing still true?"** The manifest carries the
host, date and base ref of the run that wrote it, and `--check` is the signal
that fires when a surface stops matching. This run exercised that signal for
real rather than describing it: at position 2 of the list as written, `--check`
exited 1 and named all three drifted surfaces and the exact label the PDF failed
to show. After the write, it exits 0 with `three surfaces match 6 recorded
harnesses`. The check is wired into the repository suite as
`harness-roster-check`, so a drifted roster fails a normal run.

The recorded triple reaches every surface:

| Surface | What it shows |
| --- | --- |
| manifest | `host darwin-arm64`, `date 2026-09-05`, `base_ref 8851ea80…` |
| README provenance | `recorded on darwin-arm64 on 2026-09-05 against 8851ea80…` |
| README sentence | `A probe on darwin-arm64 recorded every harness below on 2026-09-05` |
| guide provenance | `recorded on darwin-arm64 on 2026-09-05 against 8851ea80…` |
| PDF roster card | `Manual only - probed darwin-arm64, 2026-09-05` |

**"Why did this harness get the class it got?"** Every entry carries its probe
command, the observed result and its blocker. Copilot is `manual route` because
`copilot --version` was not run — the binary did not resolve on `PATH` — and
because the seat check and the organisation policy value both came back empty.
A reader gets those facts, not an adjective.

The structured probe log carries one `run_id` correlating
`probe_run_started`, six `harness_probe_done` events and the write event, so a
single run can be reconstructed from the log alone.

## Credential sweep

The probe spawns clients, so the sweep runs against real output. Result: **no
credential-shaped material in either file.**

Ten patterns were applied to the committed manifest (5,215 bytes) and the probe
log (2,197 bytes): GitHub `gh*_` tokens, `sk-` keys, AWS access key ids, Google
API keys, bearer headers, JWTs, PEM private key headers, assigned
secret/token/password values, absolute home paths, and hex runs of 32 characters
or more. Zero matches in both files. The only long hex strings present are the
probe's own `run_id` and the two git refs, which were allow-listed as known
non-secret values.

The Phylax boundary lint is clean at exit 0 over
`scripts/probe_harnesses.py`, `scripts/render_harness_roster.py`,
`scripts/build_contributor_guide.py` and `tests/test_harness_manifest.py`.

One caveat, stated so nobody reads more into the lint than it establishes:
Phylax analyses `.py`, `.ts`, `.tsx` and `requirements*.txt` only. Handing it
`docs/harness-classification.json` prints `clean` at exit 0 **without reading
the file**, so a JSON or log sweep through that tool would be vacuous. The
pattern sweep above is what actually covers the manifest and the log. The suite
also holds this independently: `CredentialTests` in
`tests/test_harness_manifest.py` feeds the probe a client output fixture
carrying a token and sweeps both the manifest and the log for it.

## The test the re-probe broke

`tests/test_harness_manifest.py:1777` held a positive control asserting that a
real date still renders, and it pinned the literal `2026-09-04` against the
landed manifest. The control's job is to show that the calendar guard refuses a
bad date rather than the field itself, so the specific date was never the point
— but pinning it made this the one case that no re-probe could ever pass.

The control now reads `recorded.date` off the landed manifest and parses it as a
calendar date before asserting it reaches the label. Parsing first keeps it
load-bearing, because `assertIn` on an empty string would pass vacuously. The
refusal loop over `2026-13-45`, `2026-02-31` and `0000-00-00` is unchanged, and
nothing about the compare semantics or the `stale-manifest` case was touched.

This was the only place a landed `recorded` value was pinned. Every other
`2026-09-04` in the module belongs to a synthetic fixture that builds its own
document.

## Proof

On the committed tree:

- `python3 scripts/render_harness_roster.py --check` — exit 0,
  `three surfaces match 6 recorded harnesses`
- `python3 -m unittest tests.test_harness_manifest -v` — exit 0, 95 tests, OK
- `python3 scripts/run_checks.py --full` — exit 0, 29 of 29 checks pass. It read
  28 of 29 when this document was written at `bc0d8b12`: `root-suite` was red on
  two cases carrying the ADR-078 collision described below, which `311c0a89`
  then cleared.

`.horos/boundary.json` needed one refresh, and not for the reason the PDF
suggested. The boundary records the PDF by byte count, and the rebuilt page is
2,702,681 bytes as before, so the PDF entry reproduced unchanged. Adding this
document to the tree is what moved the `counts` block, so the boundary was
regenerated with
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`.

## The red this step then cleared

`tests/test_decision_records.py` compares this branch's decision-record numbers
against the default branch. At `bc0d8b12`,
`docs/decisions/ADR-078-generate-the-harness-roster-from-one-probed-manifest.md`
collided with `ADR-078-echo-fiat-required-as-a-filer-set-label.md` on main, and
two cases failed on it: the collision case itself, and
`test_the_pinned_decision_record_tests_pass`, which runs the first one.

The collision was neither new work nor a regression from this step:

- The record was added at `183179ca`, step 3's audit head, and its message
  already reads "renumber the roster record to ADR-078 after a third collision".
- `run_checks.py --full` was green at 29 of 29 on the entry state, at
  `8851ea80…`, earlier in this same session.
- The local `origin/main` ref fast-forwarded to `5e2bb508` at 10:07:55, between
  that green run and this one. The comparison reads the local ref and does not
  fetch, so the collision appeared when main moved, not when this step committed.

`311c0a89` moved the record to ADR-079, checked free against `origin/main`,
whose numbered records run 074 to 078, and against every open pull request head.
Thirteen occurrences moved across five files, and no audit record references the
number. At that commit `tests.test_decision_records` is 5 of 5 at exit 0 and
`run_checks.py --full` is 29 of 29 at exit 0.

That was the fourth collision on this record, and three of the four landed while
the branch was waiting, so any number chosen now can collide again. The number is
rechecked immediately before the run is merged rather than only before this step
is pushed. ADR-079's own Numbering section states all four.
