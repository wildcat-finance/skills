"""Wildcat V2 wrapper instances as capture subjects (skills#2092).

`LegacyIdentityTests` freezes what a plan without `wildcat_v2_wrappers`
builds. Every literal below was computed at Skills
`50d71a2e8c1777f8eb26db32dd8adeadb34063bd`, before any wrapper code existed,
by building the constructed V2 and V1 releases through the fake transport in
`test_wildcat_venue.py`. A later change that moves a legacy release's bytes
fails here.

The design record's conformance resolver loads these three cases by name for
`legacy-identities-hold`, so their identifiers must not change.
"""

import hashlib
import json

from tests import test_wildcat_venue as venue
from alexandria_lib import wildcat_registry
from alexandria_lib.venues import wildcat_v1, wildcat_v2


V2_RELEASE_ID = "sha256:f2b94e967c761a871129f5889fd372e992d62de87104fb5d5a4480338f9915a1"
V1_RELEASE_ID = "sha256:cbbacc59170bdf549c56347f8a962a869a6632868606a1ce3a0e1b37c0ae3def"
# The three registry digests are written only in `wildcat_registry.py`, which
# `RegistryGeneratorTests` enforces, so the freeze pins the SHA-256 of the
# V2, pre-#1880 and V1 constants joined by newlines rather than restating them.
REGISTRY_CONSTANTS_SHA256 = "5ac269412766da57a767a0874cf1d27a5c1987c3f398ffa29c67c341712c884f"
V2_REGISTRY_BYTES = 64891
V1_REGISTRY_BYTES = 7712


class LegacyIdentityTests(venue.WildcatCase):
    """The constructed legacy releases and the registry pins, as they stood at the base."""

    def setUp(self):
        """Each case names its venue before the shared fixture loads."""

    def released_on(self, name):
        self.VENUE = name
        super().setUp()
        output, release_id = self.released()
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["release_id"], release_id)
        self.assertNotIn("wildcat_v2_wrappers", self.plan)
        return release_id

    def test_constructed_v2_release_identifier_is_frozen(self):
        self.assertEqual(self.released_on(wildcat_v2.VENUE), V2_RELEASE_ID)

    def test_constructed_v1_release_identifier_is_frozen(self):
        self.assertEqual(self.released_on(wildcat_v1.VENUE), V1_RELEASE_ID)

    def test_registry_digest_constants_are_unchanged(self):
        constants = (
            wildcat_registry.WILDCAT_V2_REGISTRY_SHA256,
            wildcat_registry.PRE_1880_WILDCAT_V2_REGISTRY_SHA256,
            wildcat_registry.WILDCAT_V1_REGISTRY_SHA256,
        )
        joined = "\n".join(constants).encode("ascii")
        self.assertEqual(hashlib.sha256(joined).hexdigest(), REGISTRY_CONSTANTS_SHA256)
        v2 = wildcat_registry.registry_bytes(venue.REPO_ROOT)
        v1 = wildcat_registry.registry_v1_bytes(venue.REPO_ROOT)
        self.assertEqual(len(v2), V2_REGISTRY_BYTES)
        self.assertEqual(hashlib.sha256(v2).hexdigest(), constants[0])
        self.assertEqual(len(v1), V1_REGISTRY_BYTES)
        self.assertEqual(hashlib.sha256(v1).hexdigest(), constants[2])
