# Study: carry the Elenchus guard verdict into Fiat audit rounds

Assuming, unless corrected:

1. A step makes a formal bug-fix claim by placing one `elenchus-guard` block
   inside its exact receipted runbook step. Fiat will not infer that claim from
   a title, prose keywords or the diff.
2. The block owns the test command and report adapter inputs. The controller
   records the Elenchus verdict reported by the Warden; it does not execute the
   test command itself or claim that a reported value proves the command ran.
3. `guarded`, `unguarded`, `passed` and `inconclusive` remain observations, not
   a new audit-close policy. Requiring a known failing guard before production
   work belongs to issue #453 and is outside this run.
4. A legacy runbook with no guard block is an ordinary step and owes no guard
   field. Existing states and audit rounds remain readable and gain no claim
   they did not record.
5. This is generation work for Elenchus and Fiat. It does not reopen or advance
   either held frontier.

## 1. Problem statement

Elenchus already classifies a changed test against its parent as exactly one of
`guarded`, `unguarded`, `passed` or `inconclusive`. Fiat's Warden can read the
result, but `audit-round` has nowhere to preserve it. An unguarded bug fix is
therefore carried into `Leads not pursued` by hand, and a later reader cannot
recover the verdict from controller state.

Build a source-bound route for maintainers running Fiat over a bug-fix step.
The runbook declares the Elenchus command, the Warden runs that command against
the implementation commit, and the audit-round receipt stores the returned
status beside the three existing lint exits. A working prototype satisfies all
of these checks:

- `python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker -v`
  continues to prove all four verdicts and the structured-report refusals.
- Focused controller tests create a bug-fix runbook, show that `hexctl next`
  carries the exact command, source digest and implementation ref, show that a
  missing `--guard-status` is refused, and show that each of the four values is
  stored unchanged on an audit round.
- The same tests mutate, remove and duplicate the receipted block and require
  `next` to refuse before emitting a Warden packet.
- A non-bug-fix step reaches and closes audit without a guard flag, and a
  legacy state carrying no guard data remains readable.
- `python3 -m unittest discover -s tests` and
  `python3 plugins/hexaemeron/tests/run_tests.py` pass, followed by
  `python3 scripts/promise_machine.py check`,
  `python3 scripts/promise_machine.py coverage --check` and
  `git diff --check`.

Those checks establish receipt shape, source binding and preservation of the
reported category. They do not establish that every bug fix is guarded, that a
caller reported honestly, or that the surrounding system has no other fault.

## 2. Prior art

The target starts at `cd48583be2caeace32b14638dbdd85692b73a004` on
`main`. `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` hashes to
`9069e2a4266bf349c963aaad6e22cf2966d14bb34d05d025b72c9e77017d39c5`.
Its `check()` result and CLI JSON contain `status`; `audit_line()` renders that
status for a person. The classifier reads runner-owned structure and treats
diagnostics and ordinary exit codes as non-classifying evidence. An unguarded
result is non-fatal unless the caller selects `--require-guard`.

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` hashes to
`adf0fc24d650fdbb9d38b5b7ccb52320e5d76c1fbed0f3e9f303fa79a4d48167`.
`done runbook` currently registers titles from `.hexaemeron/steps.json` and
binds the Markdown artefact by SHA-256. `source_runbook_step()` later selects
one exact, unfenced `## Step N: <title>` block. The Warden packet carries the
risk register but not the runbook step. `audit-round` accepts the three lint
exits, checks their consistency with the findings count, and stores them under
`lints`. It records no guard field.

The two latest merged pull requests that changed the controller were read.
[PR #445](https://github.com/wildcat-finance/skills/pull/445) bound task issues
to run and step branches and carried issue #363 forward untouched. That issue
stays outside this run. [PR #444](https://github.com/wildcat-finance/skills/pull/444)
made the frontier ledger gate accept both history-row spellings; it carried no
unfinished guard work.

The behaviour origins were also read. [PR #195](https://github.com/wildcat-finance/skills/pull/195)
introduced the four Elenchus outcomes and fixed report ownership and bounded
reads. [PR #206](https://github.com/wildcat-finance/skills/pull/206) added the
three receipted lint exits and states the relevant limit: the controller
records what the caller reports and cannot know that a check ran. Its package
publication repair in [PR #207](https://github.com/wildcat-finance/skills/pull/207)
shows that changed installed behaviour also needs a Hexaemeron package bump.
The two latest merged pull requests touching the Elenchus skill text,
[PR #426](https://github.com/wildcat-finance/skills/pull/426) and
[PR #288](https://github.com/wildcat-finance/skills/pull/288), removed a
duplicated routing paragraph and added Promise Machine declarations. Neither
left guard-to-audit work open. PR #195 was read as the last merged behavioural
change to Elenchus.

The current audit records were read before drawing options. `audit/AUDIT.md`
sections `Elenchus structured reports, step 1, rounds 1-2` preserve the two
fixed report-boundary findings and a clean second round. Sections `Receipted
lint rounds, steps 1-3` preserve the structured-field precedent, its
caller-reporting limit, its backward-compatibility checks and its clean-close
composition. `plugins/hexaemeron/audit/AUDIT.md` contains only the older plugin
baseline audit; it adds no later Elenchus or lint-receipt decision. No relevant
lead from those records is silently reopened here.

Issue #429 depends on this result. Its future audit schema and synopsis must
preserve the four-value verdict. This study supplies that structured value and
stops. It does not build #429's schema, timestamp or synopsis.

## 3. Constraints and non-goals

The starting ref is the exact SHA above. The observed tools are Python 3.14.6,
Forge 1.7.1, Node 26.6.0, Git 2.50.1 and GitHub CLI 2.96.0. Use Python's
standard library and the existing Elenchus adapters; add no dependency, shell
execution or new report format. No Solidity changes are planned.

The formal runbook extension is a single fenced block inside the step that
claims a bug fix:

````markdown
```elenchus-guard
{
  "test_command": "python3 tests/emit_unittest_report.py {report}",
  "report_format": "unittest-json-v1",
  "report_file": ".elenchus/unittest.json"
}
```
````

The command has one exact `{report}` argument. `report_format` is one of the
three existing Elenchus formats, and `report_file` stays under the existing
Elenchus report-path rules. The block's presence is the claim; no block means
the step does not claim a bug fix. This run does not guess from words such as
"repair", inspect commit-message intent, or classify the diff.

The Warden runs the block against the signed implementation commit stored by
`done implement`. Audit-fix commits are separate findings work and do not
replace the ref whose changed tests are being checked. The controller adds no
`--require-guard` policy. It stores an unguarded, passed or inconclusive result
without recasting it as guarded or clean.

Out of scope: #429's audit-log schema and synopsis, #369's synopsis reader,
#453's pre-change known-failure injection, #363's delegated-task identity,
rewriting historical audit entries, changing Elenchus classification, running
the test command inside `hexctl`, and changing CI.

Boundaries for the run:

- **Always.** Run the focused Elenchus, controller and delegation-packet tests;
  both repository suites; Promise Machine checks; all lints required by the
  changed tree; version, manifest and frontier checks; and `git diff --check`
  before a commit.
- **Ask first.** Adding a dependency, changing CI, making an unguarded result
  block audit closure, changing any public Elenchus report format, changing a
  held frontier, or widening the subprocess trust boundary.
- **Never.** Run the guard command through a shell, copy its diagnostics into
  controller state, edit a vendored directory, alter an old audit entry, delete
  a failing test, claim an unrun command ran, or change key or credential
  handling.

## 4. Design options

**A. Add a free `--guard-status` flag.** This copies the lint-exit surface with
the fewest lines. It gives the caller a value even when no runbook command
exists, so the receipt cannot say which fix or command the status describes.
Rejected because it preserves a word without its source.

**B. Infer bug-fix steps from titles, prose or changed files.** This avoids a
new runbook marker. The vocabulary is open, refactors can change tests, and a
bug fix can touch no conventionally named file. The inference would be both
easy to evade and hard to explain. Rejected.

**C. Put the command in an expanded `steps.json` object.** The sidecar is
already read during the runbook receipt and could carry the whole declaration.
It would duplicate the human-readable `**Tests.**` contract and create a second
source whose bytes are not currently retained by the receipt. Rejected in
favour of one visible source.

**D. Parse one bounded `elenchus-guard` block from the exact runbook step.**
Chosen. The current runbook SHA and exact-step selector already provide most of
the source boundary. The controller adds one block parser, includes the block
and implementation ref in the Warden brief, requires `--guard-status` only for
that step, and stores the value with the runbook and command digests. This is
the cheapest construction that binds the status to an inspectable command.
It trades away implicit discovery: a prose bug-fix claim without the block is
a malformed Fiat specification and must be corrected at runbook review rather
than guessed during audit.

The block parser accepts exactly one block per exact step, a JSON object with
the three fields shown above and no empty value. It rejects a missing field, a
duplicate or nested decoy, an unknown report format, a command without one
exact `{report}`, and source bytes that no longer match the receipted runbook.
The Warden packet gains `guard`, containing the command fields, source path and
SHA-256, step number and title, command SHA-256, and the implementation ref.
`next` names `--guard-status` as owed. The receipt accepts only the four
existing values, refuses the flag on a step with no guard block, and stores a
structured guard record on every audit round for the declared step. Legacy
rounds retain an absent field.

## 5. Risk register seed

```risk-register
claim-omission | the boundary between a prose bug-fix claim and the formal runbook block | review and tests refuse a claimed fix whose exact step lacks the declaration
source-drift | the receipted runbook bytes used to build a Warden packet | mutation removal and duplicate-block specimens refuse before packet emission
command-injection | the repository-owned test command executed by Elenchus | one report placeholder is split without a shell and existing path and timeout controls remain active
verdict-forgery | the value reported back to audit-round | the receipt states it is caller-reported and accepts only the four Elenchus values
verdict-drift | the duplicated status vocabulary at the Elenchus and Fiat boundary | a test derives or compares the accepted set so a new Elenchus value cannot be dropped silently
ref-mismatch | the commit whose changed tests Elenchus overlays onto its parent | the packet and stored guard record name the signed implementation receipt commit
diagnostic-leak | bounded test output at the Warden-to-controller boundary | only status source digests and ref enter state or ledger
legacy-overclaim | states and runbooks written before the guard field existed | legacy reads remain valid and never synthesise a status or source binding
later-issue-leak | the boundary between verdict preservation and later consumption policy | tests preserve all four values without adding schema synopsis injection or closure policy
frontier-drift | the mature Elenchus ledger and open Fiat held target | generation rows retain both frontier revisions and digests byte for byte
package-staleness | the installed Hexaemeron copy after controller behaviour changes | version-propagation tests require one package bump across every manifest and marketplace
self-hosting-gap | the live run began under the controller it changes | acceptance uses fresh checked-in-controller fixtures and does not treat old initialization as proof of the new contract
```

## 6. Glossary seeds

- **Bug-fix step.** A runbook step containing one valid `elenchus-guard`
  block; this is a formal Fiat claim, not a guess from prose or diff content.
- **Guard declaration.** The source-bound test command, report format and
  report file inside that block.
- **Guard verdict.** Exactly `guarded`, `unguarded`, `passed` or
  `inconclusive`, with the meanings already owned by Elenchus.
- **Guard ref.** The signed implementation commit recorded by `done implement`
  and supplied to Elenchus as `--ref`.
- **Reported verdict.** A value the Warden says Elenchus returned. Fiat checks
  its shape and source relation; it does not independently rerun the command.
- **Legacy step.** A receipted step from before this contract, with no formal
  guard declaration and no guard verdict owed.

## 7. Sources

- Issue #327: <https://github.com/wildcat-finance/skills/issues/327>.
- Dependent issue #429: <https://github.com/wildcat-finance/skills/issues/429>.
- Elenchus contract and checker:
  `plugins/hexaemeron/skills/elenchus/SKILL.md`,
  `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py`, and
  `plugins/hexaemeron/tests/test_elenchus_checker.py`.
- Fiat contract, controller and role:
  `plugins/hexaemeron/skills/fiat/SKILL.md`,
  `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
  `plugins/hexaemeron/skills/fiat/references/audit-loop.md`,
  `plugins/hexaemeron/agents/warden.md`,
  `plugins/hexaemeron/tests/test_hexctl.py`, and
  `plugins/hexaemeron/tests/test_fiat_skill.py`.
- Version law and ledgers: `plugins/hexaemeron/skills/VERSIONING.md`,
  `plugins/hexaemeron/skills/elenchus/EVOLUTION.md`, and
  `plugins/hexaemeron/skills/fiat/EVOLUTION.md`.
- Current audit records: `audit/AUDIT.md` and
  `plugins/hexaemeron/audit/AUDIT.md`.
- Merged change records: PRs
  [#195](https://github.com/wildcat-finance/skills/pull/195),
  [#206](https://github.com/wildcat-finance/skills/pull/206),
  [#207](https://github.com/wildcat-finance/skills/pull/207),
  [#288](https://github.com/wildcat-finance/skills/pull/288),
  [#426](https://github.com/wildcat-finance/skills/pull/426),
  [#444](https://github.com/wildcat-finance/skills/pull/444), and
  [#445](https://github.com/wildcat-finance/skills/pull/445).
- Suite law: `PROMISE_MACHINE.md`; specification contract:
  `plugins/hexaemeron/skills/protasis/SKILL.md`; prose gate:
  `plugins/hexaemeron/skills/imprimatur/SKILL.md`.

## 8. Signals, and the questions behind them

The controller is local and does not add an unattended service, metric or
alert. It still needs inspectable state for resumption. “Does this round owe a
guard verdict?” is answered by `next` naming `--guard-status` and by the guard
object in the Warden brief. “Which command and commit does it describe?” is
answered by the runbook SHA-256, command SHA-256 and guard ref in that object.
“What did the Warden report?” is answered by the structured round field in
state and the hash-chained ledger transition. “Why did reconstruction stop?”
is answered by a named missing, malformed, ambiguous or drifted-source refusal.
No new telemetry is warranted; [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md)
remains the owner if this becomes an unattended path later.

## 9. Boundaries, per capability

Runbook parsing reads untrusted Markdown under existing size, path and digest
limits. The new parser selects only the exact step and one top-level block;
fenced decoys, duplicates and changed bytes refuse. Test execution crosses a
subprocess and filesystem boundary, but the capability stays inside existing
Elenchus: `shlex` parsing, argv execution without a shell, one substituted
report path, a timeout, a detached parent worktree and bounded report and
diagnostic reads. The Warden-to-controller boundary accepts a reported enum,
not raw output. The controller records only the enum, source digests and ref.
Repository mutation stays inside the existing signed Fiat stack. See
[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) for the controls owned by
those boundaries.

## 10. The budget, or its absence

There is no performance claim and therefore no Metron before-and-after budget.
The implementation must preserve the existing bounded source reads and
Elenchus timeout. The relevant acceptance is functional and is measured by the
focused and full test commands in item 1, not by elapsed-time improvement. See
[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) if a later change is
proposed for speed.

## 11. The fail-closed posture

A malformed, duplicate, ambiguous, missing-after-declaration or digest-drifted
guard source stops packet construction. A declared bug-fix step without
`--guard-status`, an unknown status, or a status supplied for an ordinary step
stops the audit receipt. Elenchus's own missing, stale, mixed, empty or unsafe
report cases remain `inconclusive`; Fiat preserves that value and never turns
it into `guarded`. Red-before-fix tests cover every new refusal and all four
accepted values, while the existing Elenchus fixtures remain the guard for
classification. See [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md)
for the triage and guard rules.

## 12. Decisions and their homes

The formal runbook block, Warden packet field and receipt semantics are an
interface that later issues will consume. Record the reason and rejected
sidecar and inference options in
`docs/decisions/ADR-012-bind-fiat-guard-verdicts-to-runbook-source.md` and keep
the operating rule in `plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/audit-loop.md` and
`plugins/hexaemeron/agents/warden.md`. Elenchus keeps the verdict meanings in
its own `SKILL.md`; Fiat cites rather than restates them.

The Elenchus skill moves from `elenchus-v1.1.0` to `elenchus-v1.2.0` on the
generation axis while retaining frontier status `mature`, revision
`observed-failure-root-cause` and digest
`08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`
byte for byte. Fiat moves from `fiat-v5.10.1` to `fiat-v5.11.1` on the
generation axis while retaining revision `state-shape-validation`, its held
issue #363 target and digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`
byte for byte. Hexaemeron package publication moves from `1.5.4` to `1.5.5`
across every manifest and marketplace so installations can receive the new
controller. Promise Machine bindings and the Horos boundary are regenerated
only where their governed bytes require it. See
[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) for record
placement.

Unknowns left visible: the runbook has not yet selected the repository-owned
report emitter used for this delivery's own guard declaration, and the runbook
must name that exact command before implementation. No evidence supports
turning non-`guarded` values into a controller halt in #327; that policy remains
deferred to #453.
