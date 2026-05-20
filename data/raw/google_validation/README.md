# Google Validation Staging

Folder ini untuk data kandidat POI yang berasal dari Google validation workflow.

Data di sini bersifat staging, bukan master offline POI. Gunakan untuk:
- validasi online,
- kandidat waypoint resolver,
- manual review navigator,
- field verification queue.

Jangan gunakan data di folder ini untuk:
- offline map permanen,
- routing graph,
- tile cache,
- curated master POI tanpa verifikasi ulang.

Setiap file staging harus punya label sumber dan status:

```text
source=google_validation_import
source_license=restricted_google_derived
verification_status=needs_field_verification
```
