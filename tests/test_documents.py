import json
import tempfile
import unittest
from pathlib import Path

from mobile_library_automation.documents import (
    plan_documents,
    sanitize_stem,
    verify_plan,
)


CONFIG = """
[documents.categories]
geography = ["climate", "geography"]
history = ["history", "archaeology"]
"""


class DocumentTests(unittest.TestCase):
    def test_sanitize_stem_preserves_unicode_and_removes_unsafe_characters(self) -> None:
        self.assertEqual(
            sanitize_stem('  Geografía: clima? <tema>  '),
            "Geografía clima tema",
        )

    def test_plan_is_classified_and_collision_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            root = temp / "documents"
            (root / "one").mkdir(parents=True)
            (root / "two").mkdir(parents=True)
            (root / "one" / "notes.txt").write_text(
                "Climate geography notes", encoding="utf-8"
            )
            (root / "two" / "notes.txt").write_text(
                "Climate geography exercises", encoding="utf-8"
            )
            config = temp / "config.toml"
            config.write_text(CONFIG, encoding="utf-8")

            plan = plan_documents(root, config)

            self.assertEqual(len(plan), 2)
            self.assertEqual({row["category"] for row in plan}, {"geography"})
            self.assertEqual(
                len({str(row["destination"]).casefold() for row in plan}),
                2,
            )
            self.assertTrue(
                all("collision resolved" in str(row["reason"]) for row in plan)
            )
            self.assertEqual(
                verify_plan(root, plan),
                {"verified": 2, "missing": 0, "changed": 0},
            )

    def test_verify_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            root = temp / "documents"
            root.mkdir()
            outside = temp / "outside.txt"
            outside.write_text("private", encoding="utf-8")
            plan = [{"source": "../outside.txt", "sha256": "irrelevant"}]

            with self.assertRaisesRegex(ValueError, "escapes source root"):
                verify_plan(root, json.loads(json.dumps(plan)))
