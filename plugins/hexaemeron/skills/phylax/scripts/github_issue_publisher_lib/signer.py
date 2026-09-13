"""Fixed OpenSSL signing boundary for one GitHub App JWT."""

from __future__ import annotations

import base64
from collections.abc import Callable
import math
import subprocess
from typing import Protocol

from .canonical import canonical_json
from .errors import PublisherError, refuse


APP_ID = "4764812"
OPENSSL_PATH = "/usr/bin/openssl"
PEM_PATH = "/var/db/wildcat-github-issue-publisher/shoggoth-wildcat-labs.pem"
SIGN_TIMEOUT_SECONDS = 5.0
MAX_SIGNING_INPUT_BYTES = 2_048
MAX_SIGNATURE_BYTES = 4_096
RSA_SIGNATURE_BYTES = 256
OPENSSL_ARGUMENTS = (
    OPENSSL_PATH,
    "dgst",
    "-sha256",
    "-sign",
    PEM_PATH,
)


class Signer(Protocol):
    def sign(self, signing_input: bytes, *, timeout_seconds: float) -> bytes: ...

    def close(self) -> None: ...


SignerRunner = Callable[[tuple[str, ...], bytes, float, int], bytes]


def _base64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _default_runner(
    arguments: tuple[str, ...],
    signing_input: bytes,
    timeout_seconds: float,
    output_limit: int,
) -> bytes:
    """Run the fixed executable without a shell or inherited environment."""

    completed = subprocess.run(
        list(arguments),
        input=signing_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=timeout_seconds,
        check=False,
        close_fds=True,
        env={},
    )
    if completed.returncode != 0:
        refuse("GIP212", "signer.exit")
    output = completed.stdout
    if not isinstance(output, bytes) or len(output) > output_limit:
        refuse("GIP211", "signer.output")
    return output


class OpenSSLSigner:
    """Sign only bounded JWT input with one code-owned key and argv."""

    def __init__(self, runner: SignerRunner = _default_runner):
        if not callable(runner):
            refuse("GIP210", "signer.runner")
        self._runner = runner

    def sign(self, signing_input: bytes, *, timeout_seconds: float) -> bytes:
        if (
            not isinstance(signing_input, bytes)
            or not signing_input
            or len(signing_input) > MAX_SIGNING_INPUT_BYTES
            or not signing_input.isascii()
        ):
            refuse("GIP210", "signer.input")
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or timeout_seconds <= 0
            or timeout_seconds > SIGN_TIMEOUT_SECONDS
            or not math.isfinite(timeout_seconds)
        ):
            refuse("GIP210", "signer.timeout")
        try:
            signature = self._runner(
                OPENSSL_ARGUMENTS,
                signing_input,
                float(timeout_seconds),
                MAX_SIGNATURE_BYTES,
            )
        except PublisherError:
            raise
        except (OSError, subprocess.SubprocessError, TimeoutError, ValueError) as exc:
            raise PublisherError("GIP211", "signer.unavailable") from exc
        except Exception as exc:
            raise PublisherError("GIP211", "signer.unavailable") from exc
        if not isinstance(signature, bytes) or len(signature) > MAX_SIGNATURE_BYTES:
            refuse("GIP211", "signer.output")
        if len(signature) != RSA_SIGNATURE_BYTES:
            refuse("GIP213", "signer.signature")
        return signature

    def close(self) -> None:
        """The production signer retains no descriptor between calls."""


def build_app_jwt(now: int, signer: Signer, *, timeout_seconds: float) -> str:
    """Build one short-lived GitHub App JWT after admission."""

    if isinstance(now, bool) or not isinstance(now, int) or now < 1:
        refuse("GIP210", "signer.clock")
    header = _base64url(canonical_json({"alg": "RS256", "typ": "JWT"}))
    payload = _base64url(
        canonical_json({"exp": now + 540, "iat": now - 60, "iss": APP_ID})
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = signer.sign(signing_input, timeout_seconds=timeout_seconds)
    return f"{header}.{payload}.{_base64url(signature)}"
