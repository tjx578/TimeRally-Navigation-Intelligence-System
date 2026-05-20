import { CircleDot, Magnet, PencilRuler } from "lucide-react";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

export function RouteEditorPanel() {
  const editor = useRallyWorkspaceStore((state) => state.routeEditor);

  return (
    <div className="panel-section">
      <h2 className="panel-heading">Route Editor</h2>
      <div className="metric-grid">
        <div className="metric">
          <div className="metric-label">Mode</div>
          <div className="metric-value">
            <PencilRuler size={14} /> {editor.mode}
          </div>
        </div>
        <div className="metric">
          <div className="metric-label">Snap</div>
          <div className="metric-value">
            <Magnet size={14} /> {editor.snapToRoad ? "on" : "manual"}
          </div>
        </div>
      </div>
      <p className="metric-label">
        <CircleDot size={13} /> Edit hanya segmen aktif. Setelah repair, validasi jarak/waktu
        dijalankan ulang untuk sub-trayek tersebut.
      </p>
    </div>
  );
}

