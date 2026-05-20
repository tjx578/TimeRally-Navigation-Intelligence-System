# Backend Implementation Plan

## Phase 1: Core API

Implement:

```text
POST /v1/rally/parse
POST /v1/places/search
POST /v1/routing/route
POST /v1/validation/route
POST /v1/export/artifacts
```

Wire:
- parser from `packages/rally_core/parser`,
- place lookup from `packages/knowledge_engine`,
- routing provider from `services/routing-gateway`,
- validation from `packages/rally_core/constraints`,
- exporters from `packages/rally_core/exporters`.

## Phase 2: Data Store

Add PostgreSQL + PostGIS tables:

```text
events
sub_trayeks
waypoints
places
place_aliases
route_segments
validation_reports
export_artifacts
```

## Phase 3: Provider Gateways

Implement adapters:
- Valhalla,
- OSRM,
- GraphHopper,
- Google validation.

## Phase 4: Offline Package

Generate:
- event YAML,
- roadbook JSON,
- route GeoJSON,
- GPX/KML,
- PMTiles/MBTiles manifest.

## Phase 5: Championship Hardening

Add:
- golden tests,
- provider comparison,
- no-placeholder gate,
- route lock,
- audit trail.

