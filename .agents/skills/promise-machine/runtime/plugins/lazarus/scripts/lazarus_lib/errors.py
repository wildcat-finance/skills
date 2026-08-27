"""Errors raised at Lazarus trust boundaries."""


class LazarusError(Exception):
    """Base class for a user-visible Lazarus failure."""


class FormatError(LazarusError):
    """A JSON document or record does not match the selected format."""


class PathError(LazarusError):
    """A fixture path is unsafe or escapes its fixture root."""


class IntegrityError(LazarusError):
    """Fixture bytes do not match their manifest claim."""


class ResourceLimitError(LazarusError):
    """Input exceeds a declared or built-in resource limit."""
