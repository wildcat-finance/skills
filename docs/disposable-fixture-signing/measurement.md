# Measurement: isolating disposable fixture signing

The before and after that acceptance item 4 requires for issue
[#621](https://github.com/wildcat-finance/skills/issues/621), taken at the run
head on 2026-08-28. Two measurements are recorded. M1 is the construction path,
where the claim lives. M2 is suite wall time, recorded for completeness and
reported without a speedup claim.

Every number below was taken on one machine, and the host section says which.
Nothing here is a universal figure, and the section on the issue's own numbers
says why they are not reproduced.

## Host

An Apple M4 Max with 16 cores and 64 GiB, running macOS 26.6.2 on Darwin 25.6.0
arm64, with git 2.54.0 and the interpreter pinned in `.python-version`, resolved
on this host as `/Users/kethcode/.local/bin/python3.14`. The Hexaemeron suite
runs under Node 26.6.0, supplied by `npx --yes --package=node@26.6.0`.

The signing configuration these numbers were taken under is `commit.gpgsign`
set to `true`, `gpg.format` set to `ssh`, and `user.signingkey` set to
`/Users/kethcode/.ssh/id_ed25519_github.pub`.

This contributor signs with SSH, so there is no pinentry and no stall. The
fixture commit succeeds and carries a real personal signature. That is the
quieter of the two forms of the fault the study records, and it is the only form
this host can measure.

The before arm is a detached worktree at `f5d94a5f`, which is the study's base
ref and also the merge-base of this delivery with `origin/main`, so the two arms
differ by this delivery's own commits and nothing else. The after arm is the run
head.

## M1: the construction path

Twenty fixture commits into a disposable repository, three samples per arm, wall
time divided by twenty. The signed arm inherits the host's real signing
configuration. The unsigned arm declares `commit.gpgsign false` in its own local
config, which is the rule this delivery applies.

| Arm | Sample 1 | Sample 2 | Sample 3 | Mean | Within-arm range |
| --- | --- | --- | --- | --- | --- |
| signed | 21.3 | 21.6 | 21.3 | 21.40 | 0.3 |
| unsigned | 16.6 | 16.9 | 16.8 | 16.77 | 0.3 |
| difference | 4.7 | 4.7 | 4.5 | 4.63 | 0.2 |

All figures are milliseconds per commit. The two arms ran as two sequences
rather than as paired trials, so the difference row is the gap between
same-numbered samples; its mean is the same 4.63 ms that the two arm means give.

The largest within-arm range is 0.3 ms and the improvement is 4.6 ms, so the
improvement exceeds the measured spread by a factor of 15. Acceptance item 4 is
met, and it is met here rather than anywhere else in this record.

Each arm was checked to be what it claims. The last commit of every signed
sample carries a `gpgsig` header and reads `G` under `%G?`; the last commit of
every unsigned sample carries no such header and reads `N`. Without that check
the two arms could differ for some reason other than signing.

The study recorded the same loop at the base ref: 25.6, 25.5 and 25.5 ms per
commit signed against 20.3, 20.5 and 20.1 unsigned, a spread of at most 0.4 ms
and an improvement of 5.2 ms. Both arms are faster at the run head than they
were when the study ran, which is a property of the machine on the day rather
than of the change. The improvement is 4.6 ms here against 5.2 ms there, and
both exceed their own spread by more than an order of magnitude.

## M2: suite wall time

Three samples of each of the four suite commands in each arm, under the
contributor's real configuration rather than under any override. Samples were
interleaved, one after-arm run followed by the matching before-arm run, so that
any drift in machine conditions falls on both arms alike. All 24 runs exited 0.

A delta counts as inside variance when its magnitude does not exceed the larger
of the two arms' own within-arm ranges. That criterion is stated here rather
than chosen after seeing the numbers.

| Suite | Before (s) | After (s) | Before mean | After mean | Delta | Spread | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| root | 33.45, 31.82, 32.92 | 34.47, 34.21, 35.04 | 32.73 | 34.57 | +1.84 | 1.63 | outside the spread, see below |
| hermes | 13.60, 13.46, 14.25 | 13.64, 13.49, 14.27 | 13.77 | 13.80 | +0.03 | 0.79 | inside variance |
| hexaemeron | 463.24, 497.48, 506.68 | 460.75, 471.04, 509.20 | 489.13 | 480.33 | -8.80 | 48.45 | inside variance |
| horos | 2.79, 3.44, 3.41 | 2.74, 3.23, 3.35 | 3.21 | 3.11 | -0.11 | 0.65 | inside variance |

Three of the four suites show a delta inside variance, in those words. No
suite-level speedup is claimed on this host and acceptance item 4 is not
satisfied from M2. The arithmetic behind that expectation is in the study: a
handful of fixture commits at 4.6 ms each is tens of milliseconds against suite
times measured in seconds and minutes.

The root suite is the exception and it is not a speedup or a regression. The two
arms do not run the same work: the before arm runs 462 tests and the after arm
runs 482, because this delivery added `tests/test_disposable_fixture_signing.py`
and `tests/test_root_elenchus_runner.py` to that suite. At the before arm's rate
of 70.8 ms per test, twenty extra tests account for 1.42 s of the observed
1.84 s, and the residual 0.42 s sits inside the before arm's own 1.63 s range.
A same-command comparison is what item 4 asks for, and for this suite the
command is the same while the work behind it is not, so no timing conclusion is
drawn from it.

One condition worth stating: about two seconds of unrelated document linting ran
on the same machine during the first after-arm Hexaemeron sample. Against a
460 s run on sixteen cores that is under half a percent, and it does not change
any verdict above, but a reader comparing these numbers to their own should know
the machine was not otherwise idle.

## The issue's own figures, and why they are not repeated

Issue #621 recorded 188.38 seconds for the root suite against 6.91 seconds for
the same 118 tests, at revision `e4d1f5677fa1`. That was a contributor signing
with GPG, where a non-interactive fixture commit waits on a pinentry prompt
nobody answers, so the pair measures the difference between failing and working
rather than a speedup. It was also a different revision on a machine this
delivery does not have.

Those figures stand as the record of what the fault costs a GPG contributor.
They are not reproduced here and no claim in this delivery rests on them.

## What acceptance item 4 rests on

M1, and only M1. Three samples per arm of the same command, a spread of 0.3 ms,
an improvement of 4.6 ms, and the improvement exceeding the spread by a factor
of 15.

The correctness result that carries acceptance items 1 and 5 is not a timing
result. Under a hostile global configuration supplied as a file, the four suite
commands leave a sentinel that records a verification and records no request to
sign. That pairing is checked by the runbook's step 5 exit rather than here.

`docs/decisions/ADR-046-declare-signing-policy-on-disposable-git-fixtures.md`
carries a third measured result, the injection-precedence table, which decides
how a guard must supply its hostile configuration. It is recorded there because
it constrains the rule rather than the budget.
