# Reconciliation journal binding, issue #1887

## Preserved archives

The [recomputation record](wildcat-recomputation.json), produced on 2026-09-25,
checks both archives and every unpacked file against the committed staging
manifests before recomputing the reconcile checkpoint digest. No RPC request
was made and no preserved input was changed.

- Wildcat V1: all 107 files and 103 journals match their manifest. The recomputed
  `staging_sha256` equals the preserved checkpoint's
  `db54adc0d58ae3341689194e695370c106fca7a09fe6208c85923e563b112634`.
- Wildcat V2: all 125 files and 121 journals match their manifest. The checkpoint
  has no `staging_sha256` field. Recomputing yields
  `0560d4c6fdf29346c3b857a4d1416b46a4ddba74dcce0547f36b705eeaf39741`,
  but no preserved digest exists to compare it with. Whether these are the
  journal bytes originally reconciled remains unknown.

The complete offline build and verification also reproduced the original
Wildcat V1, Wildcat V2 and Compound release identifiers. Their reconciliation
records remain unchanged and `check` reports the absent journal binding:

- V1: `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`.
- V2: `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`.
- Compound: `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`.

## Recompute

The digest is SHA-256 over the canonical committed collect state followed by
canonical objects containing each journal's name, byte count and SHA-256,
ordered by name. This is the formula used by
`Reconciler._committed_input_digest`. It detects accidental change. A writer
able to replace the checkpoint can replace its digest too.

Rerun from the repository root, supplying both preserved archives and their
unpacked staging trees:

```bash
python3 plugins/alexandria/docs/reconciliation-binding/recompute.py \
  --v1-staging "$ALEXANDRIA_WILDCAT_V1_STAGING" --v1-archive /path/to/v1.tar.zst \
  --v2-staging "$ALEXANDRIA_WILDCAT_V2_STAGING" --v2-archive /path/to/v2.tar.zst
```

The command reads local files and prints one record. An absent checkpoint
digest is reported as `absent`; a mismatch exits 1. Neither outcome rewrites
the historical evidence.

## Regression

The regression suite changes `abab` to `abac` after reconciliation without
changing the journal length, for whole and split journals. It also repackages
the changed logs into a digest-valid release. On parent
`dc837a458503877bc029d740398fbe2c37ed922d`, both tests fail because `build` and
`check` accept the edits. With the fix, both refuse by journal name. Run them
from `plugins/alexandria` with
`python3 -m unittest tests.test_reconciliation_binding -v`.
