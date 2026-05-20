# Data Layout

Data dipisahkan menjadi raw dan curated.

## raw

Data asli yang belum dinormalisasi. Jangan ditimpa.

### raw/rally_documents

Hasil OCR dan metadata soal rally historis.

### raw/historical_waypoints

Waypoint yang muncul dari soal lama. Dipakai sebagai memory resolver, tetapi belum menjadi curated POI sampai diverifikasi.

## curated/places

Master POI database yang dipakai resolver.

## curated/kmpal

KMPAL verified points.

## curated/rally_rules

SOP, singkatan, formula, scoring.

## mapdata

OSM extract, PMTiles, MBTiles, Valhalla tiles, OSRM graph.

## fixtures

Kasus uji rally yang punya expected output.
