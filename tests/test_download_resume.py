"""Downloader recovery tests use mocked network responses, not benchmark data."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from kgc.data import download_dataset, SPLITS


class DownloadResumeTests(unittest.TestCase):
    def response(self, url, timeout=None):
        if not isinstance(url, str):
            return io.BytesIO(json.dumps({"sha": "a" * 40}).encode())
        return io.BytesIO(b"aa\trel\tbb\n")

    def test_resume_reuses_only_verified_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls = []
            def interrupted(url, timeout=None):
                if isinstance(url, str) and url.endswith("valid.txt"):
                    raise TimeoutError("mock interruption")
                return self.response(url, timeout)
            with patch("kgc.data.urllib.request.urlopen", side_effect=interrupted):
                with self.assertRaises(TimeoutError):
                    download_dataset(root)
            self.assertTrue((root / "train.txt").exists())
            self.assertTrue((root / "download-state.json").exists())
            def resumed(url, timeout=None):
                calls.append(url)
                return self.response(url, timeout)
            with patch("kgc.data.urllib.request.urlopen", side_effect=resumed), patch("kgc.data.load_dataset", return_value="verified-test-double"):
                result = download_dataset(root, resume=True)
            self.assertEqual(result, "verified-test-double")
            self.assertFalse(any(not isinstance(u, str) or u.endswith("train.txt") for u in calls))
            source = json.loads((root / "source.json").read_text())
            self.assertEqual(set(source["sha256"]), set(SPLITS))
            self.assertFalse((root / "download-state.json").exists())

    def test_legacy_partial_file_verified_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train = root / "train.txt"
            train.write_text("xx\trel\tyy\n")
            with patch("kgc.data.urllib.request.urlopen", side_effect=self.response):
                with self.assertRaisesRegex(ValueError, "preserved"):
                    download_dataset(root, resume=True)
            self.assertEqual(train.read_text(), "xx\trel\tyy\n")

    def test_nonresume_still_refuses_existing_splits(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "train.txt").write_text("aa rel bb\n")
            with self.assertRaises(FileExistsError):
                download_dataset(tmp)
