import { AlertTriangle, Trophy } from "lucide-react";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

export function ValidationPanel() {
  const validation = useRallyWorkspaceStore((state) => state.validation);

  return (
    <div className="panel-section">
      <h2 className="panel-heading">Validasi Championship</h2>
      <div className="metric-grid">
        <div className="metric">
          <div className="metric-label">Distance</div>
          <div className="metric-value">{validation?.distanceStatus ?? "pending"}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Time</div>
          <div className="metric-value">{validation?.timeStatus ?? "pending"}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Chaining</div>
          <div className="metric-value">{validation?.chainingStatus ?? "pending"}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Score</div>
          <div className="metric-value">
            <Trophy size={14} /> {validation?.score ?? 0}
          </div>
        </div>
      </div>
      <p className="metric-label">
        <AlertTriangle size={13} /> Inferred waypoint must be reviewed before final export.
      </p>
    </div>
  );
}

