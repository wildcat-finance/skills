"""Berean: evidence-backed protocol-agent releases.

Every module here reads untrusted documents, so the shared posture is
refusal: wrong hex case, a float, a duplicate key, a symlink or a path that
leaves its tree are errors, never normalised. `BereanError` is the one
domain error; the CLI turns it into exit status 2, and a named check that
fails into exit status 1.
"""


class BereanError(Exception):
    """A document or argument berean refuses to work with."""
