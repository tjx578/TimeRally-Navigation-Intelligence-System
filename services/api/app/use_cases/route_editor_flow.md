# Route Editor Use Case Flow

## Apply Probability Candidate

```text
1. User clicks "Pakai" on candidate.
2. UI sends route-edit operation with operation=repair.
3. API records affected leg.
4. Routing gateway recalculates geometry.
5. Constraint engine revalidates distance/time.
6. Roadbook is regenerated for affected sub-trayek.
7. Candidate review log is updated.
```

## Manual Draw Repair

```text
1. User selects Draw.
2. User traces replacement segment.
3. If snap is on, geometry is snapped to road.
4. If snap is off, geometry is stored as manual trace.
5. Validation decides whether route is competition-ready.
```

## Erase Segment

```text
1. User selects Erase.
2. User marks wrong route portion.
3. System reconnects endpoints.
4. New route is treated as draft until validated.
```

