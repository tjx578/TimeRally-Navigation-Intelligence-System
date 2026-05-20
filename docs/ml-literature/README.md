# ML Literature For Time Rally Navigator

Folder ini berisi ringkasan literatur yang dipakai untuk desain ML Time Rally Navigator.

Jangan commit PDF/buku berhak cipta ke repo. Yang boleh disimpan:

- judul,
- penulis,
- DOI/link resmi,
- ringkasan dengan kata-kata sendiri,
- konsep yang diambil,
- modul repo yang ditopang,
- catatan implementasi.

## Priority Matrix

| Priority | Literature Area | Repo Feature |
|---|---|---|
| P0 | Information retrieval / BM25 / fuzzy search | waypoint candidate retrieval |
| P0 | GIS/geospatial data | POI database, spatial index, road context |
| P0 | OCR/NLP basics | OCR cleanup, alias expansion, entity extraction |
| P0 | MLOps ringan | feedback log, model report, dataset versioning |
| P1 | HMM map matching | missing waypoint sequence resolver |
| P1 | Travel-time constraints | route realism and timing feasibility |
| P1 | Learning-to-rank | candidate ranking after labeled data exists |
| P2 | Probabilistic graphical models | confidence calibration and advanced inference |
| P2 | Network optimization | advanced route optimizer |

## Selected Literature

| Title | Author(s) | Use In Repo |
|---|---|---|
| Geographic Information Science and Systems | Longley, Goodchild, Maguire, Rhind | GIS data model, POI layers, spatial query |
| GIS: A Computing Perspective | Worboys, Duckham | spatial indexing, network topology |
| Hidden Markov Map Matching Through Noise and Sparseness | Newson, Krumm | missing waypoint and GPS/noisy sequence resolution |
| Map Matching with Travel Time Constraints | Krumm, Horvitz, Letchner | route timing feasibility |
| Learning to Rank for Information Retrieval | Tie-Yan Liu | supervised waypoint ranker |
| Introduction to Information Retrieval | Manning, Raghavan, Schutze | BM25, inverted index, recall/precision |
| Probabilistic Graphical Models | Koller, Friedman | confidence and Markov reasoning |
| Speech and Language Processing | Jurafsky, Martin | OCR correction, NER, normalization |
| Designing Machine Learning Systems | Chip Huyen | production feedback loop and evaluation |
| Machine Learning Design Patterns | Lakshmanan, Robinson, Munn | feature consistency and model versioning |

## Implementation Rule

Any ML literature must map to at least one runnable or planned system component:

```text
literature -> concept -> feature -> data contract -> evaluation metric
```

If a concept cannot be mapped to a feature, keep it as background reading, not a repo requirement.
