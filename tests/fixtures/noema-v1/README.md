# Noema version 1 fixtures

This tree holds the shadow prototype's bounded evidence. None of it is a
selectable skill or authority source.

`seed-inventory.json` binds the public #942 attachment before any reference
file is imported. Step 1 verifies the ZIP in place and does not extract or
execute it. Later steps add canonical codec fixtures, runtime fixtures,
byte-identical non-executable seed references, reviewed source bindings,
mutations, profiles and evidence under their named directories.

Run the current boundary with:

```bash
python3 scripts/noema.py verify-seed \
  --archive /private/tmp/noema-v0-evidence.zip \
  --inventory tests/fixtures/noema-v1/seed-inventory.json
```

The local path is operator state. The public attachment URL and every expected
digest live in the inventory, so another operator can download the exact bytes
and verify them without trusting this checkout's temporary directory.
