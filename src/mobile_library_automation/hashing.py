from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a streaming SHA-256 digest without loading the file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_duplicate_groups(
    rows: Iterable[tuple[str, str]],
) -> dict[str, list[str]]:
    """Group paths by identical SHA-256 and omit unique files."""
    grouped: dict[str, list[str]] = defaultdict(list)
    for path, digest in rows:
        if digest:
            grouped[digest].append(path)
    return {
        digest: sorted(paths, key=str.casefold)
        for digest, paths in grouped.items()
        if len(paths) > 1
    }
