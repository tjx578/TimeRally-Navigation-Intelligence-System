"""Export sinks for generated rally artifacts.

Default menyimpan ke filesystem `EXPORTS_ROOT/<event_id>/`. Jika
`EXPORTS_ROOT` memakai URI `gs://bucket/prefix`, artefak di-upload ke Google
Cloud Storage. Ini menjaga API export tetap sama saat deployment pindah dari
VPS/Supabase ke Google Cloud-only.
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


@dataclass(frozen=True)
class StoredArtifact:
    path: str
    size_bytes: int


@dataclass
class FilesystemExportSink:
    root: Path | None = None

    def _root(self) -> Path:
        if self.root is not None:
            return self.root
        return Path(get_settings().exports_root)

    def write(self, event_id: str, filename: str, content: str | bytes) -> StoredArtifact:
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
        return StoredArtifact(path=str(target), size_bytes=target.stat().st_size)


@dataclass
class GoogleCloudStorageExportSink:
    root_uri: str

    def _parse_root(self) -> tuple[str, str]:
        without_scheme = self.root_uri.removeprefix("gs://")
        bucket, _, prefix = without_scheme.partition("/")
        if not bucket:
            raise ValueError("EXPORTS_ROOT gs:// wajib menyertakan bucket")
        return bucket, prefix.strip("/")

    def write(self, event_id: str, filename: str, content: str | bytes) -> StoredArtifact:
        try:
            from google.cloud import storage
        except ImportError as exc:  # pragma: no cover - optional production dependency
            raise RuntimeError(
                "google-cloud-storage belum terpasang, tidak bisa menulis EXPORTS_ROOT gs://"
            ) from exc

        bucket_name, prefix = self._parse_root()
        safe_event_id = _safe_segment(event_id, "event")
        safe_filename = _safe_segment(Path(filename).name, "artifact")
        object_parts = [part for part in (prefix, safe_event_id, safe_filename) if part]
        object_name = "/".join(object_parts)
        payload = content if isinstance(content, bytes) else content.encode("utf-8")

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(payload)
        return StoredArtifact(
            path=f"gs://{bucket_name}/{object_name}",
            size_bytes=len(payload),
        )


def get_export_sink() -> FilesystemExportSink | GoogleCloudStorageExportSink:
    exports_root = get_settings().exports_root
    if exports_root.startswith("gs://"):
        return GoogleCloudStorageExportSink(exports_root)
    return FilesystemExportSink()
