# Routing Gateway Contracts

## Route Request

```yaml
provider: valhalla
profile: rally_car
allow_reorder: false
waypoints:
  - id: WP001
    name: Zero Point
    coordinate: { lat: -8.65, lng: 115.216667 }
```

## Route Response

```yaml
provider: valhalla
status: ok
legs:
  - from_waypoint: WP001
    to_waypoint: WP002
    distance_m: 1430
    duration_s: 210
    geometry: polyline_or_geojson
    warnings: []
```

## Provider Error

```yaml
provider: osrm
status: error
code: route_not_found
message: No route between waypoint pair
```

