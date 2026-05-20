import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

function formatDistance(value: number | null, inferred?: number) {
  if (value !== null) return value.toFixed(2);
  return inferred === undefined ? "-" : `~${inferred.toFixed(2)}`;
}

function formatSpeed(value: number | null) {
  return value === null ? "-" : value.toFixed(2);
}

function formatTap(value: number | null) {
  return value === null ? "-" : value.toFixed(6);
}

export function TimingValidationTable() {
  const timing = useRallyWorkspaceStore((state) => state.timingValidation);

  if (!timing) {
    return null;
  }

  return (
    <section className="timing-table-region">
      <div className="roadbook-heading">
        <strong>Tabel Validasi Timing</strong>
        <span>
          Target {timing.declaredDistanceKm.toFixed(2)} km / {timing.declaredDurationMinutes} menit
        </span>
      </div>
      <table className="table timing-full-table">
        <thead>
          <tr>
            <th>Sub</th>
            <th>Klasifikasi</th>
            <th>Start</th>
            <th>Finish</th>
            <th>Jarak</th>
            <th>Waktu</th>
            <th>Speed</th>
            <th>Tap km/detik</th>
            <th>Kumulatif</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {timing.rows.map((row) => (
            <tr key={row.id}>
              <td>
                <strong>{row.sub}</strong>
                <div className="table-subtext">{row.title}</div>
              </td>
              <td>{row.classificationLabel}</td>
              <td>{row.scheduledStartTime}</td>
              <td>{row.scheduledFinishTime}</td>
              <td>{formatDistance(row.declaredDistanceKm, row.inferredDistanceKm)} km</td>
              <td>{row.declaredDurationMinutes} menit</td>
              <td>{formatSpeed(row.calculatedSpeedKmh)} km/jam</td>
              <td>{formatTap(row.kmPerSecond)}</td>
              <td>{row.cumulativeFinishMinutes} menit</td>
              <td>
                <span className={`status-pill timing-${row.status}`}>{row.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
