# Checkpoint marker selection evidence

This directory preserves the measured design for issue 1755 at Git commit
`e2307ed5966e18727434b3e49bec89db736f7b17`. The exact study and amended runbook
are `docs/fiat-checkpoint-marker-study.md` and `docs/fiat-checkpoint-marker-runbook.md`.
Step 1 records the policy and evidence; product repair, parent guards and the
native archive demonstration are later work.

## Recorded evidence

| Candidate | Missed refusals / 436 | Benign refusals / 119 | Median ceiling, ms | Traced peak, bytes |
| --- | --- | --- | --- | --- |
| footer-proximity | 117 | 114 | 92 | 155656 |
| whole-lines-only | 231 | 0 | 77 | 159103 |
| bounded-material | 0 | 0 | 196 | 173277 |
| complete-decoder | 229 | 0 | 60 | 158877 |

The checked `unique-frontier` rule selects `bounded-material`. Its measured
cost was 104 ms and 17,621 traced bytes above the released predicate on the
2,852,105-byte workload. Timing is the ceiling of the median of five sequential
samples. Allocation excludes the prebuilt corpus and imported modules and does
not measure process RSS. These are pure-scanner observations on one recorded
host; no native archive ran during selection.

- `design-evidence.json` preserves all four candidates, 24 resolved selection
  cells, eight pending conformance cells and the exact selected candidate.
  Its relative `reports/` paths still resolve to the original report bytes.
- Each selection report has its original `.observation.json` companion with
  counts, mismatches, source digests and, for timing, all five raw samples.
  The workload is 1 MiB of filler, approximately 1 MiB of repeated headers and
  the two unchanged public files. All four candidates passed four token probes
  and the deterministic input-preservation check.
- `reports/boundary-observations.json` retains ten recorded probes, their input
  byte counts and digests, and the released and selected booleans. The cases
  cover 15/16 glyphs, 256/257 metadata bytes, seven/eight metadata lines,
  1,791/1,792-byte body starts, stripped 16,384-bit geometry and a conservative
  false positive. The original ad hoc construction command was not retained;
  these records alone do not reconstruct the exact probe inputs. Step 2 owes
  executable guards on both sides of every declared bound.
- `reports/measurement-environment.json` records the measured interpreter (`3.14.6`), host,
  measurement method, source commit and controller/script digests. The exact
  measurement source is `docs/fiat-checkpoint-marker-measure-design.py`.
  `provenance.json` maps each copied file to its original path, byte count and
  SHA-256 and identifies the controller and fixture helpers at the starting tree.
- The retained audit-currency, study-check and prose reports record the checks
  performed during preparation. Audit currency covered 95 sources; it does not
  establish that every audit was read. The runbook's first failed interface check,
  corrected check and amendment prose records remain visible. Their original
  absolute paths are historical provenance, not commands to run on another host.

The corpus exercised one seeded 3,072-bit RSA key with an arithmetic round trip.
Relabelled RSA bytes establish lexical behaviour under seven private-key labels;
they do not establish valid EC, DSA, SSH or PGP key structure. Geometry fixtures
likewise establish encoded shape only. Reports contain case identifiers,
counts and digests; generated key material stays in memory or disposable fixtures.

## Replay selection

Replay the 555 selection specimens and 24 cells in a disposable checkout at the
exact starting commit, using the interpreter named by that checkout's
`.python-version` as `python3` (recorded version `3.14.6`). Run these commands
from the delivery checkout that holds this directory:

```sh
marker_source_tree=$(pwd)
marker_replay_home=$(mktemp -d)
git worktree add --detach "$marker_replay_home/baseline" e2307ed5966e18727434b3e49bec89db736f7b17
mkdir -p "$marker_replay_home/baseline/.hexaemeron/reports"
cp "$marker_source_tree/docs/fiat-checkpoint-marker-measure-design.py" "$marker_replay_home/baseline/.hexaemeron/measure_design.py"
cd "$marker_replay_home/baseline"
python3 --version
for candidate in footer-proximity whole-lines-only bounded-material complete-decoder; do
  for criterion in material-refusals benign-acceptance scan-time peak-allocation token-parity input-preservation; do
    python3 .hexaemeron/measure_design.py --candidate "$candidate" --criterion "$criterion" --report ".hexaemeron/reports/replay-$candidate-$criterion.json"
  done
done
```

The source imports that checkout's controller and test helpers. In particular,
`footer-proximity` points at the imported controller predicate. Running it
against repaired code cannot reproduce the released baseline. Keep replay
reports separate from preserved reports: fresh timing and allocation values may
differ, and their report digests will differ when the command path changes.
The reproduction source constructs synthetic markers in code; no saved private
key payload or literal paired-marker example is needed.

## Validation and pending gates

From the delivery checkout, validate the preserved selection and its decision
home with the same supported interpreter:

```sh
python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py docs/fiat-checkpoint-marker/design-evidence.json --transition design-lock
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study docs/fiat-checkpoint-marker-study.md --design-evidence docs/fiat-checkpoint-marker/design-evidence.json --repo-root .
```

The selected `implementation-regression` cell blocks `step:3`; the selected
`native-archive-roundtrip` cell blocks `integration`. Their exact resolver
commands and future report paths remain in the unchanged design record. No
pending cell is a completed test. Product conformance must compare the repaired
predicate with the released baseline in the same run, on this workload, with
five samples each: median at most four times baseline and traced peak below
1,048,576 bytes. The signed disposable demonstration must distinguish native
cryptographic verification from simulated GitHub/ref observations.

The dated amendment in `docs/fiat-checkpoint-archive-study.md` replaces the
footer-only policy before implementation. The public CP3 source and synopsis
remain at their original paths and digests, recorded in `provenance.json`.
Service Step 2 remains blocked on issue 1676. The released plugin, installation
and new-chat refresh precede a separately recorded retry of that saved service
checkpoint; this evidence completes none of those operations.

## Step 3 native recovery evidence

The 2026-09-19 [native recovery demonstration](native-recovery.md) completes the selected native conformance operation with two signed round trips, 21 isolated refusal cases and two tampered-carrier refusals. Its new reports preserve the native/simulated boundary, restored public-file digests, semantic continuation and six budget observations. Earlier selection and implementation reports remain historical records with their original bytes. The service retry and admission remain pending under the recovery handoff.
