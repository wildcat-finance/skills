# wildcat-v1 constructed parameter specimen

This release exercises every required concrete wildcat-v1 parameter/access ABI
declaration from the frozen #2090 inventory under adapter `1.2.0` and schema 3.
All inputs are constructed. Repeating-byte fixture addresses and declared
contexts establish no historical occurrence, deployed code or chain boundary.

Run from the repository root:

```bash
python3 plugins/tabularium/examples/wildcat-v1-parameters-v0/rebuild.py
```

The command builds in a fresh temporary directory, verifies the complete raw
copy and canonical release, and compares every release byte with this specimen.
`release/` is a closed release root. `expected.json`, this README and
[the data dictionary](DATA_DICTIONARY.md) sit outside it.
Native fields and parties follow the [canonical guide](../../docs/wildcat-canonical.md).
