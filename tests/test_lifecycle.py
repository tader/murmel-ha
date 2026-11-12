import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from wyoming_murmel.backend import load_backend
from wyoming_murmel.__main__ import publish_discovery

class LifecycleTests(unittest.TestCase):
    def test_download_then_offline_restart(self):
        with tempfile.TemporaryDirectory() as root:
            model = Path(root) / "models" / "snapshot"
            model.mkdir(parents=True)
            snapshot = MagicMock(side_effect=[FileNotFoundError(), str(model)])
            transcriber = MagicMock()
            transcriber.transcribe.return_value = {"text": "Hallo."}
            factory = MagicMock(return_value=transcriber)
            modules = {
                "torch": SimpleNamespace(set_num_threads=MagicMock()),
                "huggingface_hub": SimpleNamespace(snapshot_download=snapshot),
                "murmel_flash": SimpleNamespace(Transcriber=SimpleNamespace(from_pretrained=factory)),
            }
            with patch.dict("sys.modules", modules):
                backend = load_backend({"model_revision": "main"}, root)
                self.assertEqual(backend([]), "Hallo.")
                self.assertEqual(snapshot.call_count, 2)
                snapshot.reset_mock(side_effect=True)
                snapshot.side_effect = AssertionError("Network must not be used")
                self.assertEqual(load_backend({"model_revision": "main"}, root)([]), "Hallo.")
                snapshot.assert_not_called()

    def test_discovery_payload(self):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch.dict(os.environ, {"SUPERVISOR_TOKEN": "synthetic-test-token"}):
            with patch("wyoming_murmel.__main__.urlopen", return_value=response) as send:
                publish_discovery()
        request = send.call_args.args[0]
        self.assertEqual(request.full_url, "http://supervisor/discovery")
        payload = json.loads(request.data)
        self.assertEqual(payload["service"], "wyoming")
        self.assertTrue(payload["config"]["uri"].endswith(":10300"))
