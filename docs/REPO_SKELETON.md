# Repo Skeleton

Dokumen ini menjelaskan rancangan folder lengkap dan tanggung jawab tiap area.

```text
TimeRally-Navigation-Intelligence-System/
  apps/
    web-map-console/
      src/features/rally-map/        Visualisasi MapLibre, route layers, waypoint edit.
      src/features/roadbook/         Tabel waktu, ETA, tulip, instruksi per leg.
      src/features/validation/       Panel compliance, warning, confidence.
    field-mobile/
      src/                           Mobile/offline navigation shell.
  services/
    api/
      app/routers/                   REST API untuk parse, route, validate, export.
      app/schemas/                   Kontrak request/response.
      app/use_cases/                 Orkestrasi use case.
    routing-gateway/
      providers/                     Adapter Valhalla, OSRM, GraphHopper, Google.
      profiles/                      Rally car, scouting, safety, restricted road.
    place-resolver/
      providers/                     Local POI, Nominatim, Google Places, manual.
    map-tiles/
      styles/                        MapLibre style JSON, offline style.
    tracking-gateway/                Adapter Traccar dan live telemetry.
  packages/
    rally_core/
      parser/                        Soal rally -> event, sub-trayek, waypoint.
      reasoning/                     Mind map, ambiguity resolution, context logic.
      constraints/                   Absolute binding, chaining, violation handling.
      probability/                   Missing waypoint resolver.
      ml/                            Candidate ranking, feedback, evaluation.
      routing/                       Provider-neutral routing models.
      scoring/                       Championship score and penalty.
      exporters/                     YAML/EAML, GPX, KML, GeoJSON, roadbook.
    geo_engine/                      Haversine, corridor, snap, map matching helpers.
    knowledge_engine/                Abbreviation, KMPAL, POI index, fuzzy search.
    data_contracts/                  Shared schemas.
  data/
    raw/                             File asli dari user, OCR, XLSX, PDF, gambar.
    curated/places/                  Master POI database.
    curated/kmpal/                   KMPAL verified points.
    curated/rally_rules/             SOP, singkatan, formula, scoring rules.
    mapdata/osm_extracts/            PBF region extract.
    mapdata/tiles/                   PMTiles/MBTiles.
    fixtures/rally_cases/            Kasus uji rally.
    ml/                              Labels, feature tables, evaluation reports.
  infra/
    docker/                          Dockerfile per service.
    compose/                         Docker Compose stack.
    k8s/                             Deployment production.
  ops/
    runbooks/                        Runbook hari lomba.
    quality-gates/                   Checklist validasi sebelum publish.
  docs/
    decisions/                       ADR arsitektur.
  tests/
    unit/                            Parser, formula, scoring, probability.
    integration/                     API + routing engine + resolver.
    golden/                          Expected output dari soal rally resmi.
  tools/
    importers/                       Import local legacy data.
    validators/                      Lint data dan route compliance.
    benchmarks/                      Compare Valhalla/OSRM/Google timing.
```

## Definisi "Lengkap"

Skeleton disebut lengkap jika setiap capability berikut punya tempat:

1. Parsing soal rally.
2. Kamus singkatan dan contextual recognition.
3. KMPAL, POI, dan place alias.
4. Missing waypoint probability.
5. Routing multi-provider.
6. Offline map and tile delivery.
7. Google Maps validation.
8. Constraint compliance.
9. Championship scoring.
10. Export roadbook dan map files.
11. Live tracking.
12. Test berbasis kasus nyata.
