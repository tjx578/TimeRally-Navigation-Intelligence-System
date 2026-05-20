# Routing Gateway

Provider-neutral gateway untuk semua engine routing.

## Providers

```text
providers/valhalla_provider.py
providers/osrm_provider.py
providers/graphhopper_provider.py
providers/google_provider.py
```

## Required Methods

Setiap provider harus mendukung interface:

```text
route(origin, destination, waypoints, profile)
matrix(origins, destinations, profile)
nearest(point, profile)
match(gps_trace, profile)
```

## Rally Rule

Provider tidak boleh mengubah urutan waypoint kecuali request eksplisit `allow_reorder=true`. Default selalu `allow_reorder=false`.

