import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import deliver


class DeliveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.session = Path(self.temp.name) / "20261112-000406"
        self.session.mkdir()
        (self.session / "session.json").write_text(json.dumps({
            "id": self.session.name, "state": "completed"}))
        (self.session / "transcript.md").write_text("Meeting: Example\n")
        (self.session / "audio.m4a").write_bytes(b"DO NOT TRANSFER")

    def test_allowlist_and_hash_verification_before_publish(self):
        calls = []
        snapshots = {}

        def remote(host, *args, **kwargs):
            calls.append(args)
            if args[0] == "test":
                return SimpleNamespace(returncode=1, stdout="", stderr="")
            if args[0] == "sha256sum":
                return SimpleNamespace(stdout="\n".join(
                    deliver.digest(snapshots[Path(p).name]) + "  " + p
                    for p in args[1:]))
            return SimpleNamespace(returncode=0)

        def copy(args, **kwargs):
            self.assertEqual(args[:4], ["scp", "-q", "-o", "BatchMode=yes"])
            self.assertEqual([Path(p).name for p in args[4:-1]], list(deliver.FILES))
            for path in args[4:-1]:
                snapshots[Path(path).name] = Path(path).read_bytes()

        with patch.object(deliver, "remote", side_effect=remote), \
                patch.object(deliver.subprocess, "run", side_effect=copy):
            deliver.deliver("adam", "/home/xuanwo/Meetings", self.session)
        operations = [c[0] for c in calls]
        self.assertLess(operations.index("sha256sum"), operations.index("mv"))
        self.assertEqual((self.session / "audio.m4a").read_bytes(), b"DO NOT TRANSFER")

    def test_existing_meeting_with_changed_content_is_not_overwritten(self):
        with patch.object(deliver, "remote", return_value=SimpleNamespace(returncode=0)), \
                patch.object(deliver, "hashes", return_value=["changed", "changed"]), \
                patch.object(deliver.subprocess, "run") as copy:
            with self.assertRaisesRegex(ValueError, "Changed input requires review"):
                deliver.deliver("adam", "/home/xuanwo/Meetings", self.session)
            copy.assert_not_called()

    def test_recording_session_is_not_sent(self):
        (self.session / "session.json").write_text(json.dumps({
            "id": self.session.name, "state": "recording"}))
        with patch.object(deliver, "remote") as remote:
            deliver.deliver("adam", "/home/xuanwo/Meetings", self.session)
            remote.assert_not_called()


if __name__ == "__main__":
    unittest.main()
