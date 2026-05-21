"""API adapters package.

Adapter membungkus integrasi eksternal:
- routing-gateway (sekarang via in-process MockRoutingProvider untuk dev)
- place-resolver (local-first via KnowledgeIndex)
- export sink (filesystem)
"""

from app.adapters.knowledge import build_default_knowledge_index
from app.adapters.routing import RoutingAdapter, MockRoutingProvider
from app.adapters.export_sink import FilesystemExportSink

__all__ = [
    "build_default_knowledge_index",
    "RoutingAdapter",
    "MockRoutingProvider",
    "FilesystemExportSink",
]
