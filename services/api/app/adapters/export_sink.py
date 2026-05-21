"""Filesystem export sink.

Menyimpan artefak hasil exporter ke `EXPORTS_ROOT/<event_id>/`.
Di production, sink ini dapat diganti dengan S3/GCS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.settings import get_settings


@dataclass
class FilesystemExportSink:
    root: Path | None = None

    def _root(self) -> Path:
        if self.root is not None:
            return self.root
        return Path(get_settings().exports_root)

    def write(self, event_id: str, filename: str, content: str | bytes) -> Path:
        target_dir = self._root() / event_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / filename
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target
