"""Pytest setup: pastikan packages tetap dapat di-import dari repo root."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for sub in ("packages/rally_core", "packages/geo_engine", "packages/knowledge_engine", "packages/data_contracts"):
    parent = ROOT / sub
    if parent.exists():
        sys.path.insert(0, str(parent.parent))
sys.path.insert(0, str(ROOT / "services" / "api"))
