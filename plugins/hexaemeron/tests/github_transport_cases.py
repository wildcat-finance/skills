"""GitHub REST transport cases loaded by ``test_hexctl``."""


class GithubTransportCases:
    """How receipt readers reach GitHub and refuse when they cannot.

    Every read goes over REST because a ``gh`` command taking ``--json`` uses
    GraphQL. A read that never arrived also has a refusal shape that no GitHub
    verdict shares.
    """

    URL = "https://github.com/wildcat-finance/example/pull/1"

    def gh_calls(self, run):
        log_path = os.path.join(self.dir, "transport.log")
        with mock.patch.dict(
            os.environ, {"PATH": self.env["PATH"], "FAKE_GH_LOG": log_path}
        ):
            run(hexctl_module())
        with open(log_path, encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def test_every_receipt_read_goes_over_rest(self):
        branch, base, head = "fiat/run-step-1", "fiat/run", "a" * 40
        payload = self.fake_pr(self.URL, branch, base, head)

        def read(module):
            with mock.patch.dict(
                os.environ, {"FAKE_GH_PRS": json.dumps({self.URL: payload})}
            ):
                module.inspect_pull_request(
                    self.dir,
                    self.URL,
                    expected_head=branch,
                    expected_base=base,
                    expected_head_sha=head,
                    expected_merge_sha=None,
                )
            module.verify_github_commits(self.dir, [head])

        calls = self.gh_calls(read)
        self.assertTrue(calls, "the readers made no GitHub request at all")
        for call in calls:
            self.assertEqual(call[:1], ["api"], f"{call} is not a REST read")
            self.assertNotIn("--json", call, f"{call} would go over GraphQL")

    def test_the_rest_paths_name_the_repository_and_the_pull_request(self):
        branch, base, head = "fiat/run-step-1", "fiat/run", "a" * 40
        payload = self.fake_pr(self.URL, branch, base, head)

        def read(module):
            with mock.patch.dict(
                os.environ, {"FAKE_GH_PRS": json.dumps({self.URL: payload})}
            ):
                module.inspect_pull_request(
                    self.dir,
                    self.URL,
                    expected_head=branch,
                    expected_base=base,
                    expected_head_sha=head,
                    expected_merge_sha=None,
                )

        paths = [call[-1] for call in self.gh_calls(read)]
        self.assertIn("repos/wildcat-finance/example", paths)
        self.assertIn("repos/wildcat-finance/example/pulls/1", paths)

    def refusal(self, mode, read):
        error = StringIO()
        with mock.patch.dict(
            os.environ, {"PATH": self.env["PATH"], "FAKE_GH_MODE": mode}
        ), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                read(hexctl_module())
        return error.getvalue()

    def test_an_unreachable_reader_refuses_apart_from_an_unverified_verdict(self):
        """A failed read is not a verdict about otherwise verified commits."""
        unreachable = self.refusal(
            "nonzero",
            lambda module: module.verify_github_commits(self.dir, ["a" * 40]),
        )
        self.assertIn("transport failure", unreachable)
        self.assertIn("was not answered", unreachable)
        self.assertNotIn("not verified:true", unreachable)

        unverified = self.refusal(
            "verified-false",
            lambda module: module.verify_github_commits(self.dir, ["a" * 40]),
        )
        self.assertIn("not verified:true", unverified)
        self.assertNotIn("transport failure", unverified)

    def test_an_unreachable_identity_read_is_named_as_transport(self):
        message = self.refusal(
            "nonzero", lambda module: module.github_repository(self.dir)
        )
        self.assertIn("transport failure", message)
        self.assertIn("repos/wildcat-finance/example", message)

    def test_no_answer_at_all_is_transport_not_verdict(self):
        """A stall, an overrun and a non-document are not verdicts."""
        # Resolve Git before the deliberately short GitHub transport probe.
        with mock.patch.dict(
            os.environ,
            {
                "PATH": self.env["PATH"],
                "FAKE_GIT_MODE": "slow-remote",
            },
        ):
            repository = hexctl_module().target_repository(self.dir)
        for mode in ("invalid-json", "overflow", "timeout"):
            with self.subTest(mode=mode):
                module = hexctl_module()
                module.GIT_TIMEOUT = 0.5
                error = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {
                        "PATH": self.env["PATH"],
                        "FAKE_GH_MODE": mode,
                        "FAKE_GIT_MODE": "slow-remote",
                    },
                ), mock.patch.object(
                    module,
                    "target_repository",
                    return_value=repository,
                ) as target_repository, redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.verify_github_commits(self.dir, ["a" * 40])
                target_repository.assert_called_once_with(self.dir)
                self.assertIn("transport failure", error.getvalue())
                self.assertNotIn("not verified:true", error.getvalue())

    def test_an_open_pull_request_records_no_merge_commit(self):
        """Ignore REST's test merge SHA when GitHub says the PR is open."""
        module = hexctl_module()
        branch, base, head = "fiat/run-step-1", "fiat/run", "a" * 40
        payload = self.fake_pr(self.URL, branch, base, head)
        self.assertEqual(payload["merge_commit_sha"], "f" * 40)
        with mock.patch.dict(
            os.environ,
            {
                "PATH": self.env["PATH"],
                "FAKE_GH_PRS": json.dumps({self.URL: payload}),
            },
        ):
            record = module.inspect_pull_request(
                self.dir,
                self.URL,
                expected_head=branch,
                expected_base=base,
                expected_head_sha=head,
                expected_merge_sha=None,
            )
        self.assertIsNone(record["merge_sha"])
        self.assertEqual(record["state"], "OPEN")

    def test_a_merged_pull_request_records_its_merge_and_state(self):
        module = hexctl_module()
        branch, base = "fiat/run-step-1", "fiat/run"
        head, merge = "a" * 40, "e" * 40
        payload = self.fake_pr(self.URL, branch, base, head, merge)
        with mock.patch.dict(
            os.environ,
            {
                "PATH": self.env["PATH"],
                "FAKE_GH_PRS": json.dumps({self.URL: payload}),
            },
        ):
            record = module.inspect_pull_request(
                self.dir,
                self.URL,
                expected_head=branch,
                expected_base=base,
                expected_head_sha=head,
                expected_merge_sha=merge,
            )
        self.assertEqual(record["merge_sha"], merge)
        self.assertEqual(record["state"], "MERGED")

    def test_an_origin_with_a_relative_segment_is_refused(self):
        """The origin owner and name enter every REST path."""
        error = StringIO()
        with mock.patch.dict(
            os.environ,
            {
                "PATH": self.env["PATH"],
                "FAKE_GIT_ORIGIN": "https://github.com/../wildcat-finance",
            },
        ), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                hexctl_module().github_repository(self.dir)
        self.assertIn("one GitHub repository", error.getvalue())


def build_github_transport_tests(context):
    """Build the cases against the already-loaded controller test harness."""
    globals().update(
        {name: value for name, value in context.items() if not name.startswith("__")}
    )
    return type(
        "TestGithubTransport",
        (GithubTransportCases, context["HexctlCase"]),
        {},
    )
