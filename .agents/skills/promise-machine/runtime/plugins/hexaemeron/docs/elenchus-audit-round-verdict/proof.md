# Elenchus audit-round verdict proof

This proof records the issue 327 demonstration run on 2026-08-22. It used the
checkout controller at
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, SHA-256
`01efd29fcc0b1198aa62989291c1dbe4713d7c26cccbba40a1fbe4b210884870`,
from step 3's parent `024a64d9265ca21551cfab4a969657e7cefef2ad`.
The run exercised a fresh repository and the worktree created by `hexctl init`.
No network, credential, Solidity target, or raw signature output entered the
record.

The controller writes absolute worktree paths, UTC timestamps, and signed
commit ids into its packets, state, and ledger. Hashes over those values are
run-local diagnostics, not cross-run oracles. The commands below print them
and compare them only inside one replay. Fixed hashes are stated only for
source bytes that do not depend on the generated path, clock, or signing
metadata.

## Reproduction boundary

Run these commands from a clean repository root with Python 3.12 and a
configured Git signing key. The fixture uses tracked delivery documents and a
generated directory under the repository's ignored `.hexaemeron` boundary; it
does not depend on active Fiat state.

```bash
set -euo pipefail
PROJECT_ROOT=$(cd "$(git rev-parse --show-toplevel)" && pwd -P)
DEMO_PARENT="$PROJECT_ROOT/.hexaemeron"
DEMO_PARENT_CREATED=0
test ! -L "$DEMO_PARENT"
if [ ! -e "$DEMO_PARENT" ]; then
  mkdir "$DEMO_PARENT"
  DEMO_PARENT_CREATED=1
fi
test -d "$DEMO_PARENT"
DEMO_ROOT=$(mktemp -d "$DEMO_PARENT/issue327-step3-XXXXXX")
DEMO_ORIGIN="$DEMO_ROOT/origin"
HEXCTL="$PROJECT_ROOT/plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
STUDY_SOURCE="$PROJECT_ROOT/plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md"
RUNBOOK_SOURCE="$PROJECT_ROOT/plugins/hexaemeron/docs/elenchus-audit-round-verdict/runbook.md"
test "$(sha256sum "$HEXCTL" | awk '{print $1}')" = \
  "01efd29fcc0b1198aa62989291c1dbe4713d7c26cccbba40a1fbe4b210884870"
test "$(sha256sum "$STUDY_SOURCE" | awk '{print $1}')" = \
  "425152f8d8573197f33dcb491892f937798d4fe3b66ec612d8ce8ea05967852f"
test "$(sha256sum "$RUNBOOK_SOURCE" | awk '{print $1}')" = \
  "a98c67bda303bac1b3aea09817059a07d9dc45a64472847854be7547c4bd555c"
mkdir "$DEMO_ORIGIN"
git -C "$DEMO_ORIGIN" init -b main
git -C "$DEMO_ORIGIN" config user.name "Dave Coleman"
git -C "$DEMO_ORIGIN" config user.email "dave@wildcat.finance"
git -C "$DEMO_ORIGIN" commit -S --allow-empty -m "demo base"
python3.12 "$HEXCTL" --dir "$DEMO_ORIGIN" init \
  --topic "issue 327 proof" --base main
DEMO_RUN="$DEMO_ORIGIN/tmp/fiat/fiat-issue-327-proof"
```

```bash
cp "$STUDY_SOURCE" "$DEMO_RUN/.hexaemeron/study.md"
cp "$RUNBOOK_SOURCE" "$DEMO_RUN/.hexaemeron/runbook.md"
printf '\n' >> "$DEMO_RUN/.hexaemeron/runbook.md"
test "$(sha256sum "$DEMO_RUN/.hexaemeron/runbook.md" | awk '{print $1}')" = \
  "82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85"
python3.12 - "$DEMO_RUN/.hexaemeron/steps.json" <<'PY'
import json
import sys
from pathlib import Path

steps = [
    "Bind the runbook test command to the Elenchus contract",
    "Receipt the four verdicts and source-bind Warden",
    "Demonstrate legacy and release compatibility",
]
Path(sys.argv[1]).write_text(json.dumps(steps, indent=2) + "\n")
PY
python3.12 "$HEXCTL" --dir "$DEMO_RUN" done study \
  --artifact "$DEMO_RUN/.hexaemeron/study.md" \
  --skills hexaemeron:protasis,hexaemeron:imprimatur
python3.12 "$HEXCTL" --dir "$DEMO_RUN" done runbook \
  --artifact "$DEMO_RUN/.hexaemeron/runbook.md" \
  --steps-file "$DEMO_RUN/.hexaemeron/steps.json"
```

Call `next` twice before the implementation receipt. Decode both JSON objects,
require them to be equal, and retain only the Mason `brief.runbook_step`.
Create the branch and implementation commit named by that packet. Each
receipted implementation or fix commit uses one exact copy of each required
trailer.

```bash
MASON_ONE=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
MASON_TWO=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
test "$MASON_ONE" = "$MASON_TWO"
STEP_BRANCH=$(python3.12 -c \
  'import json,sys; print(json.loads(sys.argv[1])["brief"]["branch"])' \
  "$MASON_ONE")
STEP_BASE=$(python3.12 -c \
  'import json,sys; print(json.loads(sys.argv[1])["brief"]["branch_from"])' \
  "$MASON_ONE")
git -C "$DEMO_RUN" switch -c "$STEP_BRANCH" "$STEP_BASE"
git -C "$DEMO_RUN" commit -S --allow-empty \
  -m "issue 327 proof implementation" \
  -m $'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>\nWildcat-Origin: shoggoth'
IMPLEMENTATION=$(git -C "$DEMO_RUN" rev-parse HEAD)
python3.12 "$HEXCTL" --dir "$DEMO_RUN" done implement \
  --branch "$STEP_BRANCH" --commit "$IMPLEMENTATION" \
  --tests "disposable proof fixture"
python3.12 "$HEXCTL" --dir "$DEMO_RUN" record security_suite \
  '"waived: issue 327 proof has no Solidity target"'
WARDEN_ONE=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
WARDEN_TWO=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
test "$WARDEN_ONE" = "$WARDEN_TWO"
```

```bash
python3.12 - "$MASON_ONE" "$WARDEN_ONE" <<'PY'
import hashlib
import json
import sys
mason = json.loads(sys.argv[1])
warden = json.loads(sys.argv[2])
assert mason["brief"]["runbook_step"] == warden["brief"]["runbook_step"]
assert sorted(warden["brief"]["runbook_step"]) == [
    "markdown", "number", "path", "sha256", "title",
]
compact = lambda value: json.dumps(
    value, sort_keys=True, separators=(",", ":")
).encode()
step = warden["brief"]["runbook_step"]
assert hashlib.sha256(step["markdown"].encode()).hexdigest() == (
    "4da25cd2d9e8e046016501d69dd0289de2cf3dad78f0e486f59dc7d4fd7515ef"
)
assert step["sha256"] == (
    "82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85"
)
print("mason packet", hashlib.sha256(compact(mason)).hexdigest())
print("warden packet", hashlib.sha256(compact(warden)).hexdigest())
print("runbook step", hashlib.sha256(compact(step)).hexdigest())
PY
```

The decoded Mason and Warden packets carried the same five-field
`runbook_step`. Its Markdown was the exact byte range from the Step 1 heading
up to the Step 2 heading in the receipted runbook. The observed packet evidence
was:

| Subject | Replay assertion | Cross-run digest |
| --- | --- | --- |
| Mason packet | repeated compact JSON objects are equal | run-local; printed by the replay |
| Warden packet | repeated compact JSON objects are equal | run-local; printed by the replay |
| `runbook_step` | both packets carry the same five fields | run-local; its path is generated |
| Step 1 Markdown | exact source bytes | `4da25cd2d9e8e046016501d69dd0289de2cf3dad78f0e486f59dc7d4fd7515ef` |
| Receipted runbook | exact source artefact | `82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85` |

The Warden brief had exactly `audit_log_path`, `plugin_root`, `risk_register`,
`round`, `runbook_step`, `security_suite`, `stacked_branch`, and
`step_branch`. The step number was 1 and the title was `Bind the runbook test
command to the Elenchus contract`.

## Refusals, null, and legacy state

Create one signed candidate fix from the implementation head, then take
SHA-256 digests of `.hexaemeron/state.json` and
`.hexaemeron/ledger.jsonl`. `expect_refusal` requires exit 2 and compares both
raw files after each refused command, rather than assuming three commands
cannot cancel one another's mutations:

```bash
signed_fix() {
  git -C "$DEMO_RUN" commit -S --allow-empty -m "$1" \
    -m $'Co-authored-by: Shoggoth <shoggoth@wildcat.finance>\nWildcat-Origin: shoggoth' \
    >/dev/null
  git -C "$DEMO_RUN" rev-parse HEAD
}
LINT_ARGS=(--phylax-exit 0 --ephoros-exit 0 --hypomnema-exit 0)
FIX_1=$(signed_fix "issue 327 proof fix guarded")
digest_pair() {
  sha256sum "$DEMO_RUN/.hexaemeron/state.json" \
    "$DEMO_RUN/.hexaemeron/ledger.jsonl" | awk '{print $1}' | paste -sd : -
}
expect_refusal() {
  before=$(digest_pair)
  set +e
  "$@"
  status=$?
  set -e
  test "$status" -eq 2
  after=$(digest_pair)
  test "$before" = "$after"
  printf 'exit=%s state:ledger=%s\n' "$status" "$after"
}
expect_refusal python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round \
  --findings 1 --fixes-commit "$FIX_1" "${LINT_ARGS[@]}"
expect_refusal python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round \
  --findings 1 --elenchus-verdict guarded "${LINT_ARGS[@]}"
expect_refusal python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round \
  --findings 1 --fixes-commit "$FIX_1" --elenchus-verdict unknown \
  "${LINT_ARGS[@]}"
```

Each command exited 2. The first named the missing verdict and all four
accepted values, the second named the missing fix, and the third was rejected
by the closed command-line enum. Each printed the same run-local state and
ledger digest pair it observed before the command:

| Case | Exit | File relation |
| --- | ---: | --- |
| fix without verdict | 2 | state and ledger bytes unchanged |
| verdict without fix | 2 | state and ledger bytes unchanged |
| unknown verdict | 2 | state and ledger bytes unchanged |

A no-fix round with one finding and the three zero lint exits then recorded an
explicit JSON null in both state and ledger. The check prints their run-local
digests after asserting both fields exist and are null.

```bash
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  "${LINT_ARGS[@]}"
python3.12 - "$DEMO_RUN" <<'PY'
import json, sys
from pathlib import Path
meta = Path(sys.argv[1]) / ".hexaemeron"
state = json.loads((meta / "state.json").read_text())
event = json.loads((meta / "ledger.jsonl").read_text().splitlines()[-1])
round_entry = state["steps"][0]["audit"]["rounds"][-1]
assert "elenchus_verdict" in round_entry
assert round_entry["elenchus_verdict"] is None
assert "elenchus_verdict" in event["data"]
assert event["data"]["elenchus_verdict"] is None
PY
printf 'null state:ledger=%s\n' "$(digest_pair)"
```

The proof removed that round's `elenchus_verdict` key from both files to model
a pre-generation round. It recomputed the canonical compact state fingerprint,
replaced the last ledger entry's `state`, and recomputed that entry's hash over
the entry without its old `hash` field. The script prints those run-local
digests after it writes the legacy fixture.

```bash
python3.12 - "$DEMO_RUN" <<'PY'
import hashlib, json, sys
from pathlib import Path
meta = Path(sys.argv[1]) / ".hexaemeron"
state_path, ledger_path = meta / "state.json", meta / "ledger.jsonl"
state = json.loads(state_path.read_text())
state["steps"][0]["audit"]["rounds"][-1].pop("elenchus_verdict")
compact = lambda value: json.dumps(
    value, sort_keys=True, separators=(",", ":")
).encode()
state_fingerprint = hashlib.sha256(compact(state)).hexdigest()
state_path.write_text(json.dumps(state, indent=2) + "\n")
entries = [json.loads(line) for line in ledger_path.read_text().splitlines()]
entries[-1]["data"].pop("elenchus_verdict")
entries[-1]["state"] = state_fingerprint
unsigned = {key: value for key, value in entries[-1].items() if key != "hash"}
entries[-1]["hash"] = hashlib.sha256(compact(unsigned)).hexdigest()
ledger_path.write_text("".join(
    json.dumps(entry, sort_keys=True) + "\n" for entry in entries
))
print("legacy state fingerprint", state_fingerprint)
print("legacy ledger tail", entries[-1]["hash"])
PY
printf 'legacy state:ledger=%s\n' "$(digest_pair)"
```

`status`, `next`, and `verify` each exited 0 after the edit. `next` returned
`audit-round` round 2. A later verified fix round exited 0, and `done audit`
later exited 0 without adding the missing legacy field.

```bash
python3.12 "$HEXCTL" --dir "$DEMO_RUN" status
LEGACY_NEXT=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
python3.12 -c \
  'import json,sys; p=json.loads(sys.argv[1]); assert (p["do"],p["round"]) == ("audit-round",2)' \
  "$LEGACY_NEXT"
python3.12 "$HEXCTL" --dir "$DEMO_RUN" verify
```

## Four preserved verdicts

Four signed, single-commit ranges followed the legacy round. `git
verify-commit` exited 0 for every head, each message held one exact copy of the
two provenance trailers, and each controller receipt listed only that new head
in `verified_commits`.

```bash
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --fixes-commit "$FIX_1" --elenchus-verdict guarded "${LINT_ARGS[@]}"
printf 'round 2 state:ledger=%s\n' "$(digest_pair)"
FIX_2=$(signed_fix "issue 327 proof fix unguarded")
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --fixes-commit "$FIX_2" --elenchus-verdict unguarded "${LINT_ARGS[@]}"
printf 'round 3 state:ledger=%s\n' "$(digest_pair)"
FIX_3=$(signed_fix "issue 327 proof fix passed")
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 1 \
  --fixes-commit "$FIX_3" --elenchus-verdict passed "${LINT_ARGS[@]}"
printf 'round 4 state:ledger=%s\n' "$(digest_pair)"
FIX_4=$(signed_fix "issue 327 proof fix inconclusive")
python3.12 "$HEXCTL" --dir "$DEMO_RUN" audit-round --findings 0 \
  --fixes-commit "$FIX_4" --elenchus-verdict inconclusive \
  "${LINT_ARGS[@]}"
printf 'round 5 state:ledger=%s\n' "$(digest_pair)"
```

```bash
python3.12 - "$DEMO_RUN" "$IMPLEMENTATION" \
  "$FIX_1" "$FIX_2" "$FIX_3" "$FIX_4" <<'PY'
import json, subprocess, sys
from pathlib import Path
run = Path(sys.argv[1])
implementation, *fixes = sys.argv[2:]
meta = run / ".hexaemeron"
state = json.loads((meta / "state.json").read_text())
rounds = state["steps"][0]["audit"]["rounds"]
events = [
    json.loads(line) for line in (meta / "ledger.jsonl").read_text().splitlines()
    if json.loads(line)["event"] == "audit-round"
]
expected = ["missing", "guarded", "unguarded", "passed", "inconclusive"]
assert [item.get("elenchus_verdict", "missing") for item in rounds] == expected
assert [item["data"].get("elenchus_verdict", "missing") for item in events] == expected
trailers = ["Co-authored-by: Shoggoth <shoggoth@wildcat.finance>",
            "Wildcat-Origin: shoggoth"]
for commit in [implementation, *fixes]:
    message = subprocess.check_output(
        ["git", "-C", str(run), "show", "-s", "--format=%B", commit]
    ).decode().rstrip("\n").splitlines()
    assert message[-2:] == trailers
    assert all(message.count(trailer) == 1 for trailer in trailers)
    result = subprocess.run(
        ["git", "-C", str(run), "verify-commit", commit],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    assert result.returncode == 0
for parent, commit, round_entry, event in zip(
    [implementation, *fixes[:-1]], fixes, rounds[1:], events[1:]
):
    assert subprocess.check_output(
        ["git", "-C", str(run), "rev-parse", f"{commit}^"]
    ).decode().strip() == parent
    assert round_entry["fixes_commit"] == commit
    assert round_entry["verified_commits"] == [commit]
    assert event["data"]["verified_commits"] == [commit]
PY
```

```bash
CLOSE_NEXT=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
python3.12 -c \
  'import json,sys; assert json.loads(sys.argv[1])["do"] == "close-audit"' \
  "$CLOSE_NEXT"
python3.12 "$HEXCTL" --dir "$DEMO_RUN" done audit
python3.12 "$HEXCTL" --dir "$DEMO_RUN" verify
python3.12 -c \
  'import json,sys,pathlib; s=json.loads((pathlib.Path(sys.argv[1])/".hexaemeron/state.json").read_text()); assert (s["version"],s["steps"][0]["phase"]) == (1,"prose")' \
  "$DEMO_RUN"
PROSE_NEXT=$(python3.12 "$HEXCTL" --dir "$DEMO_RUN" next)
python3.12 -c \
  'import json,sys; p=json.loads(sys.argv[1]); assert (p["do"],p["step"]) == ("prose",1)' \
  "$PROSE_NEXT"
printf 'final state:ledger=%s\n' "$(digest_pair)"
```

| Label | Commit identity | Round | Findings | Verdict |
| --- | --- | ---: | ---: | --- |
| `fix-1` | one signed commit above the implementation | 2 | 1 | `guarded` |
| `fix-2` | one signed commit above `fix-1` | 3 | 1 | `unguarded` |
| `fix-3` | one signed commit above `fix-2` | 4 | 1 | `passed` |
| `fix-4` | one signed commit above `fix-3` | 5 | 0 | `inconclusive` |

The final state remained version 1 and moved the step to `prose`. Its five
rounds exposed `missing`, `guarded`, `unguarded`, `passed`, and `inconclusive`
in order. Final `verify` exited 0, and the replay printed the final run-local
state and ledger digests. The successful generated boundary was removed after
these assertions.

```bash
python3.12 - "$DEMO_ROOT" "$DEMO_PARENT" <<'PY'
from pathlib import Path
import shutil, sys
boundary = Path(sys.argv[1]).resolve()
expected_parent = Path(sys.argv[2]).resolve()
assert boundary.parent == expected_parent
assert boundary.name.startswith("issue327-step3-")
shutil.rmtree(boundary)
PY
test ! -e "$DEMO_ROOT"
test ! -L "$DEMO_ROOT"
if [ "$DEMO_PARENT_CREATED" -eq 1 ]; then
  rmdir "$DEMO_PARENT"
  test ! -e "$DEMO_PARENT"
  test ! -L "$DEMO_PARENT"
fi
```

## Study and release reconciliation

The receipted study changed once during step 2. Its prior SHA-256 was
`06f8e81b95c7ceba26ada998fe62b57a87d9afa3eea10a31813862842851abe0`,
its amended SHA-256 is
`e416668d0adb0c986ee1080b92ba9f6c07f151ba7b13ecf776b664a75dc26870`,
and the exact 888 appended bytes have SHA-256
`51e378a68b0c39a59b8ba0051b35a8b8ecc6a691446c5862bfbe34eae095debb`.
The committed copy keeps its five repository-relative skill links instead of
the live `.hexaemeron` paths. It therefore moved from
`46531ccad9b908c4af8faa6e13d8ab5842c2032a96ce9e6feb5134bf1f15bf8e`
to `425152f8d8573197f33dcb491892f937798d4fe3b66ec612d8ce8ea05967852f`
after the same 888-byte amendment was appended.

The runbook has a separate one-byte discrepancy already recorded by the run:
the receipted file is 11,430 bytes at
`82f1952def5d8658c2c8207d4c170632c0f14180cf8e5a554f980a85b7bf6f85`;
the committed copy is its first 11,429 bytes at
`a98c67bda303bac1b3aea09817059a07d9dc45a64472847854be7547c4bd555c`.
Only the receipted file's final newline is absent from the committed copy.

The final cold read found no stale release surface:

| Surface | Observed value | Disposition |
| --- | --- | --- |
| Elenchus frontmatter and ledger | `1.2.0`, `elenchus-v1.2.0`, mature | generation row retains the mature frontier; issue 453 stays deferred |
| Fiat frontmatter and ledger | `5.12.1`, `fiat-v5.12.1`, frontier SHA-256 `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa` | generation row retains issue 363's exact held target |
| Protasis frontmatter and ledger | `4.6.0`, `protasis-v4.6.0` | generation row retains the amendment-check frontier |
| Warden and audit loop | four exact values; checked and recorded, not report-byte attestation | issue 453 still owns stronger binding and blocking |
| both plugin manifests and both marketplaces | Hexaemeron `1.5.5` | all package surfaces agree |
| version constants | Hexaemeron `1.5.5`; three skill versions above | tests name the same release |
| Promise coverage | controller SHA-256 `01efd29f...884870` on all three Fiat runtime bindings | canonical promise text and field maps are unchanged |

Issue 429 remains the downstream schema and synopsis work. Issue 453 remains
the report-evidence binding and production gate. Neither was implemented or
closed here.
