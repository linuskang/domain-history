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
            file = cache / "domains/example.is-a.dev.json"
            file.write_text('{"repo": "https://example.com"}\n')
            subprocess.run(["git", "-C", str(cache), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(cache), "-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "commit", "-qm", "Add domain"],
                check=True,
            )
            result = domain_history.history(cache, "example.is-a.dev")
            self.assertEqual(len(result["commits"]), 1)
            self.assertIn("+{\"repo\"", result["commits"][0]["patch"])


if __name__ == "__main__":
    unittest.main()
