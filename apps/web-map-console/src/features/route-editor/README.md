# Route Editor Feature

Route editor membawa pola kerja Footpath ke Time Rally dengan aturan rally-specific.

## Tools

- Inspect
- Draw
- Erase
- Repair
- Split
- Lock
- Snap-to-road toggle
- Undo segment

## Data Flow

```text
user edit
  -> route-edit operation
  -> routing gateway
  -> constraint validation
  -> roadbook update
  -> candidate review log
```

## Rally Safety

Editing route must never reorder waypoints by default. Any route edit only affects the selected leg/sub-trayek.

