# Proof: merged attribution, end to end

The demo path from the study's problem statement. Run these blocks in order in
one shell, from a clean checkout of the run's final tree. Every block exits 0.

What this establishes: the checked-in controller records who a run published
under, keeps no address while doing it, and refuses to record a run as
integrated when the base no longer carries a recorded identity. What it does
not establish: that GitHub resolves any identity to an account, or that a
contributor list updates. Those belong to GitHub.

## 1. The suites

```bash
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

192 root tests and 893 Hexaemeron tests pass. Nineteen of the Hexaemeron tests
are this run's: eight in `TestMergedAttribution` and eleven in
`TestMergedState`.

## 2. What a push records

```bash
python3 -m unittest -v \
  plugins.hexaemeron.tests.test_hexctl.TestMergedAttribution
```

Eight tests. They drive the checked-in controller against a fake `git` and `gh`
and establish, in order: an external author is recorded by account and by a
digest of the lowercased address, so `Kethcode@Example.Invalid` and
`kethcode@example.invalid` produce one digest; an unlinked author records an
explicit `null`; every co-author trailer becomes its own identity with its own
digest; twelve malformed or hostile payloads each refuse without echoing
signature material or a token; verification and attribution share one request
per SHA, asserted by counting the calls; verification alone does not apply the
identity checks, so a merge commit refuses on its signature and never on its
identity shape; and neither the push receipt nor the ledger event contains an
`@`.

## 3. What integration requires

```bash
python3 -m unittest -v \
  plugins.hexaemeron.tests.test_hexctl.TestMergedState
```

Eleven tests. A preserved merge records mechanism `ancestor` and reads no merge
identity at all. A rewritten merge is carried by the merge author, or by a
co-author trailer, and the step's own merge into the run branch is tried before
the base merge. A recorded merge that never reached the base is not accepted as
a carrier. A rewritten merge that dropped the identity refuses, naming the step,
the commit and the account, with no address in the message. An ancestry call
that answers neither 0 nor 1 refuses rather than reporting absence. A legacy
push receipt without an attribution container still integrates. The `integrate`
directive names the merge method that preserves attribution. A merge-time repair
re-derives the attribution rather than describing the head it replaced.

## 4. The red side

The two audit rounds that produced fixes are replayable against the commits
they fixed.

```bash
git stash list   # expect empty; this proof never stashes
python3 - <<'PY'
import subprocess
targets = {
    "afd1c92a00b289538af5851e74e1307c046ab914": [
        "plugins.hexaemeron.tests.test_hexctl.TestMergedAttribution."
        "test_verification_alone_does_not_apply_the_attribution_checks",
        "plugins.hexaemeron.tests.test_hexctl.TestMergedAttribution."
        "test_attribution_negative_matrix_is_fail_closed_and_secret_safe",
    ],
    "353adec7497a4effcff04ea90817b6ce511fd782": [
        "plugins.hexaemeron.tests.test_hexctl.TestMergedState."
        "test_a_step_merge_is_tried_before_the_base_merge",
        "plugins.hexaemeron.tests.test_hexctl.TestMergedState."
        "test_an_empty_repaired_container_is_current_not_absent",
        "plugins.hexaemeron.tests.test_hexctl.TestMergedState."
        "test_a_step_merge_that_never_reached_the_base_is_not_a_carrier",
    ],
}
path = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
kept = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True).stdout
assert kept, "could not read the controller from HEAD"
try:
    for commit, tests in targets.items():
        old = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True).stdout
        assert old, f"could not read the controller from {commit}"
        open(path, "wb").write(old)
        red = subprocess.run(["python3", "-m", "unittest", *tests], capture_output=True)
        open(path, "wb").write(kept)
        green = subprocess.run(["python3", "-m", "unittest", *tests], capture_output=True)
        assert red.returncode != 0, f"{commit} guards did not fail on the unfixed tree"
        assert green.returncode == 0, f"{commit} guards do not pass on the fixed tree"
        print(commit[:12], "red then green over", len(tests), "guard(s)")
finally:
    # A failed assertion, a killed process or a broken `git show` must not
    # leave the reader's checkout holding an older controller.
    open(path, "wb").write(kept)
PY
git diff --quiet plugins/hexaemeron/skills/fiat/scripts/hexctl.py
```

The file is restored from `HEAD` rather than through `git stash`, because the
stash stack in this repository is shared across every worktree and a push that
saves nothing turns a push and pop pair into a bare pop of somebody else's work.

## 5. The release surface

```bash
python3 scripts/promise_machine.py check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
git diff --quiet .horos/boundary.json
```

Promise Machine reports 14 plugins and 14 copies clean; the three `fiat-*`
runtime digests match the controller this run ships. The Horos scan leaves the
boundary unchanged.

## 6. What the live run could not do

This run was governed by the installed Fiat controller, which knows neither
container. Its own push and integration receipts therefore carry no
attribution, and nothing in this run's ledger claims otherwise. The evidence
above is the checked-in controller under test, which is the controller a later
run installs. The split is recorded in `audit/AUDIT.md` under step 2 round 1 and
step 3 rounds 1 and 2.
