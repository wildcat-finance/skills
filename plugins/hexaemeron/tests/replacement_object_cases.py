"""Replacement-object cases loaded by ``test_hexctl``.

``test_hexctl.py`` is a path the promise-machine inventory reads under its
256 KiB bound, so this case lives beside it, as the host-identity cases do,
and ``test_hexctl`` mixes it into ``TestCommitVerification``.
"""


class ReplacementObjectCases:
    """The local signature check reads native objects, not replacements."""

    def test_local_signature_check_ignores_replacement_objects(self):
        module = hexctl_module()
        commit_sha = "a" * 40
        with (
            mock.patch.object(
                module, "bounded_tool_status", return_value=1
            ) as status,
            mock.patch.object(module, "signing_key", return_value=""),
            redirect_stderr(StringIO()),
        ):
            with self.assertRaises(SystemExit):
                module.verify_local_commit(self.dir, commit_sha, "step")

        status.assert_called_once_with(
            self.dir,
            "git",
            [
                "--no-replace-objects",
                "-c", "gpg.program=gpg",
                "-c", "gpg.openpgp.program=gpg",
                "-c", "gpg.x509.program=gpgsm",
                "-c", "gpg.ssh.program=ssh-keygen",
                "verify-commit", commit_sha,
            ],
        )


def build_replacement_object_cases(context):
    """Bind the case to the already-loaded controller test harness."""
    globals().update(
        {name: value for name, value in context.items() if not name.startswith("__")}
    )
    return (ReplacementObjectCases,)
