"""Verification: the core gates, the signature state, and what went unchecked.

A report says three things. Whether each gate that ran held. What is known
about the signatures, which is never that they were checked, because this tool
does not check them. And which predicate-owned gates did not run, whether the
type is unknown or a registered module is incomplete, so a reader is told what
was not looked at rather than left to assume it was clean.
"""

from . import gates as gates_module
from . import registry as registry_module


def _predicate_failure(predicate_type, detail):
    return gates_module.Gate(
        None,
        "predicate-check",
        False,
        "%s %s" % (predicate_type, detail),
    )


def _exception_text(error):
    try:
        return str(error)
    except Exception:  # noqa: BLE001 -- diagnostics must not replace the first failure
        return "<unprintable %s>" % type(error).__name__


def _validated_predicate_gates(predicate_type, entries):
    """Snapshot one module's gates only after their shared shape is sound."""
    found = []
    for entry in entries:
        if not isinstance(entry, gates_module.Gate):
            return [
                _predicate_failure(
                    predicate_type,
                    "returned something that is not a gate",
                )
            ]
        try:
            number = entry.number
            name = entry.name
            passed = entry.passed
            detail = entry.detail
        except Exception:  # noqa: BLE001 -- a broken module remains a failed check
            return [
                _predicate_failure(predicate_type, "returned a malformed gate")
            ]
        if (
            number is not None
            and (
                type(number) is not int
                or number not in gates_module.PREDICATE_GATES
            )
        ):
            return [
                _predicate_failure(predicate_type, "returned a malformed gate")
            ]
        if (
            type(name) is not str
            or type(passed) is not bool
            or type(detail) is not str
        ):
            return [
                _predicate_failure(predicate_type, "returned a malformed gate")
            ]
        # Copy the fields into the verifier's Gate class. A module-provided
        # subclass cannot then change how the report orders or renders it.
        found.append(gates_module.Gate(number, name, passed, detail))
    return found


class Report(object):
    def __init__(self, document, gates, predicate_module, predicate_ran=False):
        self.document = document
        self.gates = gates
        self.predicate_module = predicate_module
        self.predicate_ran = predicate_ran

    @property
    def statement(self):
        return self.document.statement

    @property
    def ok(self):
        return all(gate.passed for gate in self.gates)

    @property
    def missing_predicate_gates(self):
        """Predicate-owned gate numbers absent from this report."""
        found = {gate.number for gate in self.gates}
        return tuple(
            number
            for number in gates_module.PREDICATE_GATES
            if number not in found
        )

    @property
    def predicate_gates_checked(self):
        """Whether a registered predicate reported both gates it owns."""
        return self.predicate_module is not None and not self.missing_predicate_gates

    @property
    def ordered(self):
        """Numbered gates in order, then the checks that carry no number.

        The core gates run first and the predicate's arrive after, so without
        this the report reads 1, 3, 4, 6, 7, 2, 5, which invites a reader to
        wonder what happened to gate 2.
        """
        return sorted(self.gates, key=lambda gate: (gate.number is None, gate.number or 0))

    @property
    def unchecked(self):
        """What this run did not check, as lines to print rather than omit."""
        out = []
        numbers = " and ".join(str(n) for n in gates_module.PREDICATE_GATES)
        if self.predicate_module is None:
            out.append(
                "gates %s belong to the predicate and were not checked: %s is "
                "not registered here" % (numbers, self.statement.predicate_type)
            )
        elif not self.predicate_ran:
            # Registered is not the same as checked. A predicate module that
            # exposes no checks would otherwise pass in silence, which is the
            # exact shape of thing gate 3 exists to refuse.
            out.append(
                "gates %s were not checked: %s is registered but exposes no "
                "checks" % (numbers, self.statement.predicate_type)
            )
        elif self.missing_predicate_gates:
            missing = " and ".join(str(n) for n in self.missing_predicate_gates)
            singular = len(self.missing_predicate_gates) == 1
            out.append(
                "%s %s %s not checked: %s is registered but did not report %s"
                % (
                    "gate" if singular else "gates",
                    missing,
                    "was" if singular else "were",
                    self.statement.predicate_type,
                    "it" if singular else "them",
                )
            )
        if self.document.signed:
            out.append(
                "signatures were not checked; run cosign verify-attestation "
                "for that"
            )
        return out

    def lines(self):
        out = [
            "predicate type: %s (%s)"
            % (
                self.statement.predicate_type,
                "registered" if self.predicate_module else "not registered here",
            ),
            "signatures:     %s" % self.document.signature_state,
        ]
        out.extend(gate.line() for gate in self.ordered)
        out.extend(self.unchecked)
        return [gates_module.one_line(line) for line in out]

    def to_dict(self):
        return {
            "predicateType": self.statement.predicate_type,
            "predicateTypeKnown": self.predicate_module is not None,
            "predicateGatesChecked": self.predicate_gates_checked,
            "signatureState": self.document.signature_state,
            "gates": [gate.to_dict() for gate in self.ordered],
            "unchecked": self.unchecked,
            "ok": self.ok,
        }


def report(document, registry=None):
    """Run the core gates, then whatever the predicate module adds.

    A predicate module contributes by exposing `check(statement)`, returning
    gates of its own. Registering without one is allowed and reported: gates 2
    and 5 go on the unchecked list rather than being assumed to hold.
    """
    if registry is None:
        registry = registry_module.DEFAULT
    statement = document.statement
    module = registry.get(statement.predicate_type)
    found = gates_module.run(statement, getattr(module, "CORE_LIMITS", None))

    ran = False
    check = getattr(module, "check", None) if module is not None else None
    if callable(check):
        try:
            added = list(check(statement) or [])
        except Exception as error:  # noqa: BLE001  (see below)
            # A predicate module that raises must not take the run down with
            # it. An escaping exception exits 1, the code that means a gate was
            # breached, and buries the core gates that did run.
            added = [
                _predicate_failure(
                    statement.predicate_type,
                    "raised while checking: %s" % _exception_text(error),
                )
            ]
            ran = True
        else:
            added = _validated_predicate_gates(statement.predicate_type, added)
            ran = bool(added)
        found.extend(added)

    return Report(document, found, module, ran)
