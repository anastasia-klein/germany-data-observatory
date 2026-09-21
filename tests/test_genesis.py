import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import download_genesis


class GenesisDownloadTest(unittest.TestCase):
    def test_local_env_does_not_override_existing_value(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text("DESTATIS_GENESIS_TOKEN=file-secret\n", encoding="utf-8")
            with patch.dict(os.environ, {"DESTATIS_GENESIS_TOKEN": "process-secret"}, clear=False):
                download_genesis.load_local_env(env_file)
                self.assertEqual("process-secret", os.environ["DESTATIS_GENESIS_TOKEN"])

    def test_api_request_places_token_only_in_headers(self):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return b"{}"

        def fake_urlopen(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return Response()

        with patch.object(download_genesis, "urlopen", fake_urlopen):
            download_genesis.api_request("metadata/cube", "test-secret", {"name": "cube"})

        request = captured["request"]
        self.assertNotIn(b"test-secret", request.data)
        self.assertEqual("test-secret", request.get_header("Username"))
        self.assertEqual(120, captured["timeout"])

    def test_status_error_is_concise_and_contains_no_parameters(self):
        response = {
            "Status": {"Code": 8081, "Content": "First line\nMore internal detail"},
            "Parameter": {"username": "secret"},
        }
        message = str(download_genesis.status_error(response))
        self.assertEqual("GENESIS status 8081: First line", message)
        self.assertNotIn("secret", message)

    def test_example_env_contains_placeholder_only(self):
        example = (download_genesis.ROOT / ".env.example").read_text(encoding="utf-8")
        assignments = [line for line in example.splitlines() if line and not line.startswith("#")]
        self.assertEqual(["DESTATIS_GENESIS_TOKEN="], assignments)


if __name__ == "__main__":
    unittest.main()
