# Championship Day Runbook

## Before Race

1. Load latest soal/OCR.
2. Parse event and sub-trayek.
3. Resolve all waypoints local-first.
4. Run missing waypoint probability for unresolved points.
5. Validate route with offline provider.
6. Validate with Google online if available.
7. Generate roadbook and export files.
8. Freeze final route package.

## Go/No-Go Criteria

Go if:
- no unresolved critical waypoint,
- distance deviation within tolerance,
- time table generated,
- chaining valid,
- all inferred candidates reviewed or accepted,
- offline package opens correctly.

No-Go if:
- placeholder coordinate remains,
- broken chaining,
- missing start/finish,
- route contradicts sub-trayek distance,
- confidence below threshold on critical waypoint.

## During Race

1. Follow roadbook ETA.
2. Watch deviation alerts.
3. Record GPS trace.
4. Mark actual checkpoint time.
5. Do not recalculate route without preserving original soal order.

## After Race

1. Replay GPS track.
2. Compare planned vs actual.
3. Update POI/KMPAL verification.
4. Add case to golden tests.

