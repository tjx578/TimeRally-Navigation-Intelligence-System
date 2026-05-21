"""Filesystem export sink.

Menyimpan artefak hasil exporter ke `EXPORTS_ROOT/<event_id>/`.
Di production, sink ini dapat diganti dengan S3/GCS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from app.settings import get_settings


_SAFE_SEGMENT_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_segment(value: str, fallback: str) -> str:
    cleaned = _SAFE_SEGMENT_RE.sub("-", value.strip()).strip(".-")
    return cleaned[:120] or fallback


@dataclass
class FilesystemExportSink:
    root: Path | None = None

    def _root(self) -> Path:
        if self.root is not None:
            return self.root
        return Path(get_settings().exports_root)

    def write(self, event_id: str, filename: str, content: str | bytes) -> Path:
        root = self._root().resolve()
        safe_event_id = _safe_segment(event_id, "event")
        safe_filename = _safe_segment(Path(filename).name, "artifact")
        target_dir = root / safe_event_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = (target_dir / safe_filename).resolve()
        if root not in target.parents:
            raise ValueError("export target keluar dari EXPORTS_ROOT")
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target
