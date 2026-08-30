## Step 1, round 1 -- 2026-08-30T05:49:37Z

Audit schema: fiat-audit-round/v2

Covered: stale-cost-figures=reviewed; guard-brittleness=reviewed; adr-supersession=reviewed; adr-number-collision=reviewed; install-prose-drift=reviewed; boundary-currency=reviewed

Not checked: whether `1_010` and `22_500_000` are the right headroom. The round establishes that the guard fires and names the recorded figure, not that those two bounds are correctly sized. Also not checked: the discovery claim the record rests on. That relocation breaks the skills.sh listing and the ref-less install is argued from reading the CLI's `source-parser.ts`, `add.ts`, `blob.ts` and `git.ts` and from the root `skills.sh.json`; no relocation was attempted and no install was driven against a moved payload, so the claim is a source reading rather than an observed failure.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | `tests/test_skills_sh_package.py` | The new module-level constant `AGENTS` pointed at `.agents/` in a module that separately reads files literally named `AGENTS.md` at four other points (lines 184, 199, 202 and 264). A reader grepping `AGENTS` got both, and the constant read as though it named one of those documents. | fixed in e1f13e6a73e5fd7fb819f9e92f872d3211c96de2 |

Leads not pursued: `RECORDED_TRACKED_FILES` and `RECORDED_TRACKED_BYTES` appear only in the failure messages and are never asserted, so the recorded figure can drift below the ceiling without the suite noticing; asserting them exactly was rejected in the study as brittle, because every ordinary plugin addition would then fail the guard, and the ceiling is what the study chose instead. The guard walks the filesystem rather than `git ls-files`, so an untracked file left under `.agents/` counts toward the ceiling; that is fail-closed, and a stray file in a generated tree is itself worth surfacing. `Path.is_file()` follows symlinks, so a symlink into a large file would inflate the byte total; the payload carries none, and `test_manifest_binds_every_runtime_file_to_source_bytes` and `test_no_manifested_runtime_file_is_gitignored` would both surface one. Evidence for three of the covered concerns: the figures were re-measured at the commit and returned 999 files and 21,789,732 bytes, matching both the record and the guard; `docs/decisions/ADR-054` is absent from `origin/main` at `7e97b5195d5b0e43146b4200f26cd41b89003413`, so the number is free at this cut; and `INSTALL.md` line 129 and `README.md` line 38 both carry `npx skills add wildcat-finance/skills --skill promise-machine`, which is the form the CLI resolves as a `github` source. The three lints exit 0 and the runner contract reports 737 of 737.
