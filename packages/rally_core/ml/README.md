# Rally Core ML

ML di Time Rally Navigator adalah lapisan pendukung, bukan pengganti rule dan validasi deterministic.

## Responsibilities

- Generate candidate waypoint list from OCR tokens.
- Score and rank candidates with explainable features.
- Resolve missing waypoint sequence with route/timing constraints.
- Log navigator feedback for future training.
- Evaluate candidate ranking quality.

## MVP Components

```text
candidate_retrieval/   BM25/fuzzy/alias candidate generator.
features/              Feature extraction for candidate scoring.
rankers/               Rule ranker first, supervised ranker later.
sequence/              Viterbi-like missing waypoint resolver.
evaluation/            Precision@1, Recall@5, NDCG@3, route deviation.
feedback/              Navigator correction logs.
```

## Non-Goals

- ML must not override official timing.
- ML must not reorder waypoints automatically.
- ML must not promote Google-derived POI into curated offline data.
- ML must not hide uncertainty from the navigator.

## First Model

Start with an explainable rule ranker:

```text
score =
0.30 * text_similarity
+ 0.15 * alias_match
+ 0.15 * category_match
+ 0.15 * route_continuity
+ 0.10 * timing_feasibility
+ 0.10 * historical_frequency
+ 0.05 * source_confidence
```

Train supervised ranker only after enough navigator-labeled decisions exist.
