from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageOps

from .hashing import exact_duplicate_groups, sha256_file


DEFAULT_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"
}
DEFAULT_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".md"}


@dataclass(frozen=True)
class InventoryRecord:
    path: str
    kind: str
    size: int
    mtime_ns: int
    sha256: str
    width: int | None = None
    height: int | None = None
    error: str | None = None


class Inventory:
    """Incremental SQLite inventory keyed by normalized relative path."""

    def __init__(self, database: Path):
        database.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                size INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                error TEXT
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_files_sha256 ON files(sha256)"
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Inventory":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def cached(self, relative_path: str, size: int, mtime_ns: int) -> bool:
        row = self.connection.execute(
            "SELECT size, mtime_ns, sha256 FROM files WHERE path=?",
            (relative_path,),
        ).fetchone()
        return bool(row and row[0] == size and row[1] == mtime_ns and row[2])

    def upsert(self, record: InventoryRecord) -> None:
        values = asdict(record)
        self.connection.execute(
            """
            INSERT INTO files(path,kind,size,mtime_ns,sha256,width,height,error)
            VALUES(:path,:kind,:size,:mtime_ns,:sha256,:width,:height,:error)
            ON CONFLICT(path) DO UPDATE SET
                kind=excluded.kind,
                size=excluded.size,
                mtime_ns=excluded.mtime_ns,
                sha256=excluded.sha256,
                width=excluded.width,
                height=excluded.height,
                error=excluded.error
            """,
            values,
        )

    def duplicates(self) -> dict[str, list[str]]:
        rows = self.connection.execute(
            "SELECT path, sha256 FROM files WHERE sha256 <> '' ORDER BY path"
        )
        return exact_duplicate_groups(rows)


def _image_size(path: Path) -> tuple[int | None, int | None, str | None]:
    try:
        with Image.open(path) as opened:
            image = ImageOps.exif_transpose(opened)
            return image.width, image.height, None
    except Exception as exc:  # a damaged input belongs in the audit trail
        return None, None, f"{type(exc).__name__}: {exc}"


def scan(
    root: Path,
    database: Path,
    image_extensions: set[str] | None = None,
    document_extensions: set[str] | None = None,
) -> dict[str, object]:
    root = root.resolve(strict=True)
    images = {suffix.lower() for suffix in (image_extensions or DEFAULT_IMAGE_EXTENSIONS)}
    documents = {
        suffix.lower() for suffix in (document_extensions or DEFAULT_DOCUMENT_EXTENSIONS)
    }
    supported = images | documents
    processed = skipped = failed = 0

    with Inventory(database) as inventory:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in supported:
                continue
            relative = path.relative_to(root).as_posix()
            stat = path.stat()
            if inventory.cached(relative, stat.st_size, stat.st_mtime_ns):
                skipped += 1
                continue
            kind = "image" if path.suffix.lower() in images else "document"
            width = height = None
            error = None
            if kind == "image":
                width, height, error = _image_size(path)
            try:
                digest = sha256_file(path)
            except OSError as exc:
                digest = ""
                error = f"{type(exc).__name__}: {exc}"
            inventory.upsert(
                InventoryRecord(
                    path=relative,
                    kind=kind,
                    size=stat.st_size,
                    mtime_ns=stat.st_mtime_ns,
                    sha256=digest,
                    width=width,
                    height=height,
                    error=error,
                )
            )
            processed += 1
            failed += int(error is not None)
        inventory.connection.commit()
        duplicate_groups = inventory.duplicates()

    return {
        "root": str(root),
        "processed": processed,
        "unchanged": skipped,
        "read_errors": failed,
        "exact_duplicate_groups": len(duplicate_groups),
        "exact_duplicate_copies": sum(len(paths) - 1 for paths in duplicate_groups.values()),
    }
