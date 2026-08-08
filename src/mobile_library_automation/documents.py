from __future__ import annotations

import json
import re
import tomllib
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

from pypdf import PdfReader

from .hashing import sha256_file


DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".md"}
INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _xml_text(data: bytes) -> str:
    root = ElementTree.fromstring(data)
    return " ".join(text.strip() for text in root.itertext() if text.strip())


def extract_evidence(path: Path, limit: int = 12_000) -> str:
    """Extract a bounded amount of local text without changing the source."""
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="replace")[:limit]
        if suffix == ".pdf":
            reader = PdfReader(path)
            return " ".join((page.extract_text() or "") for page in reader.pages[:2])[:limit]
        if suffix in {".docx", ".xlsx"}:
            members = (
                ["docProps/core.xml", "word/document.xml"]
                if suffix == ".docx"
                else ["docProps/core.xml", "xl/sharedStrings.xml"]
            )
            chunks: list[str] = []
            with zipfile.ZipFile(path) as archive:
                for member in members:
                    if member in archive.namelist():
                        chunks.append(_xml_text(archive.read(member)))
            return " ".join(chunks)[:limit]
    except Exception:
        return ""
    return ""


def sanitize_stem(value: str, fallback: str = "document") -> str:
    value = unicodedata.normalize("NFC", value)
    value = INVALID_WINDOWS_CHARS.sub(" ", value)
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip(" .-")
    value = re.sub(r"\b(?:copy|copia)\b$", "", value, flags=re.IGNORECASE).strip(" .-")
    return (value or fallback)[:112].rstrip(" .-")


def _candidate_title(path: Path, evidence: str) -> str:
    original = sanitize_stem(path.stem)
    generic = bool(
        re.fullmatch(
            r"(?:document(?:o)?|untitled|null|tema\s*\d+|[0-9a-f-]{16,}|\d{7,})",
            original,
            flags=re.IGNORECASE,
        )
    )
    if not generic:
        return original
    first_line = next((line.strip() for line in evidence.splitlines() if line.strip()), "")
    words = re.sub(r"\s+", " ", first_line).split()[:14]
    return sanitize_stem(" ".join(words), fallback=original)


def load_categories(config_path: Path) -> dict[str, list[str]]:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    categories = data.get("documents", {}).get("categories", {})
    return {
        str(name): [str(keyword).casefold() for keyword in keywords]
        for name, keywords in categories.items()
    }


def classify(evidence: str, categories: dict[str, list[str]]) -> tuple[str, str]:
    normalized = unicodedata.normalize("NFKD", evidence).casefold()
    scores = Counter(
        {
            category: sum(normalized.count(keyword) for keyword in keywords)
            for category, keywords in categories.items()
        }
    )
    if not scores or scores.most_common(1)[0][1] == 0:
        return "uncategorized", "no configured keyword matched"
    winner, score = scores.most_common(1)[0]
    return winner, f"{score} configured keyword matches"


def plan_documents(root: Path, config_path: Path) -> list[dict[str, object]]:
    root = root.resolve(strict=True)
    categories = load_categories(config_path)
    plan: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in DOCUMENT_EXTENSIONS:
            continue
        evidence = extract_evidence(path)
        category, reason = classify(f"{path.stem}\n{evidence}", categories)
        title = _candidate_title(path, evidence)
        plan.append(
            {
                "source": path.relative_to(root).as_posix(),
                "destination": f"{category}/{title}{path.suffix.lower()}",
                "category": category,
                "reason": reason,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )

    collisions: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in plan:
        collisions[str(row["destination"]).casefold()].append(row)
    for rows in collisions.values():
        if len(rows) < 2:
            continue
        for number, row in enumerate(rows, start=1):
            destination = PurePosixPath(str(row["destination"]))
            row["destination"] = str(
                destination.with_name(f"{destination.stem} - version {number}{destination.suffix}")
            )
            row["reason"] = f"{row['reason']}; collision resolved"
    return plan


def write_plan(plan: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_source(root: Path, relative: str) -> Path:
    candidate = (root / PurePosixPath(relative)).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes source root: {relative}")
    return candidate


def verify_plan(root: Path, plan: list[dict[str, object]]) -> dict[str, int]:
    root = root.resolve(strict=True)
    verified = missing = changed = 0
    for row in plan:
        source = _safe_source(root, str(row["source"]))
        if not source.is_file():
            missing += 1
        elif sha256_file(source) != row.get("sha256"):
            changed += 1
        else:
            verified += 1
    return {"verified": verified, "missing": missing, "changed": changed}
