# Issue 710 generator-aggregate proof

This document records the Step 3 reproduction for
[issue 710](https://github.com/wildcat-finance/skills/issues/710). It checks
the incident topology against the Step 2 controller without changing that
controller, its tests, its fixture, or its generated runtime.

## Evidence boundary

The incident is a deterministic reconstruction from reachable Git objects.
The original ignored revalidation artefact and checkpoint from the halted
issue 622 run were unavailable. This proof therefore does not claim to have
read those operator bytes, rerun their ten recorded commands, or recovered or
changed that run. The checked sources are the
[fixture](../plugins/hexaemeron/tests/fixtures/fiat-710-generator-aggregate.json),
the reachable commits it names, the
[focused controller tests](../plugins/hexaemeron/tests/test_hexctl_generator_aggregates.py),
and the Step 2 controller at the tip inherited by this step.

Every repository Python command used the interpreter fixed by
`.python-version`; it reported `Python 3.13.15`. The proof extraction first
asked the normalized receipt for `payload_total_bytes`, a value held only by
the source fixture. That lookup failed with `KeyError` before any tracked file
or controller record changed. Reading the normalized key set localised the
mistake, and the corrected extraction below uses only fields the receipt
actually retains.

## Fixed inputs

The delivery start and reconstructed incident base are the same commit, but
they are listed separately because they answer different provenance
questions.

| Input | Commit | Evidence use |
| --- | --- | --- |
| delivery starting commit | `bec742ac17a5fdd95f0242d2b7ba894828cebf22` | Fiat starting-base identity |
| reconstructed product merge | `6f9f800c79efed5642f73ca3e2a80786b12ce276` | product inventory and sync first parent |
| reconstructed base head | `bec742ac17a5fdd95f0242d2b7ba894828cebf22` | upstream inventory and sync second parent |
| product-first sync commit | `f0a84ca343b8d9ed477bc1cb4d0dd6a49bbe3897` | composition inventory and final aggregate tree |
| product/base merge base | `b245d68e7e8c9d07b0dbbaa67e57b05cd00b18ef` | product and upstream inventory origin |

Fresh object inspection returned `commit` for all four fixture commits, the
sync parents in product-first order, and the merge base above:

```text
f0a84ca343b8d9ed477bc1cb4d0dd6a49bbe3897 6f9f800c79efed5642f73ca3e2a80786b12ce276 bec742ac17a5fdd95f0242d2b7ba894828cebf22
b245d68e7e8c9d07b0dbbaa67e57b05cd00b18ef
```

The fresh fixture digest was:

```text
90ccba75f8a1b6e2404630df363419a50e6d5555086040cddc92615ef902649d  plugins/hexaemeron/tests/fixtures/fiat-710-generator-aggregate.json
```

## Recomputed surface and the version-1 refusal

The extraction imported the focused module, used its null-safe Git path
reader against the commits above, sorted each inventory, and asserted every
count and inventory digest against the fixture. It then called the controller
record builder for both schemas. The independently recomputed inventories
were:

| Inventory | Paths | SHA-256 of sorted newline-delimited paths |
| --- | ---: | --- |
| product | 53 | `79237b2bd07fc76b8de868f87a077545393b33bac97e49f175ad433f5b04fb0c` |
| upstream | 1,087 | `56e1dbd29e5f780977e3a3200c69c35e1ed7774a416843b5d3875af2920a356c` |
| overlap | 5 | `f9212e3b26a5729837ae3850967d43ec8a258fe18213960eb5cf34ad46e91086` |
| composition | 1,095 | `e9d5617e6db2fd91fab605517019a0172868b88abdf373453b83eaa11915c588` |
| required | 1,095 | `e9d5617e6db2fd91fab605517019a0172868b88abdf373453b83eaa11915c588` |
| aggregate-owned runtime | 887 | `d47d479b9d68e1095b833dc97da89b1eb4e57027eb0cc9ef3165ba7f7e1ef421` |
| individually listed outside | 208 | `8b3e8cf458fbf36ed46cab5d1d12e7e873fd788d7b0f67fa893fbae590b7457f` |

Passing all 1,095 required paths to the unchanged version-1 route produced
the exact established refusal:

```text
exit: 2
stderr: hexctl: error: integration path delta exceeds 500 paths
```

## Version-2 checked transition

The same Git objects passed through the registered version-2 route. There was
one selected aggregate. The normalized receipt retained:

```json
{
  "schema": "fiat-integration-revalidation/v2",
  "required_path_count": 1095,
  "aggregate_owned_path_count": 887,
  "individual_path_count": 208,
  "affected_aggregates": [
    {
      "id": "promise-machine-portable-runtime-v1",
      "prefix": ".agents/skills/promise-machine/runtime/",
      "generator": "scripts/portable_promise_machine.py",
      "manifest": "MANIFEST.json",
      "manifest_sha256": "7f03a24cf128b93c124d61a3cadbfec7368f0922931705d204845b2126e05ca6",
      "file_count": 887,
      "payload_file_count": 886,
      "tree_sha256": "f69ec4719fb73e4ce5620aa199b3e00aa4458b99228cb052f97cfc8e72152de3",
      "git_tree": "5b8cea1a952767e095ee16ab5800ae28993c2617",
      "total_bytes": 20161661
    }
  ],
  "coverage_ids": ["portable-runtime", "outside-surface"]
}
```

The transition test began with a local fixture state in `integrate`, called
`done sync-run` over the normalized record, called `done integrate`, and
asserted both `phase == "done"` and
`receipts.integrate.sync.revalidation.schema ==
"fiat-integration-revalidation/v2"`. Remote and GitHub boundaries were mocked;
this was a controller-transition demonstration, not an external merge. Its
fresh output was:

```text
fiat/710-fixture synced with main at bec742ac17a5fdd95f0242d2b7ba894828cebf22; product evidence preserved; 2 integration revalidation check(s) recorded; integration may continue
fiat/710-fixture merged into main (aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa); run complete
```

## Refusal and mutation-order checks

Each row changed one declaration or one outside-path relation. Every call
exited 2 with the exact diagnostic shown.

| Specimen | Refusal boundary | Diagnostic after `hexctl: error:` |
| --- | --- | --- |
| file count `887` to `886` | final-tree count | `generator aggregate promise-machine-portable-runtime-v1 file count does not match` |
| manifest SHA-256 to zero | final manifest bytes | `generator aggregate promise-machine-portable-runtime-v1 manifest digest does not match` |
| tree SHA-256 to zero | domain-separated tree digest | `generator aggregate promise-machine-portable-runtime-v1 tree digest does not match` |
| undeclared aggregate id | source registry | `affected_aggregates entry 0 names an unknown aggregate` |
| missing outside path | complete outside surface | `affected_paths omits the computed outside integration surface: tests/test_version_propagation.py` |
| aggregate-owned path declared outside | exact path classification | `affected_paths must contain only the exact outside integration surface` |

The live, ignored Fiat state and ledger were hashed before and after those six
validation calls. Both pairs were byte-identical. The state digest was
`3d56278948c864a6962a9d61a2afe72e62abe197766f98551141e197dad54570`;
the ledger digest was
`449bbef4236b51e86c83b6fcac48d28a23dd6761972f70dc64589741b54e5f31`.

## Version-1 compatibility

The focused compatibility case rebuilt the existing two-path version-1
fixture and compared the complete normalized mapping. The fresh artefact was
removed after the check. Its normalized receipt was:

```json
{
  "schema": "fiat-integration-revalidation/v1",
  "artifact": ".fiat-710-proof-v1.json",
  "sha256": "982860b6f44b6e41bb6a298ef03c05d2a88c4027ec9a61e76fb71e9460908b1a",
  "base_before": "4444444444444444444444444444444444444444",
  "base_after": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "product_paths": ["product.py", "shared.json"],
  "upstream_paths": ["shared.json", "upstream.py"],
  "overlap_paths": ["shared.json"],
  "composition_paths": ["shared.json", "upstream.py"],
  "affected_paths": ["shared.json", "upstream.py"],
  "checks": [
    {
      "id": "root-suite",
      "command": "python3 -m unittest discover -s tests",
      "paths": ["shared.json", "upstream.py"],
      "exit": 0
    }
  ]
}
```

The focused test asserts this whole mapping. The complete Hexaemeron suite
also exercises the existing version-1 lifecycle, supersession, frontier, and
receipt fixtures without migrating their bytes or schema.

## Fresh checks

The corrected focused command, with no import-root flag, ran 15 tests and
returned `OK`. The complete Hexaemeron runner used a fresh ignored report at
`.elenchus/fiat-710-step-3.json`; it ran 1,392 tests, returned `OK`, and
reported one skip. Its two fixture transition messages are reproduced above.

The first root-suite run in the live Fiat worktree ran 460 tests and had one
failure. The failing test recursively read two ignored controller prose files,
`.hexaemeron/steps/2/pr.md` and `.hexaemeron/task-issue-comment.md`, and treated
their historically accurate Step 2 `CPython 3.13.15` evidence as current
tracked prose. Neither file is part of this commit, and neither was edited.
The exact prescribed root command is therefore rerun on this exact tracked
tree in a clean detached worktree. That bounded run separates product bytes
from local controller evidence and returns 460 of 460 tests green.

The root runner printed a legacy `INOCULATION {...}` summary while executing
its unit tests. No inoculation command, checkpoint operation, archive action,
or recovery action ran. Checkpoint policy for this delivery remains `local
checkpointing only`.

On the exact tracked tree, these remaining gates return exit 0:

- byte comparison between `.hexaemeron/runbook.md` and the tracked runbook;
- Protasis on the tracked runbook;
- the portable-runtime check;
- Promise coverage and version-propagation tests through the root suite;
- audit-synopsis currency;
- Imprimatur on this proof and the tracked runbook;
- Brevitas reports for this proof and the tracked runbook;
- Phylax, Ephoros, and Hypomnema over their prescribed trees;
- Horos against the tracked reading boundary; and
- `git diff --check`.

The tracked runbook is an exact copy of the amended controller runbook, with
SHA-256
`c271da247301a97772f13fcba0b7299a728313d52c736de1713e68f7dbb1fa0b`.
[ADR-043](decisions/ADR-043-bind-sync-run-generator-aggregates.md) remains the
decision record; the fixture remains the incident preimage; this proof is the
durable reproduction record.
