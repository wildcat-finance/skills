# Wildcat timestamp specification

## Source bundle

This bundle preserves the #1997 study, runbook, selected design and eighteen
selection reports. `source-pins.json` binds the original and public bytes. The
public study appends one design bridge; its original prefix remains exact.
The controller documents remain local and unchanged.

## Selection evidence

The proposal model in `design_probe.py` is selection evidence only. It models
deduplication and exact joins; it does not execute the production collector or
consumer. Its reports retain their original command identities. To reproduce
them from the pinned starting tree, stage the model and `candidate-specs.json`
under `.hexaemeron/` in a fresh worktree and execute each selection report's
command. The model source assertions describe the starting tree, so later
product changes can invalidate that reproduction.

## Scaffold and limits

```sh
python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case scaffold --report .hexaemeron/steps/1/scaffold.json
```

Production timestamp cases remain unavailable at Step 1. The scaffold runs
report controls and constructed legacy V1/V2 verification. A passing scaffold
does not establish capture, mapping, dossier propagation or design conformance.
The integration resolver must execute the completed demonstration before it
emits the selected `collector-journal` / `timestamp-demo` design report,
separately from its unittest counters.

No private release payload, local custody path or provider credential is in
this bundle. Historical release counts are observations in the study; this
scaffold does not re-run the retained private releases or Lazarus fixtures.
