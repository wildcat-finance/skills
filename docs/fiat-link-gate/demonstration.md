# Demonstration: the link gate refuses a location-dependent study

Step 3 of the [skills#1086](https://github.com/wildcat-finance/skills/issues/1086) run, recorded on 2026-09-14. It runs the study's demo path with the step 2 controller, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at commit `6add41dfe502062074ab841911fead4439f64dcd`, in a throwaway repository under the ignored `tmp/` directory. `done study` runs the link gate before its design-lock check, so the throwaway run holds this run's design record and its 18 reports for the conforming study to receipt. Local absolute paths read `<worktree>`. The throwaway repository's commit id differs on every run, and so do the `state.json` and `ledger.jsonl` digests: both files record timestamps and that commit id, and `state.json` records absolute paths.

What it shows:

1. `done study` over the five `../<skill>/SKILL.md` citations the skills#1070 run froze exits 2 and names line 3 and its target, `../ephoros/SKILL.md`.
2. The SHA-256 digests of the throwaway run's `state.json` and `ledger.jsonl` are identical before and after that refusal, so nothing was pinned.
3. The same study with each citation pinned to commit `485c90d3ad545b696584197f83d942c705988216` receipts with exit 0, and the run moves to `runbook`.

The commands and their output, as run from the worktree root with `hexctl` set to `<worktree>/plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and `demo` to `<worktree>/tmp/fiat-1086-demo`:

```text
$ mkdir "$demo"
[exit 0]

$ git -C "$demo" init -q -b main
[exit 0]

$ git -C "$demo" -c commit.gpgsign=false -c user.name=demo -c user.email=demo@example.invalid commit -q --allow-empty -m demo
[exit 0]

$ python3 "$hexctl" --dir "$demo" init --topic "link gate demonstration"
hexctl: warning: this run names no task issue, so no filed `Fiat-Required` decision was read and the receipt records the nulls. The gate binds a run called against an issue; nothing here says this work earned a run rather than one pull request.
initialised <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration/.hexaemeron (topic: link gate demonstration); run branch fiat/link-gate-demonstration off cb79b32a0929114c98e42acdc4f63f6c1697bebf
run worktree <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration
work in it: hexctl --dir <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration next
[exit 0]

$ run_dir="$demo/tmp/fiat/fiat-link-gate-demonstration"; echo "$run_dir"
<worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration
[exit 0]

$ cp .hexaemeron/design-evidence.json "$run_dir/.hexaemeron/"
[exit 0]

$ cp -R .hexaemeron/reports "$run_dir/.hexaemeron/"
[exit 0]

$ { printf '# Specimen\n\n'; for s in ephoros phylax metron elenchus hypomnema; do printf 'See [%s](../%s/SKILL.md) for its contract.\n' "$s" "$s"; done; } > "$run_dir/.hexaemeron/study.md"; cat "$run_dir/.hexaemeron/study.md"
# Specimen

See [ephoros](../ephoros/SKILL.md) for its contract.
See [phylax](../phylax/SKILL.md) for its contract.
See [metron](../metron/SKILL.md) for its contract.
See [elenchus](../elenchus/SKILL.md) for its contract.
See [hypomnema](../hypomnema/SKILL.md) for its contract.
[exit 0]

$ shasum -a 256 "$run_dir/.hexaemeron/state.json" "$run_dir/.hexaemeron/ledger.jsonl"
eaa6b25b7e08700b9d11b3fbe29a1499421f16e8324df4ba486a90f58dfb4d08  <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration/.hexaemeron/state.json
0c1f8e4f4ceaebf9c116f6c878dad885294d17ccdcfde7735a4a566fdff029cb  <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration/.hexaemeron/ledger.jsonl
[exit 0]

$ (cd "$run_dir" && python3 "$hexctl" --dir . done study --artifact .hexaemeron/study.md --skills hexaemeron:protasis)
hexctl: error: study artefact .hexaemeron/study.md line 3: pointer rule refused pointer ../ephoros/SKILL.md: its target depends on where the file sits; cite a commit-pinned absolute URL, an in-page anchor or a path in a code span
[exit 2]

$ shasum -a 256 "$run_dir/.hexaemeron/state.json" "$run_dir/.hexaemeron/ledger.jsonl"
eaa6b25b7e08700b9d11b3fbe29a1499421f16e8324df4ba486a90f58dfb4d08  <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration/.hexaemeron/state.json
0c1f8e4f4ceaebf9c116f6c878dad885294d17ccdcfde7735a4a566fdff029cb  <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration/.hexaemeron/ledger.jsonl
[exit 0]

$ { printf '# Specimen\n\n'; for s in ephoros phylax metron elenchus hypomnema; do printf 'See [%s](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/%s/SKILL.md) for its contract.\n' "$s" "$s"; done; } > "$run_dir/.hexaemeron/study.md"; cat "$run_dir/.hexaemeron/study.md"
# Specimen

See [ephoros](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/ephoros/SKILL.md) for its contract.
See [phylax](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/phylax/SKILL.md) for its contract.
See [metron](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/metron/SKILL.md) for its contract.
See [elenchus](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/elenchus/SKILL.md) for its contract.
See [hypomnema](https://github.com/wildcat-finance/skills/blob/485c90d3ad545b696584197f83d942c705988216/plugins/hexaemeron/skills/hypomnema/SKILL.md) for its contract.
[exit 0]

$ (cd "$run_dir" && python3 "$hexctl" --dir . done study --artifact .hexaemeron/study.md --skills hexaemeron:protasis)
study receipted; phase -> runbook
[exit 0]

$ shasum -a 256 "$run_dir/.hexaemeron/state.json" "$run_dir/.hexaemeron/ledger.jsonl"
4b3537fb1cc614c8c63b4485cf5e43c7da5d947f2cb2f659098735fb49bb24a2  <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration/.hexaemeron/state.json
5cb0afe06cc57dfbfe8da1efb5ba14b21b736907ea902fe6ed1e119a28301e50  <worktree>/tmp/fiat-1086-demo/tmp/fiat/fiat-link-gate-demonstration/.hexaemeron/ledger.jsonl
[exit 0]

$ (cd "$run_dir" && python3 "$hexctl" --dir . status --field phase)
"runbook"
[exit 0]
```
