import tempfile
import unittest
from pathlib import Path

from mobile_library_automation.inventory import scan


class InventoryTests(unittest.TestCase):
    def test_inventory_is_incremental_and_counts_exact_copies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "a.txt").write_text("duplicate", encoding="utf-8")
            (source / "b.txt").write_text("duplicate", encoding="utf-8")
            database = root / "run" / "library.sqlite"

            first = scan(source, database)
            second = scan(source, database)

            self.assertEqual(first["processed"], 2)
            self.assertEqual(first["exact_duplicate_groups"], 1)
            self.assertEqual(first["exact_duplicate_copies"], 1)
            self.assertEqual(second["processed"], 0)
            self.assertEqual(second["unchanged"], 2)
