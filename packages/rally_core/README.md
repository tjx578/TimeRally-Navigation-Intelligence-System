# Rally Core

Core logic yang membuat sistem ini berbeda dari aplikasi peta biasa.

## Modules

```text
parser/       Soal rally -> structured event.
reasoning/    Context recognition dan ambiguity reasoning.
constraints/  Absolute binding dan violation handling.
probability/  Missing waypoint resolver.
routing/      Provider-neutral route domain models.
scoring/      Championship score.
exporters/    YAML, GPX, KML, GeoJSON, roadbook.
```

## Invariant

Logika rally harus bisa dites tanpa UI, tanpa Google, dan tanpa routing engine eksternal. Provider eksternal hanya memperkaya dan memvalidasi.

