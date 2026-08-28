"""in-toto Statement v1, built and parsed.

The structure is borrowed rather than invented: `_type`, `subject`,
`predicateType`, `predicate`, exactly as in-toto defines them. What this module
adds is refusal. A subject without a digest, a predicate type that is not a URI,
or a predicate that is not an object are all things a JSON parser accepts and a
verifier should not.

Subjects match by digest. The `name` field distinguishes entries for a reader
and carries no authority, so `subject_for` takes a digest set and never a name.
"""

import json

from . import digests, safejson

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
TYPE_FIELD = "_type"

FIELDS = frozenset({TYPE_FIELD, "subject", "predicateType", "predicate"})
"""Statement v1 is exactly these. Extensions belong in the predicate."""


class StatementError(ValueError):
    """A parsed object that is not a statement this tool will act on."""


DESCRIPTOR_FIELDS = frozenset(
    {
        "name",
        "uri",
        "digest",
        "content",
        "downloadLocation",
        "mediaType",
        "annotations",
    }
)
"""in-toto ResourceDescriptor v1. A subject outside this shape is refused."""


class Subject(object):
    """One digested artefact a statement is about.

    The descriptor fields this tool does not act on are carried rather than
    dropped. A subject arrives inside signed bytes, and re-emitting it without
    its `uri` or its annotations would hand on a different document from the
    one that was signed.
    """

    def __init__(self, digest, name=None, extra=None):
        self.digest = digests.check(digest)
        if name is not None and not isinstance(name, str):
            raise StatementError("subject name must be a string when present")
        self.name = name
        self.extra = dict(extra or {})

    @classmethod
    def from_dict(cls, raw):
        if not isinstance(raw, dict):
            raise StatementError("each subject must be an object")
        label = raw.get("name", "<unnamed>")
        unknown = sorted(set(raw) - DESCRIPTOR_FIELDS)
        if unknown:
            raise StatementError(
                "subject %r carries fields a ResourceDescriptor does not "
                "define: %s" % (label, ", ".join(unknown))
            )
        if "digest" not in raw:
            raise StatementError(
                "subject %r has no digest; in-toto requires one on every subject"
                % label
            )
        try:
            return cls(
                raw["digest"],
                raw.get("name"),
                {k: v for k, v in raw.items() if k not in ("name", "digest")},
            )
        except digests.DigestError as error:
            raise StatementError("subject %r: %s" % (label, error))

    def to_dict(self):
        out = {}
        if self.name is not None:
            out["name"] = self.name
        out["digest"] = dict(self.digest)
        for key in sorted(self.extra):
            out[key] = self.extra[key]
        return out

    def __repr__(self):
        return "Subject(%s, name=%r)" % (digests.short(self.digest), self.name)


class Statement(object):
    def __init__(self, subjects, predicate_type, predicate=None):
        if not subjects:
            raise StatementError("a statement covers at least one subject")
        self.subjects = list(subjects)
        if not isinstance(predicate_type, str) or ":" not in predicate_type:
            raise StatementError(
                "predicateType must be a type URI, got %r" % (predicate_type,)
            )
        self.predicate_type = predicate_type
        if predicate is not None and not isinstance(predicate, dict):
            raise StatementError("predicate must be an object when present")
        self.predicate = predicate

    @classmethod
    def from_dict(cls, raw):
        if not isinstance(raw, dict):
            raise StatementError("a statement is a JSON object")
        found = raw.get(TYPE_FIELD)
        if found != STATEMENT_TYPE:
            raise StatementError(
                "_type is %r, expected %r" % (found, STATEMENT_TYPE)
            )
        unknown = sorted(set(raw) - FIELDS)
        if unknown:
            # A field the statement shape does not define is a field this
            # verifier will not show and some other consumer might act on.
            # Refusing keeps the two readings of one signed document together.
            raise StatementError(
                "statement carries fields Statement v1 does not define: %s"
                % ", ".join(unknown)
            )
        subject = raw.get("subject")
        if not isinstance(subject, list) or not subject:
            raise StatementError("subject must be a non-empty array")
        return cls(
            [Subject.from_dict(entry) for entry in subject],
            raw.get("predicateType"),
            raw.get("predicate"),
        )

    @classmethod
    def from_json(cls, data, loader=None):
        """Parse statement bytes. Accepts bytes or str.

        `loader` is the bounded parser from `safejson` by default. A caller
        passing its own takes responsibility for the bounds.
        """
        if loader is None:
            loader = safejson.loads
        if isinstance(data, str):
            data = data.encode("utf-8")
        try:
            return cls.from_dict(loader(data))
        except safejson.InputError:
            raise
        except ValueError as error:
            if isinstance(error, StatementError):
                raise
            raise StatementError("statement is not valid JSON: %s" % error)
        except RecursionError:
            raise StatementError("statement is nested too deeply to parse")

    def to_dict(self):
        out = {
            "_type": STATEMENT_TYPE,
            "subject": [entry.to_dict() for entry in self.subjects],
            "predicateType": self.predicate_type,
        }
        if self.predicate is not None:
            out["predicate"] = self.predicate
        return out

    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    def subject_for(self, digest):
        """The first subject agreeing with this digest set, or None.

        Takes a digest set rather than a name on purpose: in-toto matches
        subjects by digest, and a verifier that matched by name would accept a
        claim pointing at a label instead of at bytes.
        """
        digest = digests.check(digest)
        for entry in self.subjects:
            if digests.agree(entry.digest, digest):
                return entry
        return None

    def covers(self, digest):
        return self.subject_for(digest) is not None

    def __repr__(self):
        return "Statement(%d subjects, %s)" % (len(self.subjects), self.predicate_type)
