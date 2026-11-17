import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import domain_history


class DomainHistoryTests(unittest.TestCase):
    def test_normalize_domain_accepts_urls(self):
        self.assertEqual(
            domain_history.normalize_domain("https://Example.is-a.dev./path"),
            "example.is-a.dev",
        )

    def test_normalize_domain_rejects_git_arguments(self):
        with self.assertRaises(ValueError):
            domain_history.normalize_domain("--all")

    def test_history_includes_commit_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            subprocess = __import__("subprocess")
            subprocess.run(["git", "init", "-q", str(cache)], check=True)
            (cache / "domains").mkdir()
            file = cache / "domains/example.json"
            file.write_text('{"repo": "https://example.com"}\n')
            subprocess.run(["git", "-C", str(cache), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(cache), "-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "commit", "-qm", "Add domain"],
                check=True,
            )
            result = domain_history.history(cache, "example.is-a.dev")
            self.assertEqual(len(result["files"]), 1)
            self.assertEqual(result["files"][0]["path"], "domains/example.json")
            self.assertIn("+{\"repo\"", result["files"][0]["commits"][0]["patch"])

    def test_history_includes_nested_records(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            subprocess = __import__("subprocess")
            subprocess.run(["git", "init", "-q", str(cache)], check=True)
            (cache / "domains").mkdir()
            for name in ("linus.json", "_discord.linus.json", "other.json"):
                (cache / "domains" / name).write_text("{}\n")
            subprocess.run(["git", "-C", str(cache), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(cache), "-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "commit", "-qm", "Add domains"],
                check=True,
            )
            result = domain_history.history(cache, "linus.is-a.dev")
            self.assertEqual(
                [file["path"] for file in result["files"]],
                ["domains/_discord.linus.json", "domains/linus.json"],
            )


if __name__ == "__main__":
    unittest.main()
