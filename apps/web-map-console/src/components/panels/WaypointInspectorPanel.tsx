import { MapPin } from "lucide-react";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

export function WaypointInspectorPanel() {
  const waypoints = useRallyWorkspaceStore((state) => state.waypoints);

  return (
    <div className="panel-section">
      <h2 className="panel-heading">Waypoint Review</h2>
      {waypoints.length === 0 ? (
        <p className="metric-label">Belum ada waypoint. Jalankan parse soal terlebih dahulu.</p>
      ) : (
        waypoints.map((waypoint) => (
          <div className="metric" key={waypoint.id}>
            <div className="metric-label">
              <MapPin size={12} /> {waypoint.id}
            </div>
            <div className="metric-value">{waypoint.label}</div>
            <span className="status-pill">{waypoint.status}</span>
          </div>
        ))
      )}
    </div>
  );
}

