# Place Resolver

Resolver mengubah token waypoint menjadi koordinat.

## Resolution Order

1. Local verified POI.
2. KMPAL database.
3. Curated aliases.
4. Nominatim local.
5. Google Places online.
6. Missing waypoint probability.
7. Manual confirmation.

## Output Status

```text
verified_local
verified_kmpal
verified_osm
verified_google_online
inferred_high_confidence
inferred_low_confidence
unresolved
```

