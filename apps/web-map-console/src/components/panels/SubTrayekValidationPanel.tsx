import { CheckCircle2, Clock3, Gauge, Route, TriangleAlert } from "lucide-react";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";
import type { TimingValidationStatus } from "../../types/rally";

function formatKm(value: number | null, inferred?: number) {
  if (value !== null) {
    return value.toFixed(2);
  }
  return inferred === undefined ? "-" : `~${inferred.toFixed(2)}`;
}

function formatSpeed(value: number | null) {
  return value === null ? "-" : `${value.toFixed(2)} km/jam`;
}

function statusLabel(status: TimingValidationStatus) {
  if (status === "valid") return "valid";
  if (status === "warning") return "review";
  if (status === "error") return "konflik";
  return "belum cek";
}

export function SubTrayekValidationPanel() {
  const timing = useRallyWorkspaceStore((state) => state.timingValidation);

  if (!timing) {
    return (
      <div className="panel-section">
        <h2 className="panel-heading">Validasi Sub-Trayek</h2>
        <p className="metric-label">Belum ada tabel waktu, jarak, dan kecepatan dari OCR soal.</p>
      </div>
    );
  }

  return (
    <div className="panel-section">
      <div className="panel-title-row">
        <h2 className="panel-heading">Validasi Sub-Trayek</h2>
        <span className={`status-pill timing-${timing.status}`}>{statusLabel(timing.status)}</span>
      </div>

      <div className="metric-grid">
        <div className="metric">
          <div className="metric-label">
            <Route size={12} /> Jarak OCR
          </div>
          <div className="metric-value">{timing.calculatedDistanceKm.toFixed(2)} km</div>
        </div>
        <div className="metric">
          <div className="metric-label">
            <Clock3 size={12} /> Waktu OCR
          </div>
          <div className="metric-value">{timing.calculatedDurationMinutes} menit</div>
        </div>
        <div className="metric">
          <div className="metric-label">Target Jarak</div>
          <div className="metric-value">{timing.declaredDistanceKm.toFixed(2)} km</div>
        </div>
        <div className="metric">
          <div className="metric-label">Target Waktu</div>
          <div className="metric-value">{timing.declaredDurationMinutes} menit</div>
        </div>
      </div>

      <div className="timing-summary">
        <span>
          <Gauge size={13} /> Delta jarak {timing.distanceDeltaKm.toFixed(2)} km
        </span>
        <span>Delta waktu {timing.durationDeltaMinutes} menit</span>
      </div>

      <div className="timing-table-wrap">
        <table className="table timing-table">
          <thead>
            <tr>
              <th>Sub</th>
              <th>Start</th>
              <th>Finish</th>
              <th>Jarak</th>
              <th>Waktu</th>
              <th>Kecepatan</th>
              <th>Mode</th>
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
                <td>{row.scheduledStartTime}</td>
                <td>{row.scheduledFinishTime}</td>
                <td>{formatKm(row.declaredDistanceKm, row.inferredDistanceKm)}</td>
                <td>{row.declaredDurationMinutes} mnt</td>
                <td>{formatSpeed(row.calculatedSpeedKmh)}</td>
                <td>{row.classificationLabel}</td>
                <td>
                  <span className={`status-pill timing-${row.status}`}>{statusLabel(row.status)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {timing.warnings.length > 0 ? (
        <ul className="reason-list">
          {timing.warnings.map((warning) => (
            <li key={warning}>
              <TriangleAlert size={12} /> {warning}
            </li>
          ))}
        </ul>
      ) : (
        <p className="metric-label">
          <CheckCircle2 size={13} /> Total sub yang dihitung sudah sesuai dengan total soal.
        </p>
      )}
    </div>
  );
}
