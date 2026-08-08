import tempfile
import unittest
from pathlib import Path

from mobile_library_automation.hashing import exact_duplicate_groups, sha256_file


class HashingTests(unittest.TestCase):
    def test_streaming_hash_and_duplicate_groups(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.txt"
            second = root / "second.txt"
            unique = root / "unique.txt"
            first.write_text("same bytes", encoding="utf-8")
            second.write_text("same bytes", encoding="utf-8")
            unique.write_text("different bytes", encoding="utf-8")

            shared = sha256_file(first)
            groups = exact_duplicate_groups(
                [
                    (first.name, shared),
                    (second.name, sha256_file(second)),
                    (unique.name, sha256_file(unique)),
                ]
            )

            self.assertEqual(groups, {shared: ["first.txt", "second.txt"]})
