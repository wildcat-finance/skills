## Step 1, round 1 -- 2026-08-30T06:34:53Z

Audit schema: fiat-audit-round/v2

Covered: generator-output-escape=reviewed; suite-coverage-loss=reviewed; authored-file-loss=reviewed; publish-unverified=not-applicable; stale-destination=not-applicable; workflow-drift=not-applicable; token-scope=not-applicable; broken-install-window=not-applicable

Not checked: the five not-applicable concerns all sit on the destination repository and its scheduled job, which step 2 builds. Nothing in this step publishes, schedules or holds a token. Also not checked: whether a package this generator writes installs through the skills CLI. The generated tree verifies itself offline here; no `npx skills add` was run against a published repository, and step 2 owns that proof.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `scripts/portable_promise_machine.py` | `package --out` called `shutil.rmtree` on whatever stood at the destination before writing, so naming a populated directory destroyed its contents and exited 0. Driven against a throwaway tree holding one file: the file was gone and the command reported success. The four refusals already driven covered paths that should be rejected, not a directory that should be left alone, and the phylax lint exited 0 on the file both before and after. | fixed and guarded in 69b3180c850d3ddd09ccfaf547b53951f6b13dd9 |
| S1-R1-02 | low | `scripts/portable_promise_machine.py` | `_checked_output` carried `parent.resolve() != parent`, comparing an already-resolved path against its own resolution. The branch could never be taken, and it read as a symlink guard that was not one. | removed in the same commit |

Leads not pursued: the marker test treats any directory carrying `.agents/skills/promise-machine/runtime/MANIFEST.json` as one this generator wrote, so a directory a person assembled with that path inside it would still be cleared; the manifest is a generated artefact nobody writes by hand, and the alternative is a sentinel file that adds a path with no other purpose. `_package_bytes` reads every source into memory before writing, holding about 21 MB at once; that is bounded by the payload the generator already builds the same way in `expected_files`, and no caller streams it. The generated `README.md` names the source commit but nothing signs it, so a package cannot prove which commit it came from against a hostile publisher; the destination is written only by its own job, and proving publisher authenticity is outside this run and outside ADR-040's boundary. The three lints exit 0 and the runner contract reports 741 of 741, up from the 740 on the step branch by the guard this round adds.
