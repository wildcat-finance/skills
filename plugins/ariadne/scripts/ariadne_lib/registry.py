"""The predicate registry: a type URI to the module that understands it.

The registry is the reason the core can stay artefact-neutral. A predicate
module owns its own field table and its own checks, and the core knows only how
to find it and what to ask of it. Adding a predicate costs a module and a
registration, which is what the dataset and state-fixture predicates each cost.

Five are registered: the Solidity release, the dataset, the grounded-agent
release and the two explicitly versioned state-fixture predicates.
`ariadne predicates`
lists whatever is there rather than a table somebody maintains. An unknown
predicate type is reported rather than raised: a verifier that meets a type it
does not know can still check the core gates, and should say which part it could
not check.
"""

REQUIRED_ATTRIBUTES = ("TYPE", "SUMMARY")

OPTIONAL_INTERFACE = ("check", "EXPECTED_RESULTS")
"""`check(statement)` returns the predicate's own gates. `EXPECTED_RESULTS`
declares their complete ordered `(number, name)` set. A module without a check
is registered and the verifier reports gates 2 and 5 as unchecked; a module
without the declaration retains the legacy check interface."""


class RegistryError(ValueError):
    """A predicate that cannot be registered."""


class Registry(object):
    def __init__(self):
        self._modules = {}

    def register(self, module):
        for attribute in REQUIRED_ATTRIBUTES:
            if not getattr(module, attribute, None):
                raise RegistryError(
                    "predicate module %r has no %s" % (module, attribute)
                )
        type_uri = module.TYPE
        if not isinstance(type_uri, str) or ":" not in type_uri:
            raise RegistryError("predicate TYPE must be a type URI, got %r" % (type_uri,))
        if type_uri in self._modules and self._modules[type_uri] is not module:
            raise RegistryError("predicate type %s is already registered" % type_uri)
        self._modules[type_uri] = module
        return module

    def get(self, type_uri):
        """The module for this type, or None. Never raises on an unknown type."""
        return self._modules.get(type_uri)

    def knows(self, type_uri):
        return type_uri in self._modules

    def entries(self):
        """Sorted (type URI, summary) pairs."""
        return sorted(
            (type_uri, module.SUMMARY) for type_uri, module in self._modules.items()
        )

    def __len__(self):
        return len(self._modules)


DEFAULT = Registry()
"""The registry the CLI reads. Predicate modules register themselves into it."""
