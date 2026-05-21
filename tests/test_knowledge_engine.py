from pathlib import Path

from knowledge_engine import (
    KMPALDatabase,
    KnowledgeIndex,
    PlaceAliasStore,
    default_abbreviation_dictionary,
)


FIXTURES = Path(__file__).resolve().parents[1] / "data" / "curated"


def test_default_abbreviation_dictionary_has_core_tokens():
    abbr = default_abbreviation_dictionary()
    tokens = {e.token for e in abbr.entries}
    assert "BKN" in tokens
    assert "br" in tokens
    assert "BR" in tokens


def test_place_alias_store_search_fuzzy():
    if not FIXTURES.exists():
        return
    store = PlaceAliasStore.from_yaml_file(FIXTURES / "places" / "bali_sample.yaml")
    hits = store.search("Mertasari")
    assert len(hits) >= 1
    assert hits[0].canonical_name == "Pantai Mertasari"


def test_kmpal_database_lookup_exact():
    if not (FIXTURES / "kmpal" / "bali_sample.yaml").exists():
        return
    db = KMPALDatabase.from_yaml_file(FIXTURES / "kmpal" / "bali_sample.yaml")
    point = db.find("KSM 2")
    assert point is not None
    assert point.code == "KSM"


def test_knowledge_index_combined_lookup():
    idx = KnowledgeIndex()
    hits = idx.lookup("BKN")
    assert any(h.kind == "abbreviation" for h in hits)
