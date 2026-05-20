# ML Data

Folder ini menyimpan data untuk training, evaluasi, dan feedback ML.

Jangan simpan model besar atau dataset berlisensi tidak jelas tanpa keputusan governance.

## Layout

```text
labels/          Navigator feedback labels.
features/        Generated feature tables.
evaluations/     Model reports and metric snapshots.
model_registry/  Small metadata files for model versioning.
```

## Minimum Feedback Record

```text
event_id
trayek_id
sub_trayek_id
query_text
candidate_id
candidate_name
candidate_source
rank_position
accepted
label
correction_note
confirmed_by
confirmed_at
```

## Evaluation Metrics

- Precision@1
- Recall@5
- NDCG@3
- route distance deviation
- timing feasibility error
- navigator correction time

## Governance

Google-derived source stays restricted-use. Store `place_id` and reference metadata according to data governance, but do not promote restricted content into curated offline POI without verification.
