"""Core rally intelligence package.

Berisi domain logic untuk Time Rally Navigation Intelligence System.

Modul:
    parser      : mengubah soal mentah menjadi RallyEvent terstruktur.
    reasoning   : memahami konteks singkatan dan ambiguity.
    constraints : memvalidasi absolute binding (jarak, waktu, chaining).
    probability : menyelesaikan waypoint hilang dengan probabilitas tertinggi.
    scoring     : menghitung championship score.
    exporters   : menghasilkan YAML/GPX/KML/GeoJSON/roadbook.
    routing     : domain model provider-neutral routing.
"""

from rally_core.parser.rally_parser import RallyParser
from rally_core.constraints.engine import ConstraintEngine
from rally_core.probability.resolver import MissingWaypointResolver
from rally_core.scoring.engine import ChampionshipScorer

__all__ = [
    "RallyParser",
    "ConstraintEngine",
    "MissingWaypointResolver",
    "ChampionshipScorer",
]

__version__ = "0.1.0"
