"""Market control observations admitted only by the versioned control profile."""

DECLARATIONS = (
    ("approval", "Approval(address,address,uint256)",
     (("owner", "address", True), ("spender", "address", True), ("value", "uint256", False)),
     (("pool", None), ("allowance-owner", "owner"), ("allowance-spender", "spender"))),
    ("spherex-engine-updated", "ChangedSpherexEngineAddress(address,address)",
     (("oldEngineAddress", "address", False), ("newEngineAddress", "address", False)), (("pool", None),)),
    ("spherex-operator-updated", "ChangedSpherexOperator(address,address)",
     (("oldSphereXAdmin", "address", False), ("newSphereXAdmin", "address", False)), (("pool", None),)),
)

CONTROL_RULES = {}
for _venue in ("wildcat-v1", "wildcat-v2"):
    for _suffix, _signature, _fields, _parties in DECLARATIONS:
        CONTROL_RULES[(_venue, _suffix)] = {
            "venue": _venue, "role": "market", "action": _venue + "." + _suffix,
            "family": "pool-state", "signature": _signature,
            "rule": _venue + "." + _suffix + ".v1",
            "fields": tuple(field[0] for field in _fields), "declared_fields": _fields,
            "party_fields": _parties, "party_roles": tuple(role for role, _ in _parties),
            "amount_kinds": (), "instrument_type": _venue + "-market",
            "control_observation": True,
        }
