# ML Literature Assessment and System Plan

## Objective Assessment

Riset literatur yang diberikan sudah tepat secara domain karena tidak berhenti di "machine learning umum". Isinya menyentuh area yang benar-benar relevan untuk Time Rally Navigator:

- GIS dan road network untuk memahami ruang, POI, jalan, dan relasi lokasi.
- Information retrieval untuk mencari kandidat lokasi dari hasil OCR.
- Learning-to-rank untuk memberi urutan probabilitas kandidat waypoint.
- HMM/map matching untuk waypoint hilang, GPS noisy, dan pemilihan sequence jalan.
- OCR/NLP untuk koreksi teks soal.
- MLOps ringan untuk feedback navigator, evaluasi, dan versi model.

Namun untuk kebutuhan produksi nyata, daftar itu terlalu luas jika semuanya diperlakukan sebagai prioritas awal. Sistem time rally tidak boleh menjadi eksperimen ML yang berat. Akurasi lapangan justru paling aman jika dibuat bertahap:

```text
deterministic validation
+ rule-based scoring
+ probabilistic sequence reasoning
+ navigator feedback
+ supervised ranker setelah data cukup
```

Prinsip utama: **ML membantu memilih kandidat, tetapi tidak boleh diam-diam mengubah urutan waypoint, jarak resmi, waktu resmi, atau roadbook final tanpa validasi navigator.**

## What To Keep, Delay, Or Simplify

| Area Literatur | Penilaian | Keputusan |
|---|---|---|
| GIS / geospatial systems | Sangat relevan | Wajib untuk desain database POI, spatial index, road graph. |
| Information retrieval / BM25 | Sangat relevan | Wajib untuk MVP karena kandidat harus dicari cepat dari OCR. |
| OCR / NLP | Sangat relevan | Wajib untuk normalisasi singkatan, alias, dan koreksi OCR. |
| Learning-to-rank | Relevan, tapi butuh label | Mulai dari rule ranker; supervised ranker setelah feedback cukup. |
| HMM map matching | Sangat relevan untuk missing waypoint | Pakai versi sederhana dulu: sequence scoring / Viterbi-like dynamic programming. |
| Travel-time constraints | Sangat relevan | Masuk sebagai hard/soft constraint pada route candidate. |
| Probabilistic graphical models | Teoretis kuat tapi berat | Ambil konsep confidence dan Markov sequence, bukan framework kompleks. |
| General AI / AIMA | Berguna sebagai fondasi | Bukan prioritas implementasi. |
| Network flows | Berguna untuk route optimization lanjut | Tunda; pakai OSRM/Valhalla + constraint scoring dulu. |
| MLOps | Wajib secara ringan | Cukup dataset versioning, feedback log, model report, rollback. |

## MVP ML Scope

MVP yang paling kuat dan tetap sederhana:

1. **Candidate Retrieval**
   - Input: token OCR seperti `BR Anyar`, `SDN 1 Pergung`, `Kantor Desa`.
   - Output: top-20 kandidat lokasi dari historical waypoint DB, Jembrana staging POI, curated POI, dan OSM.
   - Metode: normalized alias, fuzzy match, token overlap, category filter, spatial bias.

2. **Explainable Candidate Scoring**
   - Input: kandidat POI + konteks sub-trayek.
   - Output: confidence score yang bisa dijelaskan.
   - Metode awal: weighted rule scorer, bukan black-box model.

3. **Sequence / Missing Waypoint Resolver**
   - Input: kandidat waypoint sebelum, kandidat waypoint hilang, kandidat waypoint berikutnya.
   - Output: sequence paling mungkin.
   - Metode awal: Viterbi-like scoring dengan text score, category score, route distance, timing feasibility, historical score.

4. **Timing and Distance Guard**
   - ML tidak memutuskan waktu resmi.
   - Sistem selalu menghitung jarak sub, waktu sub, speed, km/detik, dan deviasi route distance terhadap soal.
   - Kandidat diberi penalty jika membuat jarak/waktu tidak realistis.

5. **Navigator Feedback Loop**
   - Setiap pilihan navigator menjadi data training: accepted candidate, rejected candidate, reason, event/trayek/sub, final route distance, dan manual correction.

## Recommended Scoring Model

Untuk MVP:

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

Confidence class:

| Score | Meaning | UI behavior |
|---:|---|---|
| `>= 0.85` | Strong candidate | Tampilkan sebagai rekomendasi utama, tetap perlu confirm. |
| `0.65 - 0.84` | Plausible candidate | Tampilkan top-k options. |
| `0.45 - 0.64` | Weak candidate | Perlu review navigator. |
| `< 0.45` | Unsafe | Jangan auto-route; minta validasi manual. |

## When To Start Real ML Training

Jangan train model supervised terlalu dini.

| Data label tersedia | Model yang dipakai |
|---:|---|
| `< 300` keputusan kandidat | Rule-based scoring + manual feedback. |
| `300 - 1.000` keputusan kandidat | Logistic regression / random forest untuk confidence calibration. |
| `1.000 - 3.000` keputusan kandidat | Pairwise ranker sederhana, misalnya XGBoost ranker. |
| `> 3.000` keputusan lintas event | LambdaMART / LightGBM lambdarank + event-based validation. |

Split evaluasi jangan random row. Pakai:

```text
train = event lama
validation = event berbeda / trayek berbeda
test = soal lapangan terbaru
```

Ini mencegah model hanya menghafal lokasi yang pernah muncul.

## Metrics That Matter

Untuk Time Rally, metric ML harus dikaitkan ke operasi navigator:

| Metric | Target MVP | Meaning |
|---|---:|---|
| Precision@1 | `>= 0.75` untuk POI yang ada di DB | Kandidat pertama sering benar. |
| Recall@5 | `>= 0.95` | Kandidat benar muncul di top 5. |
| NDCG@3 | `>= 0.85` setelah label cukup | Urutan top 3 masuk akal. |
| Route distance deviation | `< 3%` terhadap jarak soal setelah validasi | Rute tidak terlalu melenceng. |
| Timing consistency | `0` error formula resmi | Hitungan waktu/jarak/speed harus deterministic. |
| Navigator correction time | turun dari manual baseline | Sistem benar-benar membantu kerja navigator. |

## Best Repo Design

Tambahkan ML sebagai lapisan pembantu di atas pipeline yang sudah ada.

```text
packages/
  rally_core/
    ml/
      README.md
      candidate_retrieval/
      features/
      rankers/
      sequence/
      evaluation/
      feedback/

data/
  ml/
    README.md
    labels/
    features/
    evaluations/
    model_registry/
```

API lanjut:

```text
POST /v1/ml/waypoint-candidates/rank
POST /v1/ml/missing-waypoint/resolve
POST /v1/ml/feedback
GET  /v1/ml/model-report/{model_id}
```

Untuk sekarang, endpoint ini boleh tetap menjadi internal plan sampai route resolver dasar hidup.

## Feature Schema

Fitur kandidat waypoint minimum:

```text
query_text
normalized_query
candidate_name
candidate_aliases
candidate_category
candidate_source
candidate_verification_status
text_similarity
alias_similarity
category_match
distance_from_previous_m
distance_to_next_m
route_distance_prev_to_candidate_m
route_distance_candidate_to_next_m
target_sub_distance_m
target_sub_time_sec
timing_feasibility_score
historical_occurrence_count
same_event_region_score
ocr_confidence
source_confidence
label
```

Label:

```text
0 = wrong
1 = possible
2 = correct
3 = verified/high confidence
```

## Literature Priority For The Repo

### Level 1: wajib untuk MVP

1. Introduction to Information Retrieval
2. Hidden Markov Map Matching Through Noise and Sparseness
3. Geographic Information Science and Systems
4. Speech and Language Processing
5. Designing Machine Learning Systems

### Level 2: setelah feedback data cukup

6. Learning to Rank for Information Retrieval
7. Map Matching with Travel Time Constraints
8. Probabilistic Graphical Models
9. Machine Learning Design Patterns
10. The Elements of Statistical Learning

### Level 3: advanced / research

11. Network Flows
12. Algorithm Design
13. LambdaMART paper
14. GIS: A Computing Perspective
15. Modern Information Retrieval

## Final Recommendation

Solusi terbaik untuk Time Rally Navigator adalah **hybrid intelligence system**, bukan pure ML.

```text
OCR + rules + GIS + search ranking + route constraints + navigator feedback
```

ML masuk pada tiga tempat yang paling berdampak:

1. ranking kandidat lokasi,
2. prediksi waypoint hilang,
3. koreksi OCR/alias berdasarkan feedback.

Jarak, waktu, speed, tap detik, dan pergantian sub-trayek tetap harus dihitung deterministik karena itu inti lomba dan tidak boleh probabilistik.
