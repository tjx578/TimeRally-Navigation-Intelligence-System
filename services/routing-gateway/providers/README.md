# Routing Providers

Provider implementations live here.

## Provider Contract

```python
class RoutingProvider:
    def route(self, request): ...
    def matrix(self, request): ...
    def nearest(self, request): ...
    def match(self, request): ...
```

## Provider Responsibilities

- Preserve waypoint order.
- Return distance in meters.
- Return duration in seconds.
- Return route geometry.
- Return provider metadata.
- Return errors in standard format.

## Providers

```text
valhalla_provider.py
osrm_provider.py
graphhopper_provider.py
google_provider.py
manual_provider.py
```

