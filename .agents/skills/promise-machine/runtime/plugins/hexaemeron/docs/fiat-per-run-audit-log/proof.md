# Proof: a run writes to a record no other run writes

The demonstration the [study](study.md) named, run against the tree this file
ships in, by the controller this run changed rather than the one driving it.

That distinction matters. A Fiat change cannot take effect for the run that
makes it: the controller driving a run is whichever one was installed when it
started, which here is `fiat-v5.20.1`. So the transcript below comes from a
scratch run in a temporary repository, driven by
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` as this branch holds it.

Reproduce it with the script the run used, which creates its own repository and
leaves nothing behind:

```bash
git init -q -b main /tmp/fiat-576-demo && cd /tmp/fiat-576-demo
git commit -q --allow-empty -m base
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py --dir /tmp/fiat-576-demo \
  init --task-issue https://github.com/wildcat-finance/skills/issues/576 \
  --topic "demonstrate the derived audit log" --base main
```

The run this delivery made is the second demonstration. It set
`config audit.log_path` before its first round, under the old controller, which
accepts any string. Every one of its ten rounds is in
`audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md`, and
`git diff` over `audit/AUDIT.md` against the run branch removes no line.

## 1. A run derives its own record at init, with no operator action

```text
$ hexctl config get audit.log_path
"audit/rounds/fiat-576-demonstrate-the-derived-audit-log.md"
```

## 2. The directive names that file, so a caller is told before it is refused

```text
$ hexctl next
{
 "do": "audit-round",
 "step": 1,
 "round": 1,
 "log_path": "audit/rounds/fiat-576-demonstrate-the-derived-audit-log.md"
}
```

## 3. A round naming that file is recorded

```text
$ hexctl audit-round --findings 0 \
    --log audit/rounds/fiat-576-demonstrate-the-derived-audit-log.md \
    --audit-filter sapheneia:sapheneia \
    --phylax-exit 0 --ephoros-exit 0 --hypomnema-exit 0
step 1 audit round 1 recorded (0 finding(s)); lints phylax 0, ephoros 0,
hypomnema 0; audit filter sapheneia:sapheneia; Elenchus null
```

## 4. A round naming another file is refused, and records nothing

```text
$ hexctl audit-round --findings 0 --log audit/AUDIT.md \
    --audit-filter sapheneia:sapheneia \
    --phylax-exit 0 --ephoros-exit 0 --hypomnema-exit 0
hexctl: error: --log names 'audit/AUDIT.md', but this round writes
'audit/rounds/fiat-576-demonstrate-the-derived-audit-log.md'
(config audit.log_path); a receipt naming a file nothing opened is worse than a
receipt naming none

$ hexctl status | grep round
audit: 1 round(s), last findings: 0
```

One round on the ledger, not two. The refusal happens before anything is
appended.

## 5. A round with no declaration records the configured path anyway

```text
$ hexctl audit-round --findings 0 --audit-filter sapheneia:sapheneia \
    --phylax-exit 0 --ephoros-exit 0 --hypomnema-exit 0
step 1 audit round 2 recorded (0 finding(s)); ...

$ python3 -c "read the two recorded logs out of state"
 round 1 -> audit/rounds/fiat-576-demonstrate-the-derived-audit-log.md
 round 2 -> audit/rounds/fiat-576-demonstrate-the-derived-audit-log.md
```

The field is no longer a free string. It says the same thing whether the caller
declared it or not.

## 6. The override moves the directory; it cannot take another record's name

```text
$ hexctl config set audit.log_path \
    "plugins/hexaemeron/audit/rounds/fiat-576-demonstrate-the-derived-audit-log.md"
set audit.log_path

$ hexctl config set audit.log_path "audit/AUDIT.md"
hexctl: error: config audit.log_path must end in
'fiat-576-demonstrate-the-derived-audit-log.md', the record this run owns; got
'audit/AUDIT.md'. Move the directory if you need to; the name is what keeps two
runs out of one file.

$ hexctl config set audit.log_path "audit/rounds/fiat-999-somebody-elses-run.md"
hexctl: error: config audit.log_path must end in
'fiat-576-demonstrate-the-derived-audit-log.md', ...

$ hexctl config set audit '{"max_rounds": 8, "stacked_suffix": "--audit",
    "fold": false, "log_path": "audit/AUDIT.md"}'
hexctl: error: config audit.log_path must end in
'fiat-576-demonstrate-the-derived-audit-log.md', ...

$ hexctl config get audit.log_path
"plugins/hexaemeron/audit/rounds/fiat-576-demonstrate-the-derived-audit-log.md"
```

The last of the four is the one step 2's first audit round found: writing the
whole `audit` section reaches the same field, so it meets the same check.

## What this does not show

The transcript establishes what the controller does with a path. It does not
establish that a round wrote anything to that file, because the controller never
opens it and does not attest its bytes. That was true before this change and is
true after it. What changed is that the path a receipt names is the path the
round was told to write, rather than whatever string a caller passed.

Nor does it show the sync gate no longer asking for a check over the record.
That needs a base that advanced during a run, which this run has and the
scratch run does not. This delivery's own integration is where that is visible:
`audit/AUDIT.md` is in its overlap set once, for the one-time pointer step 4
appended, and never again.
