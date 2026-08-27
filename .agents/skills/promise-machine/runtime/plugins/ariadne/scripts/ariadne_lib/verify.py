"""Verification: the core gates, the signature state, and what went unchecked.

A report says three things. Whether each core gate held. What is known about
the signatures, which is never that they were checked, because this tool does
not check them. And which gates belong to a predicate this build does not know,
so a reader is told what was not looked at rather than left to assume it was
clean.
"""

from . import gates as gates_module
from . import registry as registry_module


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
        return out

    def to_dict(self):
        return {
            "predicateType": self.statement.predicate_type,
            "predicateTypeKnown": self.predicate_module is not None,
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
    found = gates_module.run(statement)
    module = registry.get(statement.predicate_type)

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
                gates_module.Gate(
                    None,
                    "predicate-check",
                    False,
                    "%s raised while checking: %s"
                    % (statement.predicate_type, error),
                )
            ]
            ran = True
        else:
            stray = [entry for entry in added if not isinstance(entry, gates_module.Gate)]
            if stray:
                added = [
                    gates_module.Gate(
                        None,
                        "predicate-check",
                        False,
                        "%s returned something that is not a gate"
                        % statement.predicate_type,
                    )
                ]
            ran = bool(added)
        found.extend(added)

    return Report(document, found, module, ran)
