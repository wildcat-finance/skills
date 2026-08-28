"""The DSSE envelope, read and written.

A DSSE signature covers bytes, not an object. The consequence runs through this
module: the payload decoded from an envelope is kept exactly as it arrived and
never re-serialised before it is checked or shown. A verifier that re-encodes
first is checking a document its signer never saw, and may print one thing while
having checked another.

DSSE permits either base64 alphabet, so the reader accepts both and the writer
commits to the standard one. A payload mixing characters from both alphabets is
refused: it is not the output of either encoder, and guessing which was meant is
how a payload gets decoded two ways.

`ariadne` holds no key and produces no signature. It writes unsigned envelopes,
reads signed ones, and reports which it has. `cosign` signs and verifies.
"""

import base64
import json

from . import safejson
from . import statement as statement_module

PAYLOAD_TYPE = "application/vnd.in-toto+json"

STANDARD_ONLY = set("+/")
URLSAFE_ONLY = set("-_")


class EnvelopeError(ValueError):
    """An object that is not an envelope this tool will act on."""


def pae(payload_type, body):
    """Pre-authentication encoding, DSSE v1.0.0.

    PAE(type, body) = "DSSEv1" SP LEN(type) SP type SP LEN(body) SP body,
    where LEN is decimal ASCII with no leading zeros and the lengths count
    bytes rather than characters.
    """
    if isinstance(payload_type, str):
        payload_type = payload_type.encode("utf-8")
    if not isinstance(body, bytes):
        raise EnvelopeError("PAE body must be bytes")
    return b" ".join(
        [
            b"DSSEv1",
            str(len(payload_type)).encode("ascii"),
            payload_type,
            str(len(body)).encode("ascii"),
            body,
        ]
    )


def decode_base64(text, what="payload"):
    """Decode base64 in either alphabet, refusing a string that mixes them."""
    if not isinstance(text, str):
        raise EnvelopeError("%s must be a base64 string" % what)
    characters = set(text)
    if characters & STANDARD_ONLY and characters & URLSAFE_ONLY:
        raise EnvelopeError(
            "%s mixes the standard and URL-safe base64 alphabets" % what
        )
    normalised = text.replace("-", "+").replace("_", "/")
    padding = len(normalised) % 4
    if padding:
        normalised += "=" * (4 - padding)
    try:
        return base64.b64decode(normalised, validate=True)
    except (ValueError, TypeError) as error:
        raise EnvelopeError("%s is not valid base64: %s" % (what, error))


def encode_base64(data):
    return base64.b64encode(data).decode("ascii")


ENVELOPE_FIELDS = frozenset({"payload", "payloadType", "signatures"})
SIGNATURE_FIELDS = frozenset({"sig", "keyid"})


class Signature(object):
    def __init__(self, sig, keyid=None):
        self.sig = sig
        self.keyid = keyid

    @classmethod
    def from_dict(cls, raw):
        if not isinstance(raw, dict):
            raise EnvelopeError("each signature must be an object")
        unknown = sorted(set(raw) - SIGNATURE_FIELDS)
        if unknown:
            raise EnvelopeError(
                "signature carries fields DSSE does not define: %s"
                % ", ".join(unknown)
            )
        if "sig" not in raw:
            raise EnvelopeError("signature has no sig field")
        decode_base64(raw["sig"], "signature")
        keyid = raw.get("keyid")
        if keyid is not None and not isinstance(keyid, str):
            raise EnvelopeError("keyid must be a string when present")
        return cls(raw["sig"], keyid)

    def to_dict(self):
        out = {}
        if self.keyid is not None:
            out["keyid"] = self.keyid
        out["sig"] = self.sig
        return out


class Envelope(object):
    """An envelope and the exact payload bytes it carried."""

    def __init__(self, payload, payload_type=PAYLOAD_TYPE, signatures=None):
        if not isinstance(payload, bytes):
            raise EnvelopeError("payload must be bytes")
        if not isinstance(payload_type, str) or not payload_type:
            raise EnvelopeError("payloadType must be a non-empty string")
        self.payload = payload
        self.payload_type = payload_type
        self.signatures = list(signatures or [])

    @classmethod
    def from_dict(cls, raw):
        if not isinstance(raw, dict):
            raise EnvelopeError("an envelope is a JSON object")
        unknown = sorted(set(raw) - ENVELOPE_FIELDS)
        if unknown:
            raise EnvelopeError(
                "envelope carries fields DSSE does not define: %s" % ", ".join(unknown)
            )
        for field in ("payload", "payloadType"):
            if field not in raw:
                raise EnvelopeError("envelope has no %s field" % field)
        signatures = raw.get("signatures", [])
        if not isinstance(signatures, list):
            raise EnvelopeError("signatures must be an array")
        return cls(
            decode_base64(raw["payload"]),
            raw["payloadType"],
            [Signature.from_dict(entry) for entry in signatures],
        )

    def to_dict(self):
        return {
            "payloadType": self.payload_type,
            "payload": encode_base64(self.payload),
            "signatures": [entry.to_dict() for entry in self.signatures],
        }

    def to_json(self, indent=2):
        return json.dumps(self.to_dict(), indent=indent)

    def signing_input(self):
        """The bytes a signature over this envelope covers."""
        return pae(self.payload_type, self.payload)

    @property
    def signed(self):
        return bool(self.signatures)

    def statement(self, loader=None):
        return statement_module.Statement.from_json(self.payload, loader)


class Document(object):
    """A statement as it was read, with whatever envelope carried it.

    `payload` is the byte string the statement was parsed from, kept so a later
    signature check runs against what arrived rather than against a
    reconstruction.
    """

    def __init__(self, statement, payload, envelope=None):
        self.statement = statement
        self.payload = payload
        self.envelope = envelope

    @property
    def signed(self):
        return self.envelope is not None and self.envelope.signed

    @property
    def signature_state(self):
        """What is known about authorship. Never more than that.

        `ariadne` does not check signatures, so a signed document is reported
        as carrying signatures that were not checked. Gate 7: signing is
        optional and verification is not, and a tool that printed an author it
        had not verified would be the whole problem in miniature.
        """
        if self.envelope is None:
            return "unsigned: a bare statement, with no envelope and no author"
        if not self.envelope.signed:
            return "unsigned: an envelope carrying no signatures"
        return (
            "signed: %d signature(s) present, not checked here "
            "(run cosign verify-attestation for that)" % len(self.envelope.signatures)
        )


def wrap(payload, payload_type=PAYLOAD_TYPE):
    """An unsigned envelope around statement bytes.

    DSSE expects at least one signature. An unsigned envelope is written
    anyway, because gate 7 makes the unsigned local statement a supported state
    and labelling it is more useful than refusing to write it.
    """
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return Envelope(payload, payload_type)


def read(data, loader=None):
    """Read bytes holding either a DSSE envelope or a bare statement.

    Which one it is comes from `_type`, not from guessing at `payload`. An
    envelope missing its `payloadType` should be told that, rather than being
    read as a statement and told its `_type` is absent.

    `loader` is the bounded parser from `safejson` by default, applied to the
    outer document and to the payload inside it. Both arrived from the same
    stranger.
    """
    if loader is None:
        loader = safejson.loads
    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, bytes):
        raise EnvelopeError("expected bytes")
    try:
        raw = loader(data)
    except safejson.InputError:
        raise
    except (ValueError, UnicodeDecodeError) as error:
        raise EnvelopeError("not valid JSON: %s" % error)
    except RecursionError:
        # Nesting deep enough to exhaust the stack is input, not a crash. It
        # arrives from whoever handed over the file, and it has to come back as
        # a refusal with an exit code that means bad input.
        raise EnvelopeError("nested too deeply to parse")
    if not isinstance(raw, dict):
        raise EnvelopeError("expected a JSON object")

    if statement_module.TYPE_FIELD in raw:
        return Document(statement_module.Statement.from_dict(raw), data, None)
    if not set(raw) & ENVELOPE_FIELDS:
        raise EnvelopeError(
            "neither a statement (no %s) nor an envelope (no payload)"
            % statement_module.TYPE_FIELD
        )
    found = Envelope.from_dict(raw)
    return Document(found.statement(loader), found.payload, found)
