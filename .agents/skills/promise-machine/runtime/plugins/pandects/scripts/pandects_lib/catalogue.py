"""The catalogue: what the corpus claims to contain.

A law is six things, and the catalogue is where five of them are written down.
The sixth is the Solidity, and `checker.py` is what ties the two together.

Nothing here decides whether a law is true. It decides whether something is a
law at all, which is a lower bar and the one worth enforcing mechanically: a
sentence with a hopeful name is not a law, and neither is a component nobody
can say the applicability of.
"""

from . import safejson

REQUIRED_TOP = ("version", "observables", "families", "laws")

REQUIRED_LAW = (
    "id",
    "family",
    "statement",
    "component",
    "specimen",
    "counterexample",
    "applicability",
    "bounds",
)
"""Every field a law may carry, and every one of them is required.

Absence is checked by `checker.py` rather than here, so a law missing a part is
told which part it is missing instead of being called a malformed file. Only
`id` is enforced at parse time, because without it there is nothing to name in
the message."""

REQUIRED_APPLICABILITY = ("accounting_model", "assumes", "requires")
"""Gate 3 of the specification, as fields. `assumes` and `requires` are lists so
that an empty one is a claim of no assumptions rather than an oversight."""

EXACT = "exact"


class CatalogueError(ValueError):
    """A catalogue that is not one."""


class Law(object):
    def __init__(self, raw, index):
        self.raw = raw
        self.index = index

    @property
    def id(self):
        return self.raw.get("id")

    @property
    def label(self):
        return self.id or "law %d" % (self.index + 1)

    def __getitem__(self, key):
        return self.raw[key]

    def get(self, key, default=None):
        return self.raw.get(key, default)


class Catalogue(object):
    def __init__(self, raw, path=None):
        self.raw = raw
        self.path = path
        self.laws = [Law(entry, i) for i, entry in enumerate(raw["laws"])]

    @property
    def version(self):
        return self.raw["version"]

    @property
    def families(self):
        return self.raw["families"]

    def law(self, identifier):
        for entry in self.laws:
            if entry.id == identifier:
                return entry
        return None


def parse(raw, path=None):
    """Validate the document's shape. Contents are `checker.py`'s business."""
    if not isinstance(raw, dict):
        raise CatalogueError("a catalogue is a JSON object")

    missing = [field for field in REQUIRED_TOP if field not in raw]
    if missing:
        raise CatalogueError("catalogue has no %s" % ", ".join(missing))
    if not isinstance(raw["families"], dict) or not raw["families"]:
        raise CatalogueError("families must be a non-empty object")
    if not isinstance(raw["laws"], list):
        raise CatalogueError("laws must be an array")

    seen = set()
    for index, entry in enumerate(raw["laws"]):
        label = "law %d" % (index + 1)
        if not isinstance(entry, dict):
            raise CatalogueError("%s is not an object" % label)
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise CatalogueError("%s has no id" % label)
        if identifier in seen:
            raise CatalogueError("two laws share the id %r" % identifier)
        seen.add(identifier)
        unknown = sorted(set(entry) - set(REQUIRED_LAW))
        if unknown:
            raise CatalogueError(
                "%s carries fields a law does not define: %s"
                % (identifier, ", ".join(unknown))
            )

    return Catalogue(raw, path)


def load(path):
    try:
        return parse(safejson.load_file(path), path)
    except safejson.InputError as error:
        raise CatalogueError("%s: %s" % (path, error))
