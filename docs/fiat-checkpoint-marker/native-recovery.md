# Native checkpoint recovery for issue 1755

The selected native resolver passed on 2026-09-19: 37 controller commands, two signed round trips, 21 isolated refusal cases and two tampered-carrier refusals. The prepared package is Hexaemeron 1.6.61; Fiat remains 6.68.1.

## Observed boundary

The [conformance report](reports/bounded-material-native-archive-roundtrip.json) has SHA-256 `6bcc8ec6d64b3228d333cae8c16e2de45320a3a2db8e0090cd2d633ab16ef740`. Its [observation](reports/bounded-material-native-archive-roundtrip.observation.json) has SHA-256 `2dd3f4de73d35a65b1f57e19ea0b8c6781174adf048a7c3a4293876656556087` and binds the controller at commit `33f551f87a433c79c65ac5289d35d3be2eb67a9d`, its exact bytes and the working resolver, guards, fixture helpers and budget file.

OpenPGP and SSH each used a disposable key and native Git verification. Inspect and restore ran with the producer's key directory hidden and without fixture delivery tools. GitHub responses, producer ref observations and the pre-gate fixture lifecycle were simulated. This proves the recorded fixture, not a live service retry or signer ownership.

Both public CP3 files survived archive, inspection and restore. The source remained 376,713 bytes with SHA-256 `bce008b201071b1ded3e656e24c0bfabb67923932a2cb3a994cb260172d6709c`; the synopsis remained 378,244 bytes with SHA-256 `86bab9bce5db6b37a67527336bbfb1f65036a4f3ff504e50914be416be3934b2`. Native verify, status and next returned the same semantic continuation, disposable Step 2 implementation, without executing it or changing the restored state and ledger.

The 21 refusal cases cover seven armour labels, missing footers, truncation, numeric CRLF escapes, 1- and 8-glyph wrapping, PEM and PGP metadata, escaped solidi, a chunk crossing, repeated headers, four token patterns, stripped 16,384-bit geometry and JSON carriage. Each ran alone beside the benign public files, returned `secret-shaped-member`, published no ZIP or sidecar, and preserved state and ledger. A one-byte archive mutation for each signing format returned `outer-digest-mismatch`. Relabelled and geometry cases establish lexical shapes; only the corpus's seeded 3,072-bit RSA key has an arithmetic round-trip check.

| Measurement | OpenPGP | SSH | Existing limit |
| --- | ---: | ---: | ---: |
| Export interval, ms | 175 | 177 | 15000 |
| Inspect command, ms | 197 | 193 | 10000 |
| Restore command, ms | 396 | 397 | 20000 |
| Archive bytes | 797872 | 797639 | 201581002 |
| Expanded bytes | 793682 | 793439 | 209715200 |
| Export command peak RSS, bytes | 87293952 | 87556096 | 1073741824 |

Each format has one measured sample. These small fixtures are not comparable to the historical budget workload and establish no production latency. Commands have a 120-second timeout and a 2 MiB combined output cap. Reports retain identifiers, counts, hashes, exits and limits; payloads and signing keys stay in memory or disposable directories.

## Reproduce

Use this checkout's Python pin, 3.14.6, from the repository root. Choose a fresh report path; the writer refuses an existing report or observation.

```sh
python3 plugins/hexaemeron/tests/prove_checkpoint_marker_scan.py --candidate bounded-material --criterion native-archive-roundtrip --report .hexaemeron/reports/replay-native-archive-roundtrip.json
python3 -m unittest plugins.hexaemeron.tests.test_checkpoint_marker_scan -v
```

The marker suite passed 14 tests. Its new CLI test produced one assertion failure and zero errors against the Step 2 resolver; [the parent comparison](reports/step-3-native-parent-guard.json) preserves that bounded overlay. It is not a complete parent-suite run or an Elenchus classification. The older implementation and selection reports retain their original bytes and historical status. New implementation-resolver output states only that its separate operation did not run the native demonstration.

## Recovery handoff

Publication, installation and the installed-controller refresh remain integration work. After the released plugin is installed through the host's supported route, start a new chat, resolve Fiat from that installation and verify the preserved service run before retrying its checkpoint. Keep the service's saved refusal and original state/ledger evidence. Never replace its controller with this repository's controller or treat this fixture report as a service implementation receipt.

Issue 1676 still owns service admission, issue 1756 owns native Codex currency observation, and the saved service checkpoint still needs its separately recorded retry. Signing-key diagnostics, destination custody and concurrency remain with issues 1647, 1648 and 1649. This Step 3 demonstration completes none of those operations.

The coordinating agent rechecked the saved service tree at approximately 21:12 UTC on 2026-09-19. The [service handoff](reports/service-retry-handoff.json) preserves its exact worktree, HEAD, raw state and ledger digests, 19-entry ledger tail, retry-record path and digests. Its two Hexaemeron 1.6.59 archive attempts exited 1 with `secret-shaped-member` and published no archive. These are that agent's historical observations; this worker did not inspect the service tree.

After installation and the mandatory new chat, resolve `FIAT_SKILL_DIR` from the newly active Fiat instruction file. Compare the original HEAD and raw files with the handoff before running the installed controller:

```sh
service_worktree=/home/kethcode/scratch/fiat-checkpoints/tmp/fiat/fiat-1-authenticated-checkpoint-intake-and-isolated-v
git -C "$service_worktree" rev-parse HEAD
sha256sum "$service_worktree/.hexaemeron/state.json" "$service_worktree/.hexaemeron/ledger.jsonl"
python3 "$FIAT_SKILL_DIR/scripts/hexctl.py" --dir "$service_worktree" verify
python3 "$FIAT_SKILL_DIR/scripts/hexctl.py" --dir "$service_worktree" status --json
python3 "$FIAT_SKILL_DIR/scripts/hexctl.py" --dir "$service_worktree" checkpoint archive
```

Stop on a digest disagreement or failed verification and preserve the refusal. On archive success, inspect the returned archive with its returned outer SHA-256 and retain the new result beside the saved attempts. A successful checkpoint still does not admit service Step 2; issue 1676 owns that transition.
