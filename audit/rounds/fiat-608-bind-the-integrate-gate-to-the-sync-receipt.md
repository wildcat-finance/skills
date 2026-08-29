# Issue 608: bind the integrate gate to the sync receipt's recorded base head

Rounds for the run on branch
`fiat/608-bind-the-integrate-gate-to-the-sync-receipt`, off `main` at
`c4650f02a979e859ce36374779eac9cd70744288`. The controller derived this path at
`init`. Headings carry step and round alone, because the file names the run;
finding ids follow `S<step>-R<round>-NN`.

## Step 1, round 1 -- 2026-08-25

Non-Solidity round over the two Markdown documents step 1 commits, at
`7e1fec38dfc21099e4870a589d36a77bc5501ee7` on the step branch
`fiat/608-bind-the-integrate-gate-to-the-sync-receipt-step-1-publish-the-accepted-base-head-s`.
The bundled Solidity suite is waived for the reason the study records: the diff
is static Markdown and touches no Solidity. Zero findings.

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| none | -- | -- | -- | -- |

The range holds exactly one commit and it adds exactly two files, 397 lines,
with no stray path. Both are byte-identical to the receipted artefacts twice
over: `cmp` against `.hexaemeron/study.md` and `.hexaemeron/runbook.md` exits 0
on each, and the tracked copies hash to the receipted digests,
`4229f580b240d7bded8aa1f9b48c4d39afa3fffe6444156a06fc8c831d503095` for the
study and
`744d742956b44f919f14a40a0327ff53175365c99047cb8950e63bc9fd18ef87` for the
runbook. The commit's local signature is good and it carries exactly one
co-author trailer and one origin trailer.

The three bundled lints exit 0: Phylax and Ephoros over `plugins` and `tests`,
Hypomnema over `README.md AGENTS.md .agents plugins docs`. Protasis accepts the
shipped study in `--study` mode and the shipped runbook in runbook mode.
Imprimatur scores both 100.0 with no defects. The study's five relative links
-- the ephoros, phylax, metron, elenchus and hypomnema `SKILL.md` targets --
all resolve from `docs/`; the runbook carries none. Horos reports that the
boundary matches the tree. The root suite reports 350 tests OK, the Hexaemeron
suite 1,092/1,092, and `git diff --check` exits 0 over the range.

One tool ran beyond the step's stated gates and returned a signal. Brevitas
exits 0 on the runbook and 1 on the study:
`docs/fiat-integrate-base-head-study.md:42: B027 claim stacks 2 qualifiers;
maximum is 1`. It is recorded as a lead rather than a finding because the
step's own exit freezes those bytes -- the copy must stay byte-identical to the
receipted study, which cannot be corrected, only amended -- and because
Brevitas is not among the gates the runbook names for this step. Whether a Fiat
study is inside Brevitas scope at all is arguable, since the skill excludes
completeness-oriented specification documents; the prior two runs' rounds
treated shipped studies as in scope and recorded clean passes, so the signal is
kept visible here rather than argued away.

Two register concerns are reachable at this step in analogue form and were
checked. `receipt-key-drift` is owed by step 2, where the constant lands; the
shape it takes here is drift between the shipped copies and the receipts, and
the byte-identity evidence above closes it. `bootstrap-limit` is run-level
rather than diff-level: the study names it and nothing in a docs-only diff can
move it, so it stays open by design until integrate. The other five are not
reachable in this diff and were verified untouched: `ledger-arithmetic` and
`state-compat` sit in step 2's controller and ledger changes, and the diff
names no path under `plugins/`; `version-propagation` sits in steps 2 and 3's
pinned surfaces, none of which the diff touches; `digest-pin-refresh` cannot
drift while `hexctl.py` is unchanged, and the green root suite re-checks the
pins; `test-cap` adds no test bytes anywhere.

Leads not pursued: two. First, the B027 above. The rule shipped with Brevitas's
first commit, so it predates this run's receipting and the drafting phase did
not run Brevitas before the freeze; the repair path is an appended amendment or
the next run's drafting discipline, not an edit to shipped bytes. Second, the
study's assumption 6 places the tracked copies at
`docs/fiat-integrate-receipt-binding-study.md` and `-runbook.md`, while the
receipted runbook's step 1 names the `fiat-integrate-base-head-` paths the
commit used. The runbook governed and the exit holds, but both artefacts are
receipt-frozen, so the disagreement stands in the published bytes and no gate
compares the two placements; a check belongs to Protasis and is outside this
run.

## Step 2, round 1 -- 2026-08-26T03:14:50Z

Audit schema: fiat-audit-round/v2

Covered: receipt-key-drift=reviewed; ledger-arithmetic=reviewed; version-propagation=not-applicable; state-compat=reviewed; bootstrap-limit=not-applicable; digest-pin-refresh=reviewed; test-cap=reviewed

Not checked: Solidity (waived: no Solidity in scope; the change is one controller read path and its regression test); package-version propagation (step 3); run-level bootstrap recovery (integrate).

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none

## Step 3, round 1 -- 2026-08-26T10:02:57Z

Audit schema: fiat-audit-round/v2

Covered: receipt-key-drift=reviewed; ledger-arithmetic=reviewed; version-propagation=reviewed; state-compat=reviewed; bootstrap-limit=reviewed; digest-pin-refresh=reviewed; test-cap=reviewed

Not checked: Solidity (waived: no Solidity in scope; the change is one controller read path and its regression test); signed live-main composition and bounded integration revalidation (integrate phase).

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: one integration composition condition, not a product finding. Live origin/main at 5489863196006d8e8b45799d74b56208cac65e4d already carries different fiat-v5.25.1 and fiat-v5.26.1 rows. The product remains valid as fiat-v5.25.1 against starting base c4650f02a979e859ce36374779eac9cd70744288; the signed product-first Fiat sync owns the collision, must resolve issue 608 to the then-next generation, and must cover every affected path with green integration revalidation.
