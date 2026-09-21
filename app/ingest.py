"""Load network documents and split them into searchable chunks."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    source: str  # file name the text came from
    title: str   # section heading or config block title
    text: str


def _split_markdown(source: str, text: str) -> list[Chunk]:
    """One chunk per '## ' section of a markdown runbook."""
    chunks = []
    for part in re.split(r"(?m)^## ", text):
        part = part.strip()
        if not part or part.startswith("# "):
            continue
        title, _, body = part.partition("\n")
        chunks.append(Chunk(source, title.strip(), f"{title.strip()}\n{body.strip()}"))
    return chunks


def _split_config(source: str, text: str) -> list[Chunk]:
    """One chunk per config block. Blocks are separated by blank lines and
    start with a '! --- Title ---' comment."""
    chunks = []
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        first, _, _ = block.partition("\n")
        m = re.match(r"!\s*---\s*(.*?)\s*---", first)
        title = m.group(1) if m else block.splitlines()[0]
        device = source.rsplit(".", 1)[0]
        chunks.append(Chunk(source, f"{device}: {title}", f"{device}\n{block}"))
    return chunks


def load_chunks(data_dir: str | Path) -> list[Chunk]:
    """Read every .cfg and .md file in data_dir and return all chunks."""
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    chunks: list[Chunk] = []
    for path in sorted(data_dir.iterdir()):
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            chunks.extend(_split_markdown(path.name, text))
        elif path.suffix in {".cfg", ".txt"}:
            chunks.extend(_split_config(path.name, text))
    if not chunks:
        raise ValueError(f"No .cfg, .txt or .md documents found in {data_dir}")
    return chunks
