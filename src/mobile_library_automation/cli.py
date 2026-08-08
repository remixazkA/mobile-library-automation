from __future__ import annotations

import argparse
import json
from pathlib import Path

from .documents import plan_documents, verify_plan, write_plan
from .inventory import scan
from .semantic import score_photos, write_scores


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mobile-library",
        description="Inventory and plan a private mobile library locally.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    inventory = commands.add_parser("scan", help="Build or update a SQLite inventory")
    inventory.add_argument("root", type=Path)
    inventory.add_argument("--db", type=Path, required=True)

    documents = commands.add_parser("plan-documents", help="Create a dry-run document plan")
    documents.add_argument("root", type=Path)
    documents.add_argument("--config", type=Path, required=True)
    documents.add_argument("--output", type=Path, required=True)

    verify = commands.add_parser("verify-plan", help="Verify sources against a saved plan")
    verify.add_argument("root", type=Path)
    verify.add_argument("plan", type=Path)

    photos = commands.add_parser("score-photos", help="Score photos with local OpenCLIP")
    photos.add_argument("root", type=Path)
    photos.add_argument("--config", type=Path, required=True)
    photos.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "scan":
        result = scan(args.root, args.db)
    elif args.command == "plan-documents":
        plan = plan_documents(args.root, args.config)
        write_plan(plan, args.output)
        result = {"planned": len(plan), "output": str(args.output)}
    elif args.command == "verify-plan":
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        result = verify_plan(args.root, plan)
    elif args.command == "score-photos":
        scores = score_photos(args.root, args.config)
        write_scores(scores, args.output)
        result = {"scored": len(scores), "output": str(args.output)}
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result.get("missing", 0) or result.get("changed", 0) > 0)


if __name__ == "__main__":
    raise SystemExit(main())
