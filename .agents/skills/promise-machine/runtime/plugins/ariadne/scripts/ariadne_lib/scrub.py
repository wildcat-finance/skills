"""Redaction for anything a capture records verbatim.

A build command is the likeliest place for a credential to ride along: an RPC
URL with a key in its path, a token passed as an argument, an environment
variable expanded before the shell handed the line over. Capture writes those
words into a document meant to be published and signed, so they get redacted
first.

Redaction is visible. A removed token is replaced by a marker naming what kind
of thing was there, because a statement that silently dropped an argument would
describe a command nobody ran.
"""

import re

URL = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*)://(.*)$")

KEYLIKE = re.compile(r"^[A-Za-z0-9_\-]{32,}$")
"""Long enough and mixed enough to be a token rather than a word. The mixture
is checked separately, so `--optimize-runs-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
stays put."""

HEXLIKE = re.compile(r"^(0x)?[0-9a-fA-F]{40,}$")
"""An address or a hash is hex too, so hex alone is not redacted. This exists
to describe what the marker means when a private key turns up."""

SECRET_FLAGS = frozenset(
    {
        "--rpc-url",
        "--fork-url",
        "--private-key",
        "--mnemonic",
        "--etherscan-api-key",
        "--api-key",
        "--password",
        "--token",
    }
)

REDACTED_URL = "%s://<redacted>"
REDACTED_TOKEN = "<redacted>"


def mixed(token):
    """True when a token mixes letter kinds the way a key does and a word does not."""
    return (
        any(c.isdigit() for c in token)
        and any(c.isalpha() for c in token)
        and (any(c.isupper() for c in token) or "_" in token or "-" in token)
    )


def token(word):
    """Redact one argument, keeping enough shape to read the command."""
    if not isinstance(word, str):
        return word
    match = URL.match(word)
    if match:
        return REDACTED_URL % match.group(1)
    if HEXLIKE.match(word) and len(word.lstrip("0x")) >= 64:
        # A 32-byte hex string is a private key more often than anything else
        # worth putting on a command line. Addresses and transaction hashes are
        # shorter, and they belong in the statement.
        return REDACTED_TOKEN
    if KEYLIKE.match(word) and mixed(word):
        return REDACTED_TOKEN
    return word


def assignment(word):
    """Redact the value half of `NAME=value`, keeping the name.

    Covers both `--fork-url=https://...` and an inline `PRIVATE_KEY=0x...`,
    which is how a key most often reaches a command line without a flag in
    front of it.
    """
    name, _, value = word.partition("=")
    if name in SECRET_FLAGS:
        return "%s=%s" % (name, REDACTED_TOKEN)
    return "%s=%s" % (name, token(value))


def argv(words):
    """Redact a command line, including the value after a flag that names a secret."""
    out = []
    redact_next = False
    for word in words:
        if redact_next:
            out.append(REDACTED_TOKEN)
            redact_next = False
            continue
        if isinstance(word, str) and "=" in word:
            out.append(assignment(word))
            continue
        out.append(token(word))
        redact_next = isinstance(word, str) and word in SECRET_FLAGS
    return out


def credentials(url):
    """Strip userinfo from a URL, keeping the URL.

    A repository is recorded so a reader can find it, so redacting the whole
    thing would defeat the field. What has to go is the `user:token@` some
    tooling leaves in front of the host.
    """
    if not isinstance(url, str):
        return url
    match = URL.match(url)
    if not match:
        return url
    scheme, rest = match.group(1), match.group(2)
    if "@" not in rest:
        return url
    _, _, tail = rest.partition("@")
    return "%s://%s" % (scheme, tail)


def redacted(words):
    """How many arguments a redaction removed, for recording beside the command."""
    return sum(1 for before, after in zip(words, argv(words)) if before != after)
