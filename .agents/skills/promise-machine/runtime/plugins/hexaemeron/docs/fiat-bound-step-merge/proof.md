# Proof: the loop notices a stack merged out of order

The demonstration the [study](study.md) named, run against the tree this file
ships in, by the controller this run changed rather than the one driving it.

Both faults only exist in the integrate phase, which needs a pushed stack and a
GitHub that answers. So the transcript drives the real controller with the same
fake `git` and `gh` the Hexaemeron suite uses, rather than a bare scratch
repository: everything below is `hexctl`'s own output, with the delivery tools
standing in for GitHub and nothing else changed.

Reproduce it from the tests directory:

```bash
cd plugins/hexaemeron/tests
python3 -m unittest test_stack_topology
```

That runs eighteen cases over the same fixture. The transcript below is the same
fixture driven by hand so the messages are visible.

## 1. The directive carries the command that merges the one it names

```text
$ hexctl next
{
 "do": "merge-step",
 "step": 1,
 "pr_url": "https://github.com/wildcat-finance/example/pull/1",
 "merge": "gh pr merge https://github.com/wildcat-finance/example/pull/1 --merge",
 "then": "hexctl done merge-step --step 1 --merge-commit <sha>"
}
```

Built from the URL rather than a number and a repository flag, so nothing has to
be transcribed. This is the half of the fix that removes the mistyped command.

## 2. Merging in order works, and the guard is invisible

```text
$ hexctl done merge-step --step 1 --merge-commit 1111...
step 1 merged into fiat/test-topic; 2 step(s) left in the stack
```

A run that does the right thing sees no difference. The whole Hexaemeron suite
passes with the guard live, which is the wider version of this line.

## 3. Something else merges into the run branch

```text
$ hexctl next
hexctl: error: the run branch 'fiat/test-topic' is at 9999999999999999999999999999999999999999
and this run's last receipt names 1111111111111111111111111111111111111111.
Something merged into the run branch that this run did not receipt. A stack
chains, so the topmost step branch holds every commit in the run and merging the
wrong pull request lands all of them at once. There is no repair from here: a
skipped step's pull request cannot be retargeted onto a branch its head already
sits in, and cannot merge into a base it is an ancestor of. Merge each step's
pull request by the number the directive names, one at a time. If this has
already happened, halt the run with the reason and finish by hand; do not receipt
a merge the loop did not make.
```

This is the directive immediately after the mistake, which is the only point
where anything can still be done. Before this run it arrived three steps later,
as a topology mismatch, with the repair window already closed.

## 4. `status` reports it rather than refusing

```text
$ hexctl status
phase: integrate (1/3 steps merged into fiat/test-topic)
STACK: the run branch 'fiat/test-topic' is at 99999999... and this run's last
receipt names 11111111...
```

`status` is what somebody runs to find out what is wrong, so it answers. An
unreadable remote reports the question as unknown here and refuses at the
receipt, where a wrong answer would be acted on.

## 5. The receipt refuses too

```text
$ hexctl done merge-step --step 2 --merge-commit 2222...
hexctl: error: the run branch 'fiat/test-topic' is at 99999999... and this run's
last receipt names 11111111... [same message]
```

Belt and braces. The receipt already checks the pull request it is recording; this
catches the branch underneath it.

## What this does not show

It does not show the fault being prevented, because nothing here can stop a person
merging a pull request. What changed is that the loop hands over the command
rather than a number to retype, and notices within one directive when something
merged that it did not ask for.

It does not cover retarget drift, where a waiting step's pull request base is
changed away from the run branch. That still refuses at the step's own receipt
rather than at the directive before it, and step 3's round records why.

And it does not establish that a run in this state can be recovered. It cannot;
that is the finding. The refusal says so rather than implying a repair exists.
