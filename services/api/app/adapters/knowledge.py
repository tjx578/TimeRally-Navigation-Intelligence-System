"""Adapter pembangun KnowledgeIndex untuk API.

Default: load curated YAML jika tersedia di KNOWLEDGE_ROOT, fallback ke
abbreviation dictionary built-in.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from knowledge_engine import (
    AbbreviationDictionary,
    KMPALDatabase,
    KnowledgeIndex,
    PlaceAliasStore,
    default_abbreviation_dictionary,
)

from app.settings import get_settings


def _safe_load_abbreviations(root: Path) -> AbbreviationDictionary:
    target = root / "abbreviations" / "rally_indonesia.yaml"
    if target.is_file():
        try:
            return AbbreviationDictionary.from_yaml_file(target)
        except Exception:  # noqa: BLE001 - jangan ganggu boot API jika file korup
            pass
    return default_abbreviation_dictionary()


def _safe_load_places(root: Path) -> PlaceAliasStore:
    store = PlaceAliasStore()
    places_dir = root / "places"
    if places_dir.is_dir():
        for yaml_file in places_dir.glob("*.yaml"):
            try:
                store.add_many(PlaceAliasStore.from_yaml_file(yaml_file).aliases)
            except Exception:  # noqa: BLE001
                continue
    return store


def _safe_load_kmpal(root: Path) -> KMPALDatabase:
    db = KMPALDatabase()
    kmpal_dir = root / "kmpal"
    if kmpal_dir.is_dir():
        for yaml_file in kmpal_dir.glob("*.yaml"):
            try:
                more = KMPALDatabase.from_yaml_file(yaml_file).points
                db.points.extend(more)
            except Exception:  # noqa: BLE001
                continue
    return db


@lru_cache(maxsize=1)
def build_default_knowledge_index() -> KnowledgeIndex:
    settings = get_settings()
    root = Path(settings.knowledge_root)
    return KnowledgeIndex(
        abbreviations=_safe_load_abbreviations(root),
        places=_safe_load_places(root),
        kmpal=_safe_load_kmpal(root),
    )
